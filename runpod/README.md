# Running scriptframes on RunPod — full guide

This is the complete, copy-paste guide to go from a brand-new pod to finished images.

---

## TL;DR (one-command bootstrap)

On a fresh pod with a network volume mounted at `/workspace`:

```bash
cd /workspace && \
git clone https://github.com/Sampath-04/scriptframes && \
export HF_TOKEN=hf_your_token && \
bash scriptframes/runpod/setup.sh
```

Then download a LoRA and run a project (see [Phase 3](#phase-3--add-a-lora) onward).

---

## Phase 0 — Create the pod & volume (one time)

In the RunPod console:

1. **Storage → create a Network Volume**, size **≥150 GB**, in a region you'll deploy in.
   - Why 150 GB: FLUX (~10 GB lean) + Qwen-14B (~28 GB) + PiD checkpoints + your LoRAs + generated images, with headroom.
2. **Deploy a Pod**:
   - **Type: On-Demand** (NOT Spot — Spot gets reclaimed and wipes your container mid-run).
   - **GPU:** A100 80 GB or H100 (comfortable for everything). See [GPU & VRAM](#gpu--vram) for cheaper 24 GB options.
   - **Template:** a RunPod **PyTorch** image (ships with torch + CUDA).
   - **Attach the network volume** at mount path **`/workspace`**.
3. Keep some account **balance** funded so the volume isn't garbage-collected.

> **The golden rule of this setup:** pip packages live on the *container* and are wiped
> on **every** pod stop/restart. Only the **`/workspace` volume** persists (models, LoRAs,
> projects). After any restart you just re-run `setup.sh` — it skips already-downloaded
> models, so it only takes ~2 min.

---

## Phase 1 — Get the code (just `git clone`)

```bash
cd /workspace
git clone https://github.com/Sampath-04/scriptframes
```
That's it — no file transfers. (If you make code changes locally, `git pull` on the pod to update.)

---

## Phase 2 — One-time setup

1. **Accept the FLUX.1-dev license** (once, in a browser): https://huggingface.co/black-forest-labs/FLUX.1-dev → *Agree and access repository*.
2. **Create a HuggingFace Read token**: https://huggingface.co/settings/tokens (type **Read** — it can access gated repos). Then:
   ```bash
   export HF_TOKEN=hf_your_token
   ```
3. **Run setup:**
   ```bash
   bash /workspace/scriptframes/runpod/setup.sh
   ```

   What it does (all idempotent — safe to re-run):
   - installs the pinned Python stack (torch is from the image; diffusers/transformers/etc.)
   - installs **NVIDIA PiD** + downloads its checkpoints (for optional 2K/4K upscaling)
   - downloads **FLUX.1-dev** (skipping the redundant 24 GB single-file copy) + **Qwen2.5-14B**
   - **SHA-256 verifies** every model file (catches corrupted downloads)

   Expect it to end with `ALL FILES VERIFIED INTACT` then `[6/6] done`. First run downloads
   ~40 GB (10–25 min depending on the node); later runs are instant for models.

---

## Phase 3 — Add a LoRA

Any **FLUX.1-dev** LoRA on HuggingFace (SDXL / FLUX.2 LoRAs will NOT load):

```bash
export HF_HOME=/workspace/hf_cache
python /workspace/scriptframes/scripts/download_lora.py <hf_repo_id> \
    --out /workspace/models/<name>.safetensors
```

Example (Black Myth: Wukong, trigger word `wukong`, scale ~0.3):
```bash
python /workspace/scriptframes/scripts/download_lora.py \
    wanghaofan/Black-Myth-Wukong-FLUX-LoRA \
    --out /workspace/models/wukong_lora.safetensors
```

---

## Phase 4 — Make a profile

A profile is the only thing that changes per character/series. Copy an example and edit it:
```bash
cd /workspace/scriptframes
cp profiles/cinematic-character.yaml profiles/wukong.yaml
```
Edit `profiles/wukong.yaml`:
- `lora_path: /workspace/models/wukong_lora.safetensors`
- `lora_scale: 0.3`
- `trigger_word: "wukong"`
- `character_brief:` describe the character + style so the LLM writes on-character prompts
- `style_suffix:` global style tokens (e.g. `cinematic, highly detailed, dramatic lighting`)
- `min_beats` / `max_beats`: how many images per script
- (optional) `upscale: pid` + `pid_resolution: 2k`

---

## Phase 5 — Generate a video's images

```bash
cd /workspace/scriptframes
export HF_HOME=/workspace/hf_cache
export HF_TOKEN=hf_your_token
mkdir -p projects/myvideo
```

### Step 1 — Add your script  ← this is the input you provide
The pipeline reads a plain-text file at **`projects/myvideo/script.txt`** (your full
narration/script). Create it with whichever method suits you:

- **Jupyter file editor (easiest for long text):** RunPod pods expose JupyterLab — open it,
  navigate to `workspace/scriptframes/projects/myvideo/`, create `script.txt`, paste your
  script, save.
- **nano:** `apt-get install -y nano && nano projects/myvideo/script.txt` (paste, Ctrl-O, Enter, Ctrl-X).
- **Heredoc (paste the whole block):**
  ```bash
  cat > projects/myvideo/script.txt <<'EOF'
  Your full script goes here.
  As many lines/paragraphs as you want.
  EOF
  ```
- **From your PC:** put it in a file locally and `runpodctl send script.txt`, then
  `runpodctl receive <code>` on the pod and move it to `projects/myvideo/script.txt`.

Confirm it's there: `head -3 projects/myvideo/script.txt`

**Worked example** — paste this whole block to create a ready-to-run script:
```bash
mkdir -p projects/demo
cat > projects/demo/script.txt <<'SCRIPT_EOF'
The Lighthouse Keeper

For forty years he kept the light burning, alone on the rock.
Ships passed in the dark, never knowing his name.
One night the storm tore the lamp away, and he climbed the tower with a lantern gripped in his teeth.
By dawn the sea was calm, and the village below never knew how close they came.
SCRIPT_EOF
head -3 projects/demo/script.txt
```
Longer narration scripts work exactly the same way — just more lines between the markers.

> The script's length drives how many images you get — the LLM splits it into
> `min_beats`–`max_beats` beats (set in your profile). A short script can't make 40 beats;
> lower `min_beats` for short tests.

### Step 2 — Script → per-image prompts (loads Qwen, ~1 min)
```bash
scriptframes segment projects/myvideo --config profiles/wukong.yaml
#  writes projects/myvideo/beats.json + manifest.json
#  (optional) open beats.json to tweak prompts; if you edit it, re-run segment to rebuild
```

### Step 3 — Smoke-test 3 images first (loads FLUX + LoRA)
```bash
scriptframes generate projects/myvideo --config profiles/wukong.yaml --limit 3
#  check projects/myvideo/images/01.png..03.png before committing to the full run
```

### Step 4 — Full unattended run (resumable + continue-on-error)
```bash
tmux new -s gen        # so it survives disconnects
scriptframes generate projects/myvideo --config profiles/wukong.yaml
#  detach: Ctrl-b then d   |   reattach: tmux attach -t gen
```

### Step 5 — Re-run only failed beats (if any)
```bash
scriptframes generate projects/myvideo --config profiles/wukong.yaml --retry-failed
```

### Step 6 — (optional) PiD upscale to 2K/4K
```bash
scriptframes upscale projects/myvideo --config profiles/wukong.yaml
```

Output layout:
```
projects/myvideo/
├── script.txt
├── beats.json        # the LLM's per-image prompts
├── manifest.json     # prompt + seed + status per image
├── images/           # 01.png … NN.png  (generated)
└── images_2k/        # upscaled (if you ran `upscale`)
```

---

## Phase 6 — Get the results to your machine

```bash
cd /workspace/scriptframes/projects/myvideo
tar czf /workspace/myvideo.tar.gz images images_2k 2>/dev/null
runpodctl send /workspace/myvideo.tar.gz
#  then on your PC:  runpodctl receive <code>   (install runpodctl from github.com/runpod/runpodctl)
```

---

## Phase 7 — Stop (don't terminate)

**Stop** the pod when done (don't *Terminate* — that can delete the volume). Next session:
```bash
cd /workspace && export HF_TOKEN=hf_xxx && bash scriptframes/runpod/setup.sh   # ~2 min, reinstalls packages
```
…and you're straight back to Phase 5. (`git pull` first if you changed the code.)

---

## GPU & VRAM

- **A100/H100 80 GB** — everything runs with zero tuning (current default; FLUX loads in full bf16, Qwen-14B in bf16).
- **48 GB (A6000/L40S)** — fine for generation; Qwen-14B fits.
- **24 GB (RTX 4090 / L4)** — *possible* but needs a low-VRAM path (FLUX in **fp8 + CPU offload**, and **Qwen-7B** or 4-bit Qwen). This isn't enabled by default yet — ask and it's a small config/code addition (`low_vram` mode + `profiles/lowvram.yaml`).

Note: `segment` (Qwen) and `generate` (FLUX) are **separate commands**, so the two large
models never need to be in VRAM at once.

---

## Troubleshooting (issues we actually hit)

| Symptom | Cause / fix |
|---|---|
| `ModuleNotFoundError` after a restart | Pod reset wiped pip packages → re-run `setup.sh`. |
| Images come out **pure white** | A **corrupted FLUX download**. Re-run `setup.sh` (it re-verifies via SHA-256); or delete `hf_cache/hub/models--black-forest-labs--FLUX.1-dev` and re-download. |
| `Disk quota exceeded` | Volume too small / redundant files. `setup.sh` already skips the 24 GB single-file FLUX; bump the volume to 150 GB if needed. |
| `huggingface-cli login` fails | It's renamed to `hf auth login`; `setup.sh`/env `HF_TOKEN` handles auth. |
| Download **stalls** at a big file | `hf_transfer` stalling — `setup.sh` keeps it **off** for reliability. |
| 403 / gated repo | Accept the FLUX license + use a **Read** token (fine-grained tokens need "access public gated repos" enabled). |
| ai-toolkit training crashes at "sampling" | `lora_config.yaml` already sets `disable_sampling: true`. |
| Pasting long Python one-liners breaks | Put it in a `.py` file and run it; don't paste multi-line code into the shell. |
| LoRA loads but images look off | Tune `lora_scale` (try 0.3–1.0) and the prompt wording — config only, no code changes. |
