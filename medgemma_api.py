"""
MedGemma API Client
Modal üzerinde deploy edilmiş MedGemma modeline görüntü gönderir.
"""

import base64
import json
import sys
import urllib.request
import ssl
from pathlib import Path

ENDPOINT = "https://burakcanpolat--medgemma-vllm-serve.modal.run/v1/chat/completions"
MODEL = "google/medgemma-1.5-4b-it"


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
        print("Kullanım: python medgemma_api.py <görüntü_yolu> [görüntü2] [görüntü3]")
        sys.exit(1)

    paths = sys.argv[1:]
    if len(paths) == 1:
        print(analyze_image(paths[0]))
    else:
        print(analyze_multiple(paths))
