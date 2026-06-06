import json
from pathlib import Path
from .seeds import derive_seed


def build_manifest(project_name: str, beats, base_seed: int) -> dict:
    entries = []
    for b in beats:
        entries.append({
            "id": b.id,
            "image_prompt": b.image_prompt,
            "negative_prompt": b.negative_prompt,
            "seed": derive_seed(base_seed, b.id),
            "output_file": f"images/{b.id:02d}.png",
            "status": "pending",
            "error": None,
        })
    return {"project": project_name, "base_seed": base_seed, "entries": entries}


def save_manifest(path, manifest: dict) -> None:
    Path(path).write_text(json.dumps(manifest, indent=2))


def load_manifest(path) -> dict:
    return json.loads(Path(path).read_text())


def entry_by_id(manifest: dict, beat_id: int) -> dict:
    for e in manifest["entries"]:
        if e["id"] == beat_id:
            return e
    raise KeyError(beat_id)


def mark_done(manifest: dict, beat_id: int) -> None:
    e = entry_by_id(manifest, beat_id)
    e["status"] = "done"
    e["error"] = None


def mark_failed(manifest: dict, beat_id: int, error) -> None:
    e = entry_by_id(manifest, beat_id)
    e["status"] = "failed"
    e["error"] = str(error)


def pending_entries(manifest: dict, images_dir, only_failed: bool = False) -> list:
    out = []
    for e in manifest["entries"]:
        if only_failed:
            if e["status"] == "failed":
                out.append(e)
            continue
        img = Path(images_dir) / Path(e["output_file"]).name
        done = e["status"] == "done" and img.exists()
        if not done:
            out.append(e)
    return out
