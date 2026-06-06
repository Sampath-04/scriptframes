"""Build a LoRA training dataset: copy reference images into one folder and write
a caption .txt per image. Usage:

    python scripts/prepare_dataset.py <src_dir> [<src_dir> ...] \
        --out /workspace/dataset --trigger mychar \
        --caption "mychar, <describe the recurring look/style here>"
"""
import argparse
import shutil
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--trigger", required=True)
    ap.add_argument("--caption", default="", help="full caption; defaults to the trigger word")
    args = ap.parse_args()

    caption = args.caption or args.trigger
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    n = 0
    for src in args.src:
        for img in sorted(Path(src).glob("*.png")):
            n += 1
            dst = out / f"img_{n:03d}.png"
            shutil.copy(img, dst)
            dst.with_suffix(".txt").write_text(caption)
    print(f"prepared {n} images in {out} (trigger: {args.trigger})")


if __name__ == "__main__":
    main()
