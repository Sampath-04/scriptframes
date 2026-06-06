#!/usr/bin/env bash
# scriptframes - one-shot setup for a fresh RunPod pod.
#
# IMPORTANT: pip packages live on the pod CONTAINER and are wiped on every
# restart; only the /workspace network volume persists. Re-run this script after
# any pod restart. Models are cached on the volume, so they download only once.
#
# Prereqs:
#   - Attach a network volume (>=150 GB) at /workspace
#   - Put this repo at /workspace/scriptframes
#   - Accept the FLUX.1-dev license on HuggingFace, then:  export HF_TOKEN=hf_xxx
set -euo pipefail

export HF_HOME=/workspace/hf_cache
export HF_HUB_ENABLE_HF_TRANSFER=0     # reliability over speed (hf_transfer stalls on big files)
: "${HF_TOKEN:?set HF_TOKEN first:  export HF_TOKEN=hf_xxx}"

echo "=== [1/6] torch (from base image) ==="
python -c "import torch; print('  torch', torch.__version__, 'cuda', torch.cuda.is_available())"

echo "=== [2/6] python packages (pinned for FLUX + PiD) ==="
pip install -q -e /workspace/scriptframes
# transformers>=4.57 (needed by PiD) requires torch>=2.7 for the fp8 dtype
# torch.float8_e8m0fnu. Stock pod images often ship an older torch, so upgrade it.
pip install -q --upgrade "torch==2.7.1" "torchvision==0.22.1" "torchaudio==2.7.1" \
    --index-url https://download.pytorch.org/whl/cu126
pip install -q "huggingface_hub>=0.27" "diffusers>=0.37" "transformers>=4.57" \
    accelerate peft sentencepiece protobuf

echo "=== [3/6] NVIDIA PiD (pixel-diffusion upscaler) ==="
if [ ! -d /workspace/PiD ]; then
  git clone https://github.com/nv-tlabs/PiD.git /workspace/PiD
fi
pip install -q hydra-core omegaconf attrs einops loguru termcolor fvcore iopath \
    imageio opencv-python-headless pandas boto3 botocore wandb
pip install -q -e /workspace/PiD
# PiD checkpoints — ONLY the flux ones (the full set is ~33GB across 7 backbones;
# we use FLUX.1 only, so pull just the flux 2k/4k decoders + the shared FLUX VAE ~5.5GB)
python - <<'PY'
from huggingface_hub import snapshot_download
snapshot_download(
    "nvidia/PiD",
    allow_patterns=[
        "checkpoints/ae.safetensors",
        "checkpoints/PiD_res2k_sr4x_official_flux_distill_4step/*",
        "checkpoints/PiD_res2kto4k_sr4x_official_flux_distill_4step/*",
    ],
    local_dir="/workspace/PiD",
)
print("  PiD flux checkpoints ready")
PY

echo "=== [4/6] base models (skip the redundant 24 GB single-file FLUX copy) ==="
python - <<'PY'
from huggingface_hub import snapshot_download
# diffusers loads FLUX from the transformer/ vae/ text_encoder*/ subfolders, so we
# skip the redundant standalone flux1-dev.safetensors + ae.safetensors (~24 GB).
snapshot_download("black-forest-labs/FLUX.1-dev",
                  ignore_patterns=["flux1-dev.safetensors", "ae.safetensors", "*.gguf"])
snapshot_download("Qwen/Qwen2.5-14B-Instruct")
print("  models cached")
PY

echo "=== [5/6] verify model integrity (sha256) ==="
if [ -f /workspace/hf_cache/.verified ]; then
  echo "  already verified earlier (delete /workspace/hf_cache/.verified to re-check)"
else
  python /workspace/scriptframes/runpod/verify_models.py black-forest-labs/FLUX.1-dev Qwen/Qwen2.5-14B-Instruct \
    && touch /workspace/hf_cache/.verified
fi

echo "=== [6/6] done ==="
echo "Next: download a LoRA, then run a project. See runpod/README.md"
