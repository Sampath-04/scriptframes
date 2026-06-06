"""Generate a single image from one prompt - for character design / one-offs.

Examples:
  # plain FLUX.1-dev
  python scripts/generate_one.py --prompt "..." --out /workspace/design/hero.png --seed 1
  # FLUX + a style LoRA
  python scripts/generate_one.py --prompt "..." --out hero.png \
      --lora /workspace/models/cartoon_lora.safetensors --lora-scale 0.9 --seed 1
"""
import argparse


def main():
    import torch
    from diffusers import FluxPipeline

    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="black-forest-labs/FLUX.1-dev")
    ap.add_argument("--lora", default="")
    ap.add_argument("--lora-scale", type=float, default=0.9)
    ap.add_argument("--width", type=int, default=1024)
    ap.add_argument("--height", type=int, default=1024)
    ap.add_argument("--steps", type=int, default=28)
    ap.add_argument("--guidance", type=float, default=3.5)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    pipe = FluxPipeline.from_pretrained(a.model, torch_dtype=torch.bfloat16).to("cuda")
    kw = {}
    if a.lora:
        pipe.load_lora_weights(a.lora)
        kw["joint_attention_kwargs"] = {"scale": a.lora_scale}
    img = pipe(
        prompt=a.prompt, width=a.width, height=a.height,
        num_inference_steps=a.steps, guidance_scale=a.guidance,
        generator=torch.Generator("cuda").manual_seed(a.seed), **kw,
    ).images[0]
    import os
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    img.save(a.out)
    print("saved", a.out, img.size)


if __name__ == "__main__":
    main()
