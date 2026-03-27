"""
MedGemma API Client — Unified
Sends images to MedGemma model deployed on Modal.
Includes ZIP smart-routing, series detection, batch processing, and JSON report saving.

Image transfer strategy (volume-first):
  - volume (automatic): Uploads to Modal Volume, sends file:// paths. Used automatically
    for ZIP files and multiple images when Modal CLI is available.
  - base64 (fallback): Encodes images inline in JSON. Used for single images, or as
    fallback when Modal CLI is not installed or volume upload fails.

Cold start handling:
  Before the first analysis, the script checks if the server is ready. If the Modal
  container is cold-starting, progress feedback is shown until the server responds.

Modal config: --limit-mm-per-prompt image=85 (max 85 images per request)

Usage:
  python medgemma_api.py image.jpeg                          # single, base64
  python medgemma_api.py image1.jpg image2.jpg               # multiple, auto volume
  python medgemma_api.py archive.zip                         # ZIP, auto volume
  python medgemma_api.py --base64 archive.zip                # ZIP, force base64
  python medgemma_api.py --base64 img1.jpg img2.jpg          # multiple, force base64
"""

import base64
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
import urllib.request
import urllib.error
import ssl
import datetime
from pathlib import Path

# UTF-8 output for Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _load_env():
    """Load .env file from the project root (no external deps)."""
    # Walk up from script dir to find .env
    for parent in [Path(__file__).resolve().parent.parent, Path.cwd()]:
        env_file = parent / ".env"
        if env_file.exists():
            with open(env_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, _, value = line.partition("=")
                        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))
            break


_load_env()

ENDPOINT = os.environ.get("MEDGEMMA_ENDPOINT", "")
MODEL = os.environ.get("MEDGEMMA_MODEL", "google/medgemma-1.5-4b-it")
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}
_MIME_MAP = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".png": "image/png", ".bmp": "image/bmp",
    ".tiff": "image/tiff", ".tif": "image/tiff",
}

MAX_IMAGES_PER_REQUEST = 85  # Modal vLLM config: --limit-mm-per-prompt image=85
VOLUME_NAME = "med-images"
VOLUME_MOUNT = "/data/images"  # Must match modal_medgemma.py


# ---------------------------------------------------------------------------
# SSL context
# ---------------------------------------------------------------------------

def _ssl_ctx() -> ssl.SSLContext:
    if os.environ.get("MEDGEMMA_VERIFY_SSL", "true").lower() in ("0", "false", "no"):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    return ssl.create_default_context()


# ---------------------------------------------------------------------------
# Cold start detection and server readiness
# ---------------------------------------------------------------------------

_server_warm = False


def _ping_server(timeout: int = 15) -> bool:
    """Send a lightweight GET to /v1/models to check if the server is responding."""
    if not ENDPOINT:
        return False
    # Derive /v1/models URL from the chat completions endpoint
    if "/v1/" in ENDPOINT:
        url = ENDPOINT.split("/v1/")[0] + "/v1/models"
    else:
        url = ENDPOINT
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout, context=_ssl_ctx()) as resp:
            return resp.status == 200
    except Exception:
        return False


def _ensure_server_ready() -> bool:
    """Wait for the MedGemma server to be ready. Handles cold starts with progress feedback."""
    global _server_warm
    if _server_warm:
        return True

    print("[SERVER] Checking MedGemma server status...")
    if _ping_server(timeout=15):
        print("[SERVER] Server is ready.")
        _server_warm = True
        return True

    # Cold start detected
    print("[SERVER] Server is starting up (cold start)...")
    print("[SERVER] The AI model is loading into GPU memory. This typically takes 2-5 minutes.")

    max_wait = 600  # 10 minutes
    start = time.time()
    while time.time() - start < max_wait:
        time.sleep(15)
        elapsed = int(time.time() - start)
        mins, secs = divmod(elapsed, 60)
        print(f"[SERVER] Waiting... {mins}m {secs:02d}s elapsed")
        if _ping_server(timeout=15):
            elapsed = int(time.time() - start)
            mins, secs = divmod(elapsed, 60)
            print(f"[SERVER] Server is ready! (cold start took {mins}m {secs:02d}s)")
            _server_warm = True
            return True

    print("[SERVER] Server did not respond within 10 minutes.")
    print("[SERVER] Check your deployment: modal app list")
    return False


