# Running scriptframes (FLUX.2) on RunPod

Copy-paste guide from a fresh pod to finished images.

## Phase 0 — Pod & volume (once)
- **On-Demand** pod (not Spot), **48 GB GPU** (klein 9B ≈ 29 GB).
- **Network volume ≥120 GB** mounted at `/workspace` (models + PiD + your work persist here).
- Template: a RunPod **PyTorch** image. Keep some account balance so the volume isn't deleted.

> Pip packages live on the container and are wiped on every restart; only `/workspace`
> survives. After a restart, just re-run `setup.sh` (it skips already-downloaded models).

## Phase 1 — Get the code
```bash
cd /workspace
git clone https://github.com/Sampath-04/scriptframes
```

## Phase 2 — Setup (downloads ~60 GB once)
1. Accept the **FLUX.2-klein-9B** license on its HuggingFace page (same account as your token).
2. Create a HF **Read** token, then:
   ```bash
   export HF_TOKEN=hf_your_token
   bash /workspace/scriptframes/runpod/setup.sh
   ```
   Installs diffusers-from-git + torch 2.7 + PiD, downloads FLUX.2 klein + Qwen + PiD
   checkpoints, and SHA-256 verifies them. Ends with `[6/6] done`.

## Phase 3 — Add your reference packs
Your character anchors go here (send them with `runpodctl`, then unpack):
```
/workspace/references/
  closeup/   ← ~8 head-and-shoulders shots
  full/      ← ~8 full-body shots (varied angles)
```
Confirm: `ls /workspace/references/closeup /workspace/references/full`

## Phase 4 — Make a video
```bash
cd /workspace/scriptframes
export HF_HOME=/workspace/hf_cache
export HF_TOKEN=hf_your_token

mkdir -p projects/myvideo
#  put your script in projects/myvideo/script.txt  (e.g. via the Jupyter editor or a heredoc)

scriptframes segment  projects/myvideo --config profiles/psych-mascot.yaml      # script -> beats (+ shot tags)
scriptframes generate projects/myvideo --config profiles/psych-mascot.yaml --limit 4   # smoke test
scriptframes generate projects/myvideo --config profiles/psych-mascot.yaml             # full run (resumable)
scriptframes upscale  projects/myvideo --config profiles/psych-mascot.yaml             # optional PiD 2K
```
Run the full generate inside `tmux` (or `nohup`) so it survives disconnects.

Quick one-off test (no script needed):
```bash
python scripts/generate_one.py --refs /workspace/references/full \
  --prompt "the same cartoon mascot, sitting and driving a small car, worried, flat 2D vector"
```

## Phase 5 — Get images back
```bash
cd projects/myvideo && tar czf /workspace/out.tar.gz images images_2k 2>/dev/null
runpodctl send /workspace/out.tar.gz       # then `runpodctl receive <code>` locally
```

## Output layout
```
projects/myvideo/
├── script.txt
├── beats.json        # the LLM's per-image prompts (+ shot: closeup/full)
├── manifest.json     # prompt + shot + seed + status per image
├── images/           # generated 1344×768 frames
└── images_2k/        # PiD-upscaled (if you ran upscale)
```

## Troubleshooting
| Symptom | Fix |
|---|---|
| `ModuleNotFoundError` after restart | Container packages wiped → re-run `setup.sh`. |
| `torch has no attribute float8_e8m0fnu` | FLUX.2's transformers needs torch ≥2.7 — `setup.sh` upgrades it. |
| CUDA OOM loading klein | Edit the generator to `pipe.enable_model_cpu_offload()` (slower, less VRAM). |
| Character looks off in a shot | Swap a reference in the relevant pack (closeup/full), or add a clearer anchor. |
| Image over/under-cooked | klein is distilled — keep `steps` ≈ 6 (don't raise it). |
| 403 / gated repo | Accept the FLUX.2-klein-9B license + use a Read token. |
