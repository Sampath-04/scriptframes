"""Optional NVIDIA PiD upscaling stage.

PiD (https://github.com/nv-tlabs/PiD) is a pixel-diffusion decoder that turns an
image (via VAE encode -> PiD decode) into a super-resolved 2K/4K frame in a fast
4-step pass. We use its `from_clean` entry point as a post-process upscaler so the
proven FLUX+LoRA generator stays untouched.

The exact PiD CLI/flags are pinned during the on-pod validation step (see
runpod/setup.sh + runpod/README.md). This module shells out to that entry point
per image and is driven entirely by the profile config (upscale, pid_resolution,
pid_dir), so enabling 4K is just a YAML change.
"""
import subprocess
import sys
from pathlib import Path

# Output long edge per target. PiD 16:9 checkpoints emit 2688x1536 (2k) / ~4K.
_CHECKPOINT = {"2k": "2k", "4k": "2kto4k"}


def upscale_image(input_path, output_path, config) -> None:
    ckpt = _CHECKPOINT.get(config.pid_resolution, "2k")
    pid_dir = Path(config.pid_dir)
    cmd = [
        sys.executable, "-m", "pid._src.inference.from_clean",
        "--input", str(input_path),
        "--output", str(output_path),
        "--checkpoint", ckpt,
        "--backbone", "flux",
        "--pid_inference_steps", "4",
    ]
    subprocess.run(cmd, check=True, cwd=str(pid_dir))


def upscale_project(images_dir, out_dir, config) -> int:
    images_dir = Path(images_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pngs = sorted(images_dir.glob("*.png"))
    done = 0
    for p in pngs:
        target = out_dir / p.name
        if target.exists():
            continue
        upscale_image(p, target, config)
        done += 1
    return done
