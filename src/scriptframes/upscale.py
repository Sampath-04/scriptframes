"""Optional NVIDIA PiD upscaling stage.

PiD (https://github.com/nv-tlabs/PiD) is a pixel-diffusion decoder: it takes an
image (VAE encode -> PiD decode) and reconstructs it as a super-resolved 2K/4K
frame, adding real high-frequency detail (not just stretching). We drive its
`from_clean` entry point per image so the proven FLUX+LoRA generator is untouched.

Real PiD from_clean flags (confirmed on the pod):
  --backbone flux  --pid_ckpt_type {2k,2kto4k}
  --input_path <img>  --output_dir <dir>  --prompt <caption>  --save_format png
PiD writes into --output_dir with its own filename, so we render into a temp dir
and copy the result to our target name.
"""
import glob
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_CKPT = {"2k": "2k", "4k": "2kto4k"}


def upscale_image(input_path, out_path, prompt, config) -> None:
    ckpt = _CKPT.get(config.pid_resolution, "2k")
    pid_dir = Path(config.pid_dir)
    with tempfile.TemporaryDirectory(dir=str(pid_dir)) as td:
        cmd = [
            sys.executable, "-m", "pid._src.inference.from_clean",
            "--backbone", "flux",
            "--pid_ckpt_type", ckpt,
            "--input_path", str(Path(input_path).resolve()),
            "--output_dir", td,
            "--save_format", "png",
        ]
        if prompt:
            cmd += ["--prompt", prompt]
        subprocess.run(cmd, check=True, cwd=str(pid_dir))
        produced = sorted(
            glob.glob(td + "/**/*.png", recursive=True), key=os.path.getmtime
        )
        if not produced:
            raise RuntimeError(f"PiD produced no output for {input_path}")
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(produced[-1], out_path)


def upscale_project(images_dir, out_dir, config, prompts_by_name=None) -> int:
    images_dir = Path(images_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    prompts_by_name = prompts_by_name or {}
    done = 0
    for p in sorted(images_dir.glob("*.png")):
        target = out_dir / p.name
        if target.exists():
            continue
        upscale_image(p, target, prompts_by_name.get(p.name, ""), config)
        done += 1
    return done