# ---------------------------------------------------------------------------
# Volume helpers (requires modal CLI)
# ---------------------------------------------------------------------------

def _modal_available() -> bool:
    """Check if modal CLI is installed."""
    return shutil.which("modal") is not None


def volume_upload(local_dir: str | Path, remote_dir: str) -> bool:
    """Upload a local directory to the med-images Modal Volume."""
    local_dir = Path(local_dir)
    if not local_dir.exists():
        print(f"ERROR: Directory not found: {local_dir}")
        return False

    print(f"[VOLUME] Uploading {local_dir} -> {VOLUME_NAME}:{remote_dir}")
    try:
        result = subprocess.run(
            ["modal", "volume", "put", VOLUME_NAME, local_dir.as_posix() + "/", remote_dir],
            capture_output=True, text=True, timeout=300,
        )
    except subprocess.TimeoutExpired:
        print("ERROR: Volume upload timed out (>5 min).")
        return False
    if result.returncode != 0:
        print(f"ERROR: Volume upload failed: {result.stderr}")
        return False

    print(f"[VOLUME] Upload complete.")
    return True


def volume_cleanup(remote_dir: str) -> None:
    """Remove uploaded images from the volume after analysis."""
    print(f"[VOLUME] Cleaning up {VOLUME_NAME}:{remote_dir}")
    try:
        result = subprocess.run(
            ["modal", "volume", "rm", "-r", VOLUME_NAME, remote_dir],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            print(f"WARNING: Volume cleanup failed: {result.stderr.strip()}")
    except subprocess.TimeoutExpired:
        print("WARNING: Volume cleanup timed out.")


# ---------------------------------------------------------------------------
# API call — sends payload to the endpoint
# ---------------------------------------------------------------------------

def _api_call(content: list[dict], max_tokens: int = 1024, timeout: int = 300) -> str:
    """Send a chat completion request to the MedGemma endpoint."""
    payload = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": content}],
        "max_tokens": max_tokens,
        "temperature": 0,
    }).encode()

    req = urllib.request.Request(
        ENDPOINT, data=payload,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_ssl_ctx()) as resp:
            result = json.loads(resp.read().decode())
            choices = result.get("choices")
            if not choices:
                return f"ERROR: Unexpected API response (no choices): {json.dumps(result)[:500]}"
            return choices[0]["message"]["content"]
    except urllib.error.URLError as e:
        return f"ERROR: MedGemma connection error: {e}"
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        return f"ERROR: MedGemma malformed response: {e}"
    except subprocess.TimeoutExpired:
        return "ERROR: MedGemma request timed out."
    except Exception as e:
        return f"ERROR: MedGemma API error: {e}"


# ---------------------------------------------------------------------------
# Image content builders — base64 vs file:// path
# ---------------------------------------------------------------------------

def _image_content_base64(image_path: Path) -> dict:
    """Build an image_url content block using base64 encoding."""
    mime = _MIME_MAP.get(image_path.suffix.lower(), "image/png")
    b64 = base64.b64encode(image_path.read_bytes()).decode()
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}


def _image_content_volume(volume_path: str) -> dict:
    """Build an image_url content block using a file:// path on the Modal Volume."""
    return {"type": "image_url", "image_url": {"url": f"file://{volume_path}"}}


# ---------------------------------------------------------------------------
# Analysis functions
# ---------------------------------------------------------------------------

def analyze_image(image_path: str | Path,
                  prompt: str = "Analyze this medical image. Provide detailed findings.",
                  volume_path: str | None = None) -> str:
    """Analyze a single image with MedGemma."""
    path = Path(image_path)
    if volume_path:
        img_block = _image_content_volume(volume_path)
    elif not path.exists():
        return f"ERROR: File not found: {image_path}"
    else:
        img_block = _image_content_base64(path)

    content = [{"type": "text", "text": prompt}, img_block]
    return _api_call(content, max_tokens=1024, timeout=300)


