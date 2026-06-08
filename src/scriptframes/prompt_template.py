DEFAULT_NEGATIVE = (
    "lowres, bad anatomy, extra limbs, signature, watermark, text artifacts, blurry"
)


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
        '"image_prompt" (a single line describing the drawing).\n'
        "Every image_prompt MUST feature the SAME recurring MAIN character described above, "
        "kept large and prominent, depicted consistently, conveying the beat's emotion through "
        "its pose, expression, and simple symbolic props (storm cloud, warning sign, thought "
        "bubble, hearts).\n"
        "CRITICAL character rules:\n"
        "- Always refer to the main character exactly as described above; NEVER replace it with "
        "a generic 'man', 'woman', 'person', 'boy', 'girl', 'animal', or a human name - the main "
        "character is ALWAYS the same recurring character.\n"
        "- If a beat needs other characters, add them as separate 'other people' (generic, may "
        "look different) who are NOT the main character and never replace it.\n"
        "- Keep the main character the clear, prominent focus, but VARY its placement across "
        "beats - sometimes left, sometimes right, sometimes center - and vary framing (full "
        "body vs close-up) and pose/expression, leaving space on the opposite side for props, "
        "icons, or captions. Avoid putting it dead-center every time.\n"
        "Do not include any prose outside the JSON array."
    )


def build_user_prompt(script_text: str) -> str:
    return f"SCRIPT:\n{script_text}\n\nReturn the JSON array of beats now."


def finalize_prompt(image_prompt: str, trigger_word: str = "", style_suffix: str = "") -> str:
    """Assemble the final prompt: <trigger>, <scene prompt>. <style suffix>.

    trigger_word and style_suffix come from the profile config, so the same
    pipeline serves any character/style. Each is added only if not already present.
    """
    base = image_prompt.strip().rstrip(".")
    if style_suffix and style_suffix.split(",")[0].strip().lower() not in base.lower():
        base = f"{base}. {style_suffix}"
    if trigger_word and not base.lower().startswith(trigger_word.lower()):
        base = f"{trigger_word}, {base}"
    return base
