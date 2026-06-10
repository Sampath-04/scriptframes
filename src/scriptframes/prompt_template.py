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
        '"shot" (use "closeup" ONLY for a pure face/upper-body emotion moment with no setting; '
        'use "full" for ANY scene that has a setting, action, props, or full body - e.g. sitting '
        'in a car, on a ropeway, walking),\n'
        '"image_prompt" (a VIVID, COMPLETE scene description - 2 to 4 clauses, NOT a bare line).\n'
        "\n"
        "Each image_prompt MUST include ALL of:\n"
        " (a) the SAME recurring main character (described above) with a SPECIFIC pose and facial "
        "expression;\n"
        " (b) the setting/background with concrete objects (a room with a window and a couch, a "
        "city street, the inside of a small car, a misty mountain ropeway, etc.);\n"
        " (c) a symbolic element that conveys the idea where useful (a thought bubble with a small "
        "image inside it, a dark storm cloud, a warning triangle, floating question marks, hearts);\n"
        " (d) composition - where the character is placed (left / right / center) and what fills "
        "the opposite side.\n"
        "NEVER write a bare prompt like 'the mascot looking worried'. NEVER replace the main "
        "character with a generic 'man', 'woman', 'person', 'boy', 'girl', 'animal', or a name; "
        "extra characters are 'other people' (generic). Vary placement and framing across beats.\n"
        "Example of a GOOD image_prompt: \"the same cartoon mascot sitting inside a small car "
        "gripping the steering wheel with both hands, eyes wide and sweating with worry, a thought "
        "bubble in the upper-left showing two cars crashing, simple street and sky in the "
        "background, mascot on the right side of the frame\".\n"
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