def analyze_multiple(image_paths: list[str | Path],
                     prompt: str = "Compare these medical images. Analyze progression.",
                     volume_paths: list[str] | None = None) -> str:
    """Send multiple images to MedGemma in a single request (max 85)."""
    content: list[dict] = [{"type": "text", "text": prompt}]

    total = len(image_paths)
    if total > MAX_IMAGES_PER_REQUEST:
        return f"ERROR: Too many images ({total}). Maximum is {MAX_IMAGES_PER_REQUEST} per request. Use analyze_series() for batching."

    if volume_paths:
        for vp in volume_paths:
            content.append(_image_content_volume(vp))
    else:
        for p in image_paths:
            path = Path(p)
            if not path.exists():
                return f"ERROR: File not found: {p}"
            content.append(_image_content_base64(path))

    return _api_call(content, max_tokens=2048, timeout=600)


# ---------------------------------------------------------------------------
# ZIP extraction
# ---------------------------------------------------------------------------

def extract_zip(zip_path: str | Path) -> tuple[list[Path], Path]:
    """Extract image files from a ZIP to images/temp/{zip_name}/."""
    zip_path = Path(zip_path)
    out = Path("images") / "temp" / zip_path.stem
    out.mkdir(parents=True, exist_ok=True)

    extracted: list[Path] = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        out_resolved = out.resolve()
        total_size = 0
        max_extract_size = 2 * 1024 * 1024 * 1024  # 2 GB limit
        for info in zf.infolist():
            name = info.filename
            if Path(name).suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            if name.startswith("__MACOSX"):
                continue
            # ZIP bomb protection
            total_size += info.file_size
            if total_size > max_extract_size:
                print("ERROR: ZIP extraction exceeds 2 GB limit. Possible zip bomb.")
                break
            # ZIP slip protection: validate and write manually
            target = (out / name).resolve()
            if not str(target).startswith(str(out_resolved) + os.sep):
                print(f"WARNING: Skipping suspicious path: {name}")
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(zf.read(name))
            extracted.append(target)

    extracted.sort()
    print(f"[ZIP] {len(extracted)} images extracted -> {out}")
    return extracted, out


# ---------------------------------------------------------------------------
# Series detection
# ---------------------------------------------------------------------------

def detect_series(image_paths: list[Path], extraction_root: Path) -> dict[str, list[Path]]:
    """
    Group images by series.
    - If subdirectories exist: each subdirectory = one series
    - If no subdirectories: all files = single series
    """
    subdirs: dict[str, list[Path]] = {}
    flat: list[Path] = []

    for p in image_paths:
        rel = p.relative_to(extraction_root)
        parts = rel.parts
        if len(parts) > 1:
            series_name = parts[0]
            subdirs.setdefault(series_name, []).append(p)
        else:
            flat.append(p)

    if subdirs:
        if flat:
            subdirs["_other"] = sorted(flat)
        return {k: sorted(v) for k, v in subdirs.items()}

    return {"all_images": sorted(image_paths)}


# ---------------------------------------------------------------------------
# Series analysis — each series is independent
# ---------------------------------------------------------------------------

