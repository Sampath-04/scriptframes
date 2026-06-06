def derive_seed(base_seed: int, beat_id: int) -> int:
    return (base_seed + beat_id * 7919) % (2**31 - 1)
