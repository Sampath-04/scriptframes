from dataclasses import dataclass
from pathlib import Path
import yaml


@dataclass
class Config:
    # Models
    llm_model: str                  # LLM for the segment step (script -> beats)
    flux2_model: str                # FLUX.2 klein image model
    # Reference-based character consistency (no LoRA)
    references_dir: str             # folder containing `closeup/` and `full/` packs
    ref_count: int                  # how many reference images to feed per generation
    # Generation
    base_seed: int
    width: int
    height: int
    steps: int                      # klein is distilled -> ~6 steps
    # Beat segmentation
    min_beats: int
    max_beats: int
    max_parse_retries: int
    # Character/style profile
    character_brief: str = ""       # description of the character for the LLM
    style_suffix: str = ""          # style tokens appended to every prompt
    # Optional PiD upscaling
    upscale: str = "none"           # "none" | "pid"
    pid_resolution: str = "2k"      # "2k" | "4k"
    pid_scale: int = 2              # output = input * scale (2 keeps 48GB happy)
    pid_backbone: str = "flux2"     # PiD VAE backbone matching the generator
    pid_dir: str = "/workspace/PiD"


def load_config(path) -> Config:
    data = yaml.safe_load(Path(path).read_text())
    return Config(**data)
