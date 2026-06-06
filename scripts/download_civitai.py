"""Download a LoRA from Civitai by its model-VERSION id.

Civitai requires an API key (unlike HuggingFace). Get one at
civitai.com -> Account Settings -> API Keys, then export it:
    export CIVITAI_TOKEN=xxxxxxxx

Find the version id on the model page (or via civitai.com/api/v1/models/<modelId>).
Usage:
    python scripts/download_civitai.py 977088 --out /workspace/models/cartoon_lora.safetensors
"""
import argparse
import os
import subprocess


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("version_id", help="Civitai model VERSION id (not the model id)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    token = os.environ.get("CIVITAI_TOKEN")
    if not token:
        raise SystemExit("set CIVITAI_TOKEN (civitai.com -> Account Settings -> API Keys)")

    url = f"https://civitai.com/api/download/models/{args.version_id}?token={token}"
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    # curl -L follows Civitai's redirect to the signed CDN url
    subprocess.run(["curl", "-L", "-o", args.out, url], check=True)
    size = os.path.getsize(args.out)
    if size < 1_000_000:  # a real LoRA is tens+ of MB; smaller = an error/HTML page
        raise SystemExit(f"download looks wrong ({size} bytes) - check token / version id")
    print(f"saved {args.out} ({size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
