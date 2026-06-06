"""Run an ai-toolkit FLUX LoRA training job and copy the result to a target path.

Assumes ai-toolkit is cloned at /workspace/ai-toolkit. Usage:
    python scripts/train_lora.py --config scripts/lora_config.yaml \
        --out /workspace/models/my_character_lora.safetensors

Note: ai-toolkit pulls bleeding-edge diffusers/transformers. If you trained on
that stack, switch back to the inference stack (runpod/setup.sh) before generating.
"""
import argparse
import shutil
import subprocess
from pathlib import Path

AI_TOOLKIT = Path("/workspace/ai-toolkit")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    subprocess.run(
        ["python", str(AI_TOOLKIT / "run.py"), str(Path(args.config).resolve())],
        check=True,
    )
    produced = sorted(
        Path("/workspace/lora_output").rglob("*.safetensors"),
        key=lambda p: p.stat().st_mtime,
    )
    if not produced:
        raise SystemExit("no .safetensors produced by training")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(produced[-1], args.out)
    print(f"LoRA ready at {args.out}")


if __name__ == "__main__":
    main()
