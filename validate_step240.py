import argparse
from pathlib import Path

import torch
from diffusers import Flux2KleinPipeline


PROMPTS = {
    "short": "a front-facing product photo of zqv figurine, full body, standing on a round gold display base",
    "detailed": (
        "a front-facing product photo of zqv figurine, a small collectible toy "
        "with spiky black hair, two long upright tan ears, yellow face, "
        "large anime eyes, red jacket, blue shorts, sandals, and a round gold display base"
    ),
}

SCALES = (0.75, 1.0)
SEEDS = (42, 123, 456, 789)


def parse_args():
    parser = argparse.ArgumentParser(description="Validate a FLUX.2 Klein LoRA checkpoint.")
    parser.add_argument("--model-dir", required=True, type=Path)
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args()


def main():
    args = parse_args()
    weights = args.checkpoint / "pytorch_lora_weights.safetensors"
    if not weights.is_file():
        raise FileNotFoundError(weights)
    if args.output_dir.exists():
        raise FileExistsError(f"Refusing to overwrite: {args.output_dir}")
    args.output_dir.mkdir(parents=True)

    pipe = Flux2KleinPipeline.from_pretrained(
        args.model_dir,
        dtype=torch.bfloat16,
        local_files_only=True,
    )
    if pipe.config.is_distilled:
        raise ValueError("Expected the non-distilled base pipeline")
    pipe.enable_model_cpu_offload()

    pipe.load_lora_weights(
        str(args.checkpoint),
        weight_name="pytorch_lora_weights.safetensors",
        adapter_name="figurine",
    )

    for prompt_name, prompt in PROMPTS.items():
        for scale in SCALES:
            pipe.set_adapters("figurine", adapter_weights=scale)
            scale_name = str(scale).replace(".", "")
            for seed in SEEDS:
                image = pipe(
                    prompt=prompt,
                    height=512,
                    width=512,
                    num_inference_steps=50,
                    guidance_scale=4.0,
                    generator=torch.Generator(device="cpu").manual_seed(seed),
                ).images[0]
                output_path = args.output_dir / (
                    f"step240_{prompt_name}_scale{scale_name}_seed{seed}.png"
                )
                image.save(output_path)
                print(f"Saved: {output_path}", flush=True)

    print("Validation complete: 16 images.", flush=True)


if __name__ == "__main__":
    main()
