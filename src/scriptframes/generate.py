from pathlib import Path
from .prompt_template import finalize_prompt
from . import manifest as M


def run_batch(manifest, manifest_path, images_dir, generator, config,
              limit=None, only_failed=False):
    images_dir = Path(images_dir)
    images_dir.mkdir(parents=True, exist_ok=True)
    todo = M.pending_entries(manifest, images_dir, only_failed=only_failed)
    if limit is not None:
        todo = todo[:limit]
    for e in todo:
        try:
            prompt = finalize_prompt(e["image_prompt"], config.style_suffix)
            shot = e.get("shot", "full")
            image = generator.generate(prompt, shot, e["seed"], config.width, config.height)
            image.save(images_dir / Path(e["output_file"]).name)
            M.mark_done(manifest, e["id"])
        except Exception as ex:  # continue-on-error
            M.mark_failed(manifest, e["id"], ex)
        M.save_manifest(manifest_path, manifest)
    return manifest


class Flux2Generator:
    """FLUX.2 klein with reference-image conditioning (no LoRA).

    For each beat it feeds the reference pack matching the shot type
    (`closeup` vs `full`) so the character stays consistent across scenes.
    GPU imports live inside the methods so `import scriptframes.generate`
    stays importable without torch.
    """

    def __init__(self, config):
        import torch
        from diffusers import Flux2KleinPipeline
        self.pipe = Flux2KleinPipeline.from_pretrained(
            config.flux2_model, torch_dtype=torch.bfloat16
        ).to("cuda")
        self.steps = config.steps
        self.ref_count = config.ref_count
        self.references_dir = config.references_dir
        self._packs = {}

    def _pack(self, shot):
        import glob
        import os
        from PIL import Image
        shot = "closeup" if str(shot).startswith("close") else "full"
        if shot not in self._packs:
            folder = os.path.join(self.references_dir, shot)
            paths = sorted(glob.glob(os.path.join(folder, "*.png")))[: self.ref_count]
            self._packs[shot] = [Image.open(p).convert("RGB") for p in paths]
        return self._packs[shot]

    def generate(self, prompt, shot, seed, width, height):
        import torch
        refs = self._pack(shot)
        return self.pipe(
            image=refs,
            prompt=prompt,
            width=width,
            height=height,
            num_inference_steps=self.steps,
            generator=torch.Generator("cuda").manual_seed(int(seed)),
        ).images[0]
