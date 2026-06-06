"""Download any HuggingFace LoRA repo and copy its .safetensors into models/.

Usage:
    python scripts/download_lora.py <hf_repo_id> --out /workspace/models/<name>.safetensors

Example:
    python scripts/download_lora.py wanghaofan/Black-Myth-Wukong-FLUX-LoRA \
        --out /workspace/models/wukong_lora.safetensors
"""
import argparse
import glob
import os
import shutil

from huggingface_hub import snapshot_download


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo_id")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    d = snapshot_download(args.repo_id)
    cands = sorted(
        glob.glob(d + "/**/*.safetensors", recursive=True),
        key=os.path.getsize,
        reverse=True,
    )
    if not cands:
        raise SystemExit(f"no .safetensors found in {args.repo_id}")
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    shutil.copy(cands[0], args.out)
    print(f"LoRA: {cands[0]}\n  -> {args.out}")


if __name__ == "__main__":
    main()
