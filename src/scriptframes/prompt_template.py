def build_system_prompt(min_beats: int, max_beats: int, character_brief: str) -> str:
    return (
        "You are a storyboard artist for a YouTube channel.\n"
        f"{character_brief}\n"
        f"Break the user's script into between {min_beats} and {max_beats} sequential "
        "visual beats.\n"
        "Return ONLY a JSON array. Each element must be an object with exactly these keys:\n"
        '"id" (integer, starting at 1, sequential),\n'
        '"source_line" (the script sentence(s) this beat depicts),\n'
        '"scene_description" (what is happening, plain language),\n'
        '"emotion" (one short label, e.g. anxiety, conflict, awe, calm, determination),\n'
        '"shot" (either "closeup" for an emotional face/upper-body moment, or "full" for a '
        'full-body scene/action),\n'
        '"image_prompt" (a single line describing the drawing).\n'
        "Every image_prompt MUST feature the SAME recurring main character described above, "
        "depicted consistently. Refer to it as 'the same cartoon mascot character' (or similar) "
        "and NEVER replace it with a generic 'man', 'woman', 'person', 'boy', 'girl', 'animal', "
        "or a human name. If a beat needs others, call them 'other people' (generic). Vary the "
        "setting, pose, expression, and the character's placement (left/right/center) across beats.\n"
        "Do not include any prose outside the JSON array."
    )


def build_user_prompt(script_text: str) -> str:
    return f"SCRIPT:\n{script_text}\n\nReturn the JSON array of beats now."


def finalize_prompt(image_prompt: str, style_suffix: str = "") -> str:
    """Append the style tokens to a beat's prompt (the references lock the character,
    so no trigger word is needed)."""
    base = image_prompt.strip().rstrip(".")
    if style_suffix and style_suffix.split(",")[0].strip().lower() not in base.lower():
        base = f"{base}. {style_suffix}"
    return base