def analyze_series(series_name: str, images: list[Path],
                   volume_remote_dir: str | None = None,
                   extraction_root: Path | None = None) -> dict:
    """
    Analyze a single series.
    - ≤85 images → send all in a single request
    - >85 images → split into batches of 85
    """
    total = len(images)
    mode_label = "volume" if volume_remote_dir else "base64"
    print(f"\n{'='*60}")
    print(f"  SERIES: {series_name} ({total} images, {mode_label})")
    print(f"{'='*60}")

    series_result = {
        "series_name": series_name,
        "total_images": total,
        "mode": mode_label,
        "batches": [],
    }

    def _volume_paths(batch_images: list[Path]) -> list[str] | None:
        if not volume_remote_dir or not extraction_root:
            return None
        paths = []
        for img in batch_images:
            rel = img.relative_to(extraction_root)
            paths.append(f"{VOLUME_MOUNT}/{volume_remote_dir}/{rel.as_posix()}")
        return paths

    if total <= MAX_IMAGES_PER_REQUEST:
        print(f"  -> Sending {total} images in a single request...")
        prompt = (
            f"These are {total} consecutive medical imaging slices from the same series. "
            "Analyze the complete series: describe the imaging modality, body region, "
            "and all notable findings across the entire series. "
            "Note any progression or changes between slices."
        )
        answer = analyze_multiple(images, prompt, volume_paths=_volume_paths(images))
        print(f"  -> Result: {answer[:200]}...")
        series_result["batches"].append({
            "batch": 1,
            "image_count": total,
            "images": [p.name for p in images],
            "analysis": answer,
        })
    else:
        batches = [images[i:i + MAX_IMAGES_PER_REQUEST]
                   for i in range(0, total, MAX_IMAGES_PER_REQUEST)]
        print(f"  -> {len(batches)} batches (groups of {MAX_IMAGES_PER_REQUEST})")

        for idx, batch in enumerate(batches, 1):
            print(f"\n  [BATCH {idx}/{len(batches)}] {len(batch)} images...")
            prompt = (
                f"These are medical imaging slices {(idx-1)*MAX_IMAGES_PER_REQUEST + 1}"
                f"-{(idx-1)*MAX_IMAGES_PER_REQUEST + len(batch)} "
                f"from a series of {total} total slices. "
                "Describe the imaging modality, body region, and key findings in this segment."
            )
            answer = analyze_multiple(batch, prompt, volume_paths=_volume_paths(batch))
            print(f"  -> Result: {answer[:160]}...")
            series_result["batches"].append({
                "batch": idx,
                "image_count": len(batch),
                "images": [p.name for p in batch],
                "analysis": answer,
            })

    return series_result


# ---------------------------------------------------------------------------
# Report saving
# ---------------------------------------------------------------------------

def save_report(data: dict, label: str = "report") -> Path:
    """Save results as timestamped JSON under reports/."""
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_label = "".join(c if c.isalnum() or c in "-_" else "_" for c in label)
    out = reports_dir / f"{safe_label}_{ts}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n[REPORT] Saved: {out}")
    return out


# ---------------------------------------------------------------------------
# Smart ZIP dispatcher
# ---------------------------------------------------------------------------

