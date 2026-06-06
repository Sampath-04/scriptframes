# Running scriptframes on RunPod

## Pod & volume (do this once)
- **On-Demand pod** (NOT Spot — Spot gets reclaimed and wipes your container).
- GPU: A100/H100 80 GB (generation + PiD comfortably). 24 GB works for generation-only.
- **Network volume ≥150 GB** mounted at `/workspace` (holds models, LoRAs, PiD, projects).
- Keep account balance funded so the volume isn't garbage-collected.

> Why this matters: pip packages live on the container and are wiped on every pod
> restart; only `/workspace` survives. Models/LoRAs persist there, so after a
> restart you just re-run `setup.sh` (fast — it skips already-downloaded models).

## First-time setup
1. Accept the FLUX.1-dev license at huggingface.co/black-forest-labs/FLUX.1-dev.
2. Create a HF **Read** token (works with gated repos) and:
   ```bash
   export HF_TOKEN=hf_xxx
   ```
3. Put the repo at `/workspace/scriptframes`, then:
   ```bash
   bash /workspace/scriptframes/runpod/setup.sh
   ```
   Installs packages + PiD, downloads FLUX (lean) + Qwen, and SHA-256 verifies them.

## Add a LoRA (any FLUX.1-dev LoRA)
```bash
export HF_HOME=/workspace/hf_cache
python /workspace/scriptframes/scripts/download_lora.py <hf_repo_id> \
    --out /workspace/models/<name>.safetensors
```
Point your profile's `lora_path` at that file.

## Make a video
```bash
cd /workspace/scriptframes
export HF_HOME=/workspace/hf_cache
export HF_TOKEN=hf_xxx

mkdir -p projects/myvideo
#  put your script in projects/myvideo/script.txt, and a profile in e.g. profiles/mine.yaml

scriptframes segment  projects/myvideo --config profiles/mine.yaml      # script -> prompts
#  (optional) review/edit projects/myvideo/beats.json
scriptframes generate projects/myvideo --config profiles/mine.yaml --limit 3   # smoke test
scriptframes generate projects/myvideo --config profiles/mine.yaml             # full run (resumable)
scriptframes generate projects/myvideo --config profiles/mine.yaml --retry-failed
scriptframes upscale  projects/myvideo --config profiles/mine.yaml             # optional PiD 2K/4K
```
Run the full generate inside `tmux` so it survives disconnects.

## Get images back to your machine
```bash
cd projects/myvideo && tar czf /workspace/myvideo.tar.gz images images_2k 2>/dev/null
runpodctl send /workspace/myvideo.tar.gz       # then `runpodctl receive <code>` locally
```

## Notes / lessons baked in
- Downloads run with `HF_HUB_ENABLE_HF_TRANSFER=0` (the fast path stalls on big files).
- FLUX download skips the redundant 24 GB single-file copy (diffusers uses the subfolders).
- `verify_models.py` hashes every model file so a corrupted download is caught early.
- PiD upscaling: the exact `from_clean` CLI flags are confirmed during first run on the
  pod; adjust `src/scriptframes/upscale.py` if PiD's entry point differs in your version.
