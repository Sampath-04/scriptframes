from .schema import parse_beats, validate_beat_count, BeatValidationError
from .prompt_template import build_system_prompt, build_user_prompt


def generate_beats(script_text: str, llm, config):
    system = build_system_prompt(config.min_beats, config.max_beats, config.character_brief)
    user = build_user_prompt(script_text)
    last_err = None
    for _ in range(config.max_parse_retries):
        raw = llm.generate(system, user)
        try:
            beats = parse_beats(raw)
            validate_beat_count(beats, config.min_beats, config.max_beats)
            return beats
        except BeatValidationError as e:
            last_err = e
            user = (
                build_user_prompt(script_text)
                + f"\n\nYour previous answer was invalid: {e}. "
                "Return ONLY a valid JSON array of beats."
            )
    raise BeatValidationError(
        f"failed after {config.max_parse_retries} attempts: {last_err}"
    )
