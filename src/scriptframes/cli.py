import argparse
import json
from pathlib import Path

from .config import load_config
from . import manifest as M


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="scriptframes")
    sub = parser.add_subparsers(dest="command", required=True)

    p_seg = sub.add_parser("segment", help="script.txt -> beats.json + manifest.json")
    p_seg.add_argument("project")
    p_seg.add_argument("--config", default="config.yaml")

    p_gen = sub.add_parser("generate", help="generate images from manifest.json")
    p_gen.add_argument("project")
    p_gen.add_argument("--config", default="config.yaml")
    p_gen.add_argument("--limit", type=int, default=None, help="smoke-test N images")
    p_gen.add_argument("--retry-failed", action="store_true", dest="retry_failed")

    p_up = sub.add_parser("upscale", help="PiD-upscale generated images to 2K/4K")
    p_up.add_argument("project")
    p_up.add_argument("--config", default="config.yaml")

    return parser


def cmd_segment(args) -> None:
    config = load_config(args.config)
    from .llm import QwenLLM           # lazy: heavy GPU import
    from .segment import generate_beats
    project = Path(args.project)
    script = (project / "script.txt").read_text(encoding="utf-8")
    llm = QwenLLM(config.llm_model)
    beats = generate_beats(script, llm, config)
    (project / "beats.json").write_text(
        json.dumps([b.to_dict() for b in beats], indent=2)
    )
    M.save_manifest(project / "manifest.json",
                    M.build_manifest(project.name, beats, config.base_seed))
    print(f"wrote {len(beats)} beats to {project / 'beats.json'}")


def cmd_generate(args) -> None:
    config = load_config(args.config)
    from .generate import run_batch, Flux2Generator  # lazy: heavy GPU import
    project = Path(args.project)
    manifest = M.load_manifest(project / "manifest.json")
    generator = Flux2Generator(config)
    run_batch(manifest, project / "manifest.json", project / "images",
              generator, config, limit=args.limit, only_failed=args.retry_failed)
    done = sum(1 for e in manifest["entries"] if e["status"] == "done")
    print(f"done: {done}/{len(manifest['entries'])} images")


def cmd_upscale(args) -> None:
    config = load_config(args.config)
    if config.upscale != "pid":
        raise SystemExit("set `upscale: pid` in the config to use this command")
    from .upscale import upscale_project   # lazy: needs the PiD install
    from .prompt_template import finalize_prompt
    project = Path(args.project)
    # feed each image's own prompt to PiD as the decoder caption
    prompts = {}
    manifest = M.load_manifest(project / "manifest.json")
    for e in manifest["entries"]:
        name = Path(e["output_file"]).name
        prompts[name] = finalize_prompt(e["image_prompt"], config.style_suffix)
    n = upscale_project(
        project / "images", project / f"images_{config.pid_resolution}", config, prompts
    )
    print(f"upscaled {n} images to {config.pid_resolution}")


def main(argv=None) -> None:
    args = build_parser().parse_args(argv)
    {"segment": cmd_segment, "generate": cmd_generate, "upscale": cmd_upscale}[args.command](args)


if __name__ == "__main__":
    main()
