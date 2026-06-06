from dataclasses import dataclass
from pathlib import Path
import yaml


@dataclass
class Config:
    # Models
    llm_model: str
    flux_model: str
    lora_path: str
    lora_scale: float
    # Generation
    base_seed: int
    width: int
    height: int
    steps: int
    guidance: float
    # Beat segmentation
    min_beats: int
    max_beats: int
    max_parse_retries: int
    # Character / style profile (one pipeline, many characters)
    trigger_word: str = ""          # LoRA trigger, prepended to every prompt
    style_suffix: str = ""          # style tokens appended to every prompt
    character_brief: str = ""       # description of the character/style for the LLM
    # Optional PiD upscaling
    upscale: str = "none"           # "none" | "pid"
    pid_resolution: str = "2k"      # "2k" | "4k" (which PiD checkpoint)
    pid_scale: int = 2              # output = input * scale (2 keeps 48GB happy; 4 = 8K, OOMs)
    pid_dir: str = "/workspace/PiD" # where the PiD repo + checkpoints live


def load_config(path) -> Config:
    data = yaml.safe_load(Path(path).read_text())
    return Config(**data)
