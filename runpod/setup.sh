#!/usr/bin/env bash
# scriptframes (FLUX.2) - one-shot setup for a fresh RunPod pod.
#
# IMPORTANT: pip packages live on the pod CONTAINER and are wiped on every restart;
# only the /workspace network volume persists. Re-run this after any restart.
# Models cache on the volume, so they download only once.
#
# Prereqs:
#   - Attach a network volume (>=120 GB) at /workspace
#   - Put this repo at /workspace/scriptframes
#   - Accept the FLUX.2-klein-9B license on HuggingFace, then:  export HF_TOKEN=hf_xxx
set -euo pipefail

export HF_HOME=/workspace/hf_cache
export HF_HUB_ENABLE_HF_TRANSFER=0     # reliability over speed
: "${HF_TOKEN:?set HF_TOKEN first:  export HF_TOKEN=hf_xxx}"

echo "=== [1/6] python packages (FLUX.2 needs diffusers-from-git + torch 2.7) ==="
pip install -q -e /workspace/scriptframes
# FLUX.2 klein uses a Qwen3 text encoder -> transformers needs torch>=2.7 (fp8 dtype)
pip install -q --upgrade "torch==2.7.1" "torchvision==0.22.1" "torchaudio==2.7.1" \
    --index-url https://download.pytorch.org/whl/cu126
pip install -q -U "git+https://github.com/huggingface/diffusers.git" \
    transformers accelerate safetensors sentencepiece protobuf pillow

echo "=== [2/6] NVIDIA PiD (upscaler) ==="
if [ ! -d /workspace/PiD ]; then
  git clone https://github.com/nv-tlabs/PiD.git /workspace/PiD
fi
pip install -q hydra-core omegaconf attrs einops loguru termcolor fvcore iopath \
    imageio opencv-python-headless pandas boto3 botocore wandb
pip install -q -e /workspace/PiD
# only the flux2 PiD checkpoints + shared VAE
python - <<'PY'
from huggingface_hub import snapshot_download
snapshot_download("nvidia/PiD", allow_patterns=[
    "checkpoints/flux2_ae.safetensors",
    "checkpoints/PiD_res2k_sr4x_official_flux2_distill_4step/*",
    "checkpoints/PiD_res2kto4k_sr4x_official_flux2_distill_4step/*",
], local_dir="/workspace/PiD")
print("  PiD flux2 checkpoints ready")
PY

echo "=== [3/6] base models (FLUX.2 klein + Qwen LLM for segment) ==="
python - <<'PY'
from huggingface_hub import snapshot_download
snapshot_download("black-forest-labs/FLUX.2-klein-9B")
snapshot_download("Qwen/Qwen2.5-14B-Instruct")
print("  models cached")
PY

echo "=== [4/6] verify model integrity (sha256) ==="
if [ -f /workspace/hf_cache/.verified ]; then
  echo "  already verified (delete /workspace/hf_cache/.verified to re-check)"
else
  python /workspace/scriptframes/runpod/verify_models.py \
    black-forest-labs/FLUX.2-klein-9B Qwen/Qwen2.5-14B-Instruct \
    && touch /workspace/hf_cache/.verified
fi

echo "=== [5/6] references reminder ==="
if [ -d /workspace/references/full ]; then
  echo "  references present: $(ls /workspace/references/full | wc -l) full, $(ls /workspace/references/closeup 2>/dev/null | wc -l) closeup"
else
  echo "  NOTE: put your character anchor packs at /workspace/references/{closeup,full} before generating."
fi

echo "=== [6/6] done ==="
