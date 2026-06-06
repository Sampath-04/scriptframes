from pathlib import Path
from .prompt_template import finalize_prompt, DEFAULT_NEGATIVE
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
            prompt = finalize_prompt(
                e["image_prompt"], config.trigger_word, config.style_suffix
            )
            negative = e.get("negative_prompt") or DEFAULT_NEGATIVE
            image = generator.generate(
                prompt, negative, e["seed"], config.width, config.height
            )
            image.save(images_dir / Path(e["output_file"]).name)
            M.mark_done(manifest, e["id"])
        except Exception as ex:  # continue-on-error
            M.mark_failed(manifest, e["id"], ex)
        M.save_manifest(manifest_path, manifest)
    return manifest


class FluxGenerator:
    """FLUX.1-dev + character LoRA via diffusers.

    GPU imports live inside the methods so `import scriptframes.generate` stays
    importable without torch (keeps non-GPU tooling/tests light).
    Note: FLUX.1-dev is guidance-distilled and ignores a negative prompt; it is
    accepted for a uniform interface but not passed to the pipeline.
    """

    def __init__(self, config):
        import torch
        from diffusers import FluxPipeline
        self.pipe = FluxPipeline.from_pretrained(
            config.flux_model, torch_dtype=torch.bfloat16
        ).to("cuda")
        if config.lora_path:
            self.pipe.load_lora_weights(config.lora_path)
        self.steps = config.steps
        self.guidance = config.guidance
        self.lora_scale = config.lora_scale

    def generate(self, prompt, negative, seed, width, height):
        import torch
        generator = torch.Generator("cuda").manual_seed(int(seed))
        result = self.pipe(
            prompt=prompt,
            width=width,
            height=height,
            num_inference_steps=self.steps,
            guidance_scale=self.guidance,
            generator=generator,
            joint_attention_kwargs={"scale": self.lora_scale},
        )
        return result.images[0]
