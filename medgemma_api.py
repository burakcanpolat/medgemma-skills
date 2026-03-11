"""
MedGemma API Client
Modal üzerinde deploy edilmiş MedGemma modeline görüntü gönderir.
ZIP dosyalarını otomatik çıkartır.
"""

import base64
import json
import sys
import zipfile
import tempfile
import urllib.request
import ssl
from pathlib import Path

ENDPOINT = "https://burakcanpolat--medgemma-vllm-serve.modal.run/v1/chat/completions"
MODEL = "google/medgemma-1.5-4b-it"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}


def extract_zip(zip_path: str, output_dir: str = "images") -> list[str]:
    """ZIP dosyasını çıkartır, görüntü dosyalarının yollarını döndürür."""
    out = Path(output_dir)
    out.mkdir(exist_ok=True)
    extracted = []

    with zipfile.ZipFile(zip_path, "r") as zf:
        for name in zf.namelist():
            if Path(name).suffix.lower() in IMAGE_EXTENSIONS and not name.startswith("__MACOSX"):
                zf.extract(name, out)
                extracted.append(str(out / name))

    extracted.sort()
    print(f"ZIP'ten {len(extracted)} görüntü çıkartıldı: {output_dir}/")
    return extracted


def analyze_image(image_path: str, prompt: str = "Analyze this medical image. Provide detailed findings.") -> str:
    """Tek bir görüntüyü MedGemma ile analiz eder."""
    path = Path(image_path)
    if not path.exists():
        return f"HATA: Dosya bulunamadı: {image_path}"

    mime = "image/jpeg" if path.suffix.lower() in (".jpg", ".jpeg") else "image/png"
    b64 = base64.b64encode(path.read_bytes()).decode()

    payload = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}
        ]}],
        "max_tokens": 1024,
        "temperature": 0
    }).encode()

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(ENDPOINT, data=payload, headers={"Content-Type": "application/json"}, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=300, context=ctx) as resp:
            result = json.loads(resp.read().decode())
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"HATA: MedGemma API hatası: {e}"


def analyze_multiple(image_paths: list[str], prompt: str = "Compare these medical images. Analyze progression.") -> str:
    """Birden fazla görüntüyü tek istekte MedGemma'ya gönderir."""
    content = [{"type": "text", "text": prompt}]

    for p in image_paths:
        path = Path(p)
        if not path.exists():
            return f"HATA: Dosya bulunamadı: {p}"
        mime = "image/jpeg" if path.suffix.lower() in (".jpg", ".jpeg") else "image/png"
        b64 = base64.b64encode(path.read_bytes()).decode()
        content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}})

    payload = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": content}],
        "max_tokens": 1024,
        "temperature": 0
    }).encode()

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(ENDPOINT, data=payload, headers={"Content-Type": "application/json"}, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=300, context=ctx) as resp:
            result = json.loads(resp.read().decode())
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"HATA: MedGemma API hatası: {e}"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım:")
        print("  python medgemma_api.py görüntü.jpeg")
        print("  python medgemma_api.py görüntü1.jpg görüntü2.jpg görüntü3.jpg")
        print("  python medgemma_api.py görseller.zip")
        sys.exit(1)

    input_path = sys.argv[1]

    # ZIP dosyası kontrolü
    if input_path.lower().endswith(".zip"):
        images = extract_zip(input_path)
        if not images:
            print("HATA: ZIP içinde görüntü dosyası bulunamadı.")
            sys.exit(1)
        if len(images) == 1:
            print(analyze_image(images[0]))
        else:
            print(analyze_multiple(images))
    else:
        paths = sys.argv[1:]
        if len(paths) == 1:
            print(analyze_image(paths[0]))
        else:
            print(analyze_multiple(paths))
