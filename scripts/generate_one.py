"""Generate ONE image with FLUX.2 klein + reference images - for quick tests.

Examples:
  python scripts/generate_one.py --refs /workspace/references/full \
      --prompt "the same cartoon mascot, sitting and driving a small car, worried, flat 2D vector"
  python scripts/generate_one.py --refs /workspace/references/closeup \
      --prompt "the same cartoon mascot, head and shoulders, crying" --steps 6
"""
import argparse


def main():
    import glob
    import torch
    from diffusers import Flux2KleinPipeline
    from PIL import Image

    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--refs", default="/workspace/references/full", help="folder of reference pngs")
    ap.add_argument("--out", default="/workspace/flux2_test.png")
    ap.add_argument("--model", default="black-forest-labs/FLUX.2-klein-9B")
    ap.add_argument("--steps", type=int, default=6)
    ap.add_argument("--width", type=int, default=1344)
    ap.add_argument("--height", type=int, default=768)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    pipe = Flux2KleinPipeline.from_pretrained(a.model, torch_dtype=torch.bfloat16).to("cuda")
    refs = [Image.open(p).convert("RGB") for p in sorted(glob.glob(a.refs + "/*.png"))]
    print(f"loaded {len(refs)} reference images from {a.refs}")
    img = pipe(
        image=refs, prompt=a.prompt, width=a.width, height=a.height,
        num_inference_steps=a.steps, generator=torch.Generator("cuda").manual_seed(a.seed),
    ).images[0]
    img.save(a.out)
    print("saved", a.out, img.size)


if __name__ == "__main__":
    main()
