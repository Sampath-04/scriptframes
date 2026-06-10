# scriptframes

Turn a video **script** into a set of **consistent, on-character images** using
**FLUX.2 (klein)** with **reference images** — no LoRA training needed.

You give it: a script + a handful of reference pictures of your character.
It gives you: 40–50 images of *that same character* acting out the script.

## How it keeps the character consistent

Instead of training a model on your character (a LoRA, which drifts), we hand
**FLUX.2 a few reference pictures of the character every time it draws**. It stays
close to those references, so the character looks the same in every scene.

```
script.txt
   │  1) segment  (LLM: Qwen)         → beats.json  (one scene prompt per image,
   │                                                  each tagged closeup or full)
   ▼
beats.json
   │  2) generate (FLUX.2 klein)      → for each beat, feed the matching reference
   │                                     pack (closeup vs full) + the scene prompt
   ▼
images/01.png … NN.png
   │  3) upscale  (optional, NVIDIA PiD) → crisp 2K/4K frames
   ▼
images_2k/
```

## Your reference packs

Put pictures of your character in two folders:

```
references/
  closeup/   ← head-and-shoulders shots (front, 3/4, side, a few expressions)
  full/      ← full-body shots (front, 3/4, side, back, sitting, …)
```

~6–8 images in each is enough. Variety of **angles** matters more than expressions.
A close-up beat uses the `closeup/` pack; a full-body beat uses the `full/` pack.

## A profile = one character

Everything character-specific is one YAML file (see `profiles/psych-mascot.yaml`):

| Field | Meaning |
|---|---|
| `references_dir` | folder with your `closeup/` + `full/` packs |
| `ref_count` | how many references to feed per image (≈8) |
| `character_brief` | a sentence describing the character (guides the LLM) |
| `style_suffix` | style words added to every prompt |
| `width`/`height`/`steps` | image size + denoising steps (klein ≈ 6) |
| `min_beats`/`max_beats` | how many images per script |
| `upscale`, `pid_*` | optional PiD 2K/4K upscaling |

## Quickstart (on a RunPod pod)

Full steps: **[runpod/README.md](runpod/README.md)**. In short:
```bash
export HF_TOKEN=hf_xxx
bash runpod/setup.sh                       # installs everything + downloads models
# put your reference packs at /workspace/references/{closeup,full}
# put your script at projects/myvideo/script.txt
scriptframes segment  projects/myvideo --config profiles/psych-mascot.yaml
scriptframes generate projects/myvideo --config profiles/psych-mascot.yaml --limit 4
scriptframes upscale  projects/myvideo --config profiles/psych-mascot.yaml   # optional
```

Quick one-off test (no script): `python scripts/generate_one.py --refs /workspace/references/full --prompt "..."`.

## Requirements
- A GPU pod (**48 GB** comfortable; klein 9B ≈ 29 GB) + a ≥120 GB network volume.
- FLUX.2-klein-9B (accept its license on HuggingFace).
- Python 3.10+. Heavy deps are installed by `runpod/setup.sh`.

## Components
```
src/scriptframes/   config, schema, prompt_template, seeds, manifest,
                    segment (LLM), generate (FLUX.2), upscale (PiD), cli
profiles/           example character profiles
scripts/            generate_one.py (one-off reference test)
runpod/             setup.sh, verify_models.py, README.md
```

## Note
Earlier versions used FLUX.1 + a trained LoRA for the character; that drifted on
complex scenes, so the project moved to **FLUX.2 reference conditioning**, which holds
the character far more reliably.
