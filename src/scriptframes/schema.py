from dataclasses import dataclass, asdict
import json
import re


class BeatValidationError(Exception):
    pass


@dataclass
class Beat:
    id: int
    source_line: str
    scene_description: str
    emotion: str
    image_prompt: str
    shot: str = "full"          # "closeup" | "full" -> picks the reference pack

    def to_dict(self):
        return asdict(self)


REQUIRED_FIELDS = ("id", "source_line", "scene_description", "emotion", "image_prompt")


def _norm_shot(value) -> str:
    v = str(value).strip().lower()
    return "closeup" if v.startswith("close") else "full"


def extract_json_block(raw: str) -> str:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    starts = [i for i in (text.find("["), text.find("{")) if i != -1]
    if not starts:
        raise BeatValidationError("no JSON found in LLM output")
    return text[min(starts):]


def parse_beats(raw: str) -> list:
    block = extract_json_block(raw)
    try:
        data, _ = json.JSONDecoder().raw_decode(block)
    except json.JSONDecodeError as e:
        raise BeatValidationError(f"invalid JSON: {e}") from e
    if isinstance(data, dict) and "beats" in data:
        data = data["beats"]
    if not isinstance(data, list):
        raise BeatValidationError("expected a JSON array of beats")
    beats = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise BeatValidationError(f"beat {i} is not an object")
        missing = [f for f in REQUIRED_FIELDS if f not in item]
        if missing:
            raise BeatValidationError(f"beat {i} missing fields: {missing}")
        beats.append(Beat(
            id=int(item["id"]),
            source_line=str(item["source_line"]),
            scene_description=str(item["scene_description"]),
            emotion=str(item["emotion"]),
            image_prompt=str(item["image_prompt"]),
            shot=_norm_shot(item.get("shot", "full")),
        ))
    return beats


def validate_beat_count(beats, min_beats: int, max_beats: int) -> None:
    if not (min_beats <= len(beats) <= max_beats):
        raise BeatValidationError(
            f"got {len(beats)} beats, expected {min_beats}-{max_beats}"
        )
