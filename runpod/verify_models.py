"""Verify cached model files by SHA-256 (HF stores blobs named by content hash).

Usage:
    python runpod/verify_models.py black-forest-labs/FLUX.1-dev Qwen/Qwen2.5-14B-Instruct
"""
import glob
import hashlib
import os
import sys

HF_HUB = os.environ.get("HF_HOME", "/workspace/hf_cache") + "/hub"


def sha256(path, buf=8 * 1024 * 1024):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(buf), b""):
            h.update(b)
    return h.hexdigest()


def main():
    repos = sys.argv[1:] or ["black-forest-labs/FLUX.1-dev", "Qwen/Qwen2.5-14B-Instruct"]
    all_ok = True
    for repo in repos:
        folder = "models--" + repo.replace("/", "--")
        base = os.path.join(HF_HUB, folder)
        snaps = sorted(glob.glob(base + "/snapshots/*/"))
        if not snaps:
            print("MISSING", repo); all_ok = False; continue
        snap = snaps[-1]
        for p in sorted(glob.glob(snap + "/**/*.safetensors", recursive=True)):
            real = os.path.realpath(p)
            ok = sha256(real) == os.path.basename(real)
            all_ok = all_ok and ok
            print(("OK " if ok else "BAD"), f"{os.path.getsize(real)/1e9:6.2f} GB",
                  repo, os.path.relpath(p, snap))
    print("\n=>", "ALL FILES VERIFIED INTACT" if all_ok else "INTEGRITY FAILURE")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
