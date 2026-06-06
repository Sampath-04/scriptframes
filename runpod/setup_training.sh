#!/usr/bin/env bash
# Install ai-toolkit for LoRA TRAINING (the inference setup.sh does not include it).
# Run after runpod/setup.sh. Training and inference can use slightly different package
# versions; if generation misbehaves after training, just re-run runpod/setup.sh.
set -euo pipefail

cd /workspace
if [ ! -d /workspace/ai-toolkit ]; then
  git clone https://github.com/ostris/ai-toolkit.git /workspace/ai-toolkit
fi
pip install -q -r /workspace/ai-toolkit/requirements.txt
# ai-toolkit FLUX training needs torch>=2.7 (we already use it); keep it pinned.
pip install -q --upgrade "torch==2.7.1" "torchvision==0.22.1" "torchaudio==2.7.1" \
  --index-url https://download.pytorch.org/whl/cu126 || true

echo "ai-toolkit ready at /workspace/ai-toolkit"
echo "Next: prepare_dataset.py -> edit scripts/lora_config.yaml -> train_lora.py"
