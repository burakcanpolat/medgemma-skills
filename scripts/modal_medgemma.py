"""
Modal deployment script for MedGemma vLLM server.

Deploys google/medgemma-1.5-4b-it on Modal with:
- HuggingFace model cache volume (avoids re-downloading on cold start)
- Medical images volume (for file:// path-based image input)
- OpenAI-compatible API endpoint (/v1/chat/completions)

Usage:
    modal deploy scripts/modal_medgemma.py

Prerequisites:
    1. Modal account: https://modal.com/signup
    2. Modal CLI: uv tool install modal && modal setup
    3. HuggingFace token: modal secret create huggingface-token HF_TOKEN=hf_xxx
"""

import subprocess

import modal

# ---------------------------------------------------------------------------
# App & resources
# ---------------------------------------------------------------------------

app = modal.App("medgemma-vllm")

MODEL_NAME = "google/medgemma-1.5-4b-it"
GPU_TYPE = "A10G"  # 24GB VRAM — sufficient for 4B parameter model
VLLM_PORT = 8000

# Volumes
hf_cache_vol = modal.Volume.from_name("medgemma-hf-cache", create_if_missing=True)
med_images_vol = modal.Volume.from_name("med-images", create_if_missing=True)

# Container image with vLLM
vllm_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "vllm>=0.8.0",
        "huggingface_hub[hf_xet]",
    )
)


# ---------------------------------------------------------------------------
# vLLM server function
# ---------------------------------------------------------------------------

@app.function(
    image=vllm_image,
    gpu=GPU_TYPE,
    volumes={
        "/root/.cache/huggingface": hf_cache_vol,
        "/data/images": med_images_vol,
    },
    secrets=[modal.Secret.from_name("huggingface-token")],
    timeout=600,
    container_idle_timeout=300,
    allow_concurrent_inputs=10,
)
@modal.web_server(port=VLLM_PORT, startup_timeout=600)
def serve():
    import time
    cmd = [
        "python", "-m", "vllm.entrypoints.openai.api_server",
        "--model", MODEL_NAME,
        "--host", "0.0.0.0",
        "--port", str(VLLM_PORT),
        "--trust-remote-code",  # Required by MedGemma — only use with trusted model sources
        "--dtype", "bfloat16",
        "--max-model-len", "4096",
        "--limit-mm-per-prompt", "image=85",
        "--allowed-local-media-path", "/data/images",
    ]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    # Wait briefly and verify the process is still alive
    time.sleep(5)
    if process.poll() is not None:
        output = process.stdout.read().decode() if process.stdout else ""
        raise RuntimeError(f"vLLM failed to start (exit code {process.returncode}):\n{output[:2000]}")


if __name__ == "__main__":
    print("This script is meant to be deployed with Modal:")
    print("  modal deploy scripts/modal_medgemma.py")
    print()
    print("To check deployment status:")
    print("  modal app list")
