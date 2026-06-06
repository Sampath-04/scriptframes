# scriptframes

Turn a script into a set of **consistent, on-style images** using **FLUX.1-dev + any LoRA**,
driven by simple per-project **profile configs**. Built to run unattended on a GPU pod:
feed it a script, walk away, come back to 40–50 finished frames.

Originally built for a black-and-white stick-figure channel, now generic — the engine has
no hardcoded character. Each character/series is just a YAML profile.

## How it works

```
script.txt
   │  segment   (open LLM: Qwen2.5)        ← uses the profile's character_brief
   ▼
beats.json      ~N beats, each an image prompt
   │  (optional manual review)
   ▼
generate        (FLUX.1-dev + your LoRA)   ← trigger_word + style_suffix from the profile
   ▼
images/01.png … NN.png   (+ manifest.json: prompt, seed, status per image)
   │  upscale   (optional NVIDIA PiD)      ← 2K / 4K cinematic frames
   ▼
images_2k/ …
```

- **Resumable & continue-on-error**: re-running skips finished images; failures are logged,
  not fatal; `--retry-failed` re-runs just the failures.
- **Reproducible**: deterministic per-beat seeds recorded in the manifest.
- **Profile-driven**: swap character/style by pointing to a different config — no code changes.

## A profile (config) is the only thing that changes per character

| Field | Controls |
|---|---|
| `lora_path`, `lora_scale` | which LoRA, how strongly |
| `trigger_word` | word auto-prepended to every prompt to activate the LoRA |
| `style_suffix` | style tokens appended to every prompt |
| `character_brief` | description fed to the LLM so it writes on-character prompts |
| `width`/`height`/`steps`/`guidance` | generation settings |
| `min_beats`/`max_beats` | how many images per script |
| `upscale`, `pid_resolution` | optional PiD 2K/4K upscaling |

See `profiles/cinematic-character.yaml` and `profiles/bw-lineart.yaml`.

## Quickstart (on a RunPod pod)

Full instructions: **[runpod/README.md](runpod/README.md)**. In short:
```bash
export HF_TOKEN=hf_xxx
bash runpod/setup.sh                                   # install + download + verify
python scripts/download_lora.py <hf_lora_repo> --out /workspace/models/mine.safetensors
# edit a profile, add projects/myvideo/script.txt, then:
scriptframes segment  projects/myvideo --config profiles/mine.yaml
scriptframes generate projects/myvideo --config profiles/mine.yaml
scriptframes upscale  projects/myvideo --config profiles/mine.yaml   # optional
```

## Requirements
- A GPU pod (A100/H100 80 GB recommended) with a ≥150 GB network volume.
- FLUX.1-dev (gated — accept its license) + a **FLUX.1-dev** LoRA. SDXL/FLUX.2 LoRAs won't load.
- Python 3.10+. Heavy deps (torch/diffusers/transformers/PiD) are installed by `runpod/setup.sh`.

## Components
```
src/scriptframes/   config, schema, prompt_template, seeds, manifest,
                    segment (LLM), generate (FLUX), upscale (PiD), cli
profiles/           example character/style profiles
scripts/            download_lora.py, optional LoRA training (train_lora.py)
runpod/             setup.sh, verify_models.py, README.md
```

## Status / honest notes
- FLUX + LoRA generation is proven working end-to-end.
- PiD upscaling integration is wired but its exact CLI is confirmed on first pod run
  (see note in `src/scriptframes/upscale.py`).
- LoRA quality still needs per-character tuning (`lora_scale`, prompt phrasing) — that's
  config, never code.
