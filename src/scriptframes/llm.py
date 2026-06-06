import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


class QwenLLM:
    def __init__(self, model_path: str):
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path, torch_dtype="auto", device_map="auto"
        )

    def generate(self, system: str, user: str, max_new_tokens: int = 4096) -> str:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        text = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
        generated = self.model.generate(
            **inputs, max_new_tokens=max_new_tokens, do_sample=False
        )
        new_tokens = generated[0][inputs.input_ids.shape[1]:]
        return self.tokenizer.decode(new_tokens, skip_special_tokens=True)