def process_zip(zip_path: str | Path, force_base64: bool = False) -> dict:
    """
    Extract ZIP, split into series, analyze each series independently.
    Automatically uses volume mode when Modal CLI is available (volume-first).
    Falls back to base64 if Modal is not installed or volume upload fails.
    Pass force_base64=True to skip volume and use base64 directly.
    """
    images, extraction_root = extract_zip(zip_path)
    total = len(images)

    if total == 0:
        print("ERROR: No image files found in ZIP.")
        return {}

    zip_label = Path(zip_path).stem
    session_id = f"{zip_label}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Volume-first: try volume automatically unless forced to base64
    volume_remote_dir = None
    if force_base64:
        print("[MODE] Base64 mode (forced via --base64).")
    elif _modal_available():
        remote_dir = f"sessions/{session_id}"
        print("[MODE] Attempting volume upload for optimal performance...")
        if volume_upload(extraction_root, remote_dir):
            volume_remote_dir = remote_dir
        else:
            print("[MODE] Volume upload failed. Falling back to base64.")
    else:
        print("[MODE] Modal CLI not found. Using base64 mode.")

    # Detect series
    series_map = detect_series(images, extraction_root)
    mode_label = "volume" if volume_remote_dir else "base64"
    print(f"\n[PLAN] {total} images, {len(series_map)} series ({mode_label} mode):")
    for name, imgs in series_map.items():
        batches_needed = (len(imgs) + MAX_IMAGES_PER_REQUEST - 1) // MAX_IMAGES_PER_REQUEST
        mode = "single request" if len(imgs) <= MAX_IMAGES_PER_REQUEST else f"{batches_needed} batches"
        print(f"  - {name}: {len(imgs)} images ({mode})")

    # Analyze each series independently
    results = {
        "zip_file": str(zip_path),
        "total_images": total,
        "total_series": len(series_map),
        "mode": mode_label,
        "series": {},
    }

    try:
        for series_name, series_images in series_map.items():
            series_result = analyze_series(
                series_name, series_images,
                volume_remote_dir=volume_remote_dir,
                extraction_root=extraction_root,
            )
            results["series"][series_name] = series_result

        save_report(results, label=zip_label)
    finally:
        # Always clean up, even if analysis fails
        if volume_remote_dir:
            volume_cleanup(volume_remote_dir)
        if extraction_root.exists():
            shutil.rmtree(extraction_root, ignore_errors=True)

    return results


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if not ENDPOINT:
        print("ERROR: MEDGEMMA_ENDPOINT is not set.")
        print("Please create a .env file with your Modal endpoint URL.")
        print("See .env.example for details.")
        sys.exit(1)

    # Parse flags
    args = sys.argv[1:]
    force_base64 = False
    if "--base64" in args:
        force_base64 = True
        args.remove("--base64")
    # --volume is kept for backward compatibility (now the default, silently ignored)
    if "--volume" in args:
        args.remove("--volume")

    if len(args) < 1:
        print("Usage:")
        print("  python medgemma_api.py image.jpeg                    # single image")
        print("  python medgemma_api.py image1.jpg image2.jpg         # multiple (auto volume)")
        print("  python medgemma_api.py archive.zip                   # ZIP (auto volume)")
        print("  python medgemma_api.py --base64 archive.zip          # ZIP, force base64")
        print("  python medgemma_api.py --base64 img1.jpg img2.jpg    # multiple, force base64")
        sys.exit(1)

    # Validate file extensions
    for arg in args:
        if not arg.lower().endswith(".zip"):
            ext = Path(arg).suffix.lower()
            if ext not in IMAGE_EXTENSIONS:
                print(f"ERROR: Unsupported file type: {ext or '(none)'}")
                print(f"Supported: {', '.join(sorted(IMAGE_EXTENSIONS))}")
                sys.exit(1)

    # Ensure server is ready (handles cold start with progress feedback)
    if not _ensure_server_ready():
        print("ERROR: MedGemma server is not available. Cannot proceed.")
        sys.exit(1)

    input_path = args[0]

    if input_path.lower().endswith(".zip"):
        process_zip(input_path, force_base64=force_base64)
    else:
        paths = args
        if len(paths) == 1:
            # Single image: always base64 (efficient enough)
            print(f"[SINGLE IMAGE] {paths[0]}")
            result = analyze_image(paths[0])
            print(result)
            save_report({"mode": "single", "image": paths[0], "analysis": result},
                        label=Path(paths[0]).stem)
        else:
            # Multiple images: volume-first with base64 fallback
            if not force_base64 and _modal_available():
                session_id = f"multi_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                remote_dir = f"sessions/{session_id}"
                tmp = Path("images") / "temp" / session_id
                tmp.mkdir(parents=True, exist_ok=True)
                seen_names: set[str] = set()
                final_names: list[str] = []
                for p in paths:
                    name = Path(p).name
                    if name in seen_names:
                        stem = Path(p).stem
                        suffix = Path(p).suffix
                        name = f"{stem}_{hash(p) % 10000}{suffix}"
                    seen_names.add(name)
                    final_names.append(name)
                    shutil.copy2(p, tmp / name)
                print(f"[MODE] Attempting volume upload for optimal performance...")
                if volume_upload(tmp, remote_dir):
                    vol_paths = [f"{VOLUME_MOUNT}/{remote_dir}/{n}" for n in final_names]
                    print(f"[MULTIPLE IMAGES] {len(paths)} files (volume mode)")
                    result = analyze_multiple(paths, volume_paths=vol_paths)
                    print(result)
                    save_report({"mode": "multiple_volume", "images": paths, "analysis": result},
                                label="multi_image")
                    volume_cleanup(remote_dir)
                else:
                    print("[MODE] Volume upload failed. Falling back to base64.")
                    print(f"[MULTIPLE IMAGES] {len(paths)} files (base64 fallback)")
                    result = analyze_multiple(paths)
                    print(result)
                    save_report({"mode": "multiple", "images": paths, "analysis": result},
                                label="multi_image")
                shutil.rmtree(tmp, ignore_errors=True)
            else:
                if force_base64:
                    print(f"[MODE] Base64 mode (forced via --base64).")
                else:
                    print(f"[MODE] Modal CLI not found. Using base64 mode.")
                print(f"[MULTIPLE IMAGES] {len(paths)} files")
                result = analyze_multiple(paths)
                print(result)
                save_report({"mode": "multiple", "images": paths, "analysis": result},
                            label="multi_image")
