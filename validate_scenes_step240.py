import argparse
from pathlib import Path

import torch
from diffusers import Flux2KleinPipeline


BASE_DESCRIPTION = (
    "zqv figurine, a small collectible toy with spiky black hair, "
    "two long upright tan ears, yellow face, large anime eyes, "
    "red jacket, blue shorts, sandals, and a round gold display base"
)

SCENES = {
    "bookshelf": f"a photo of {BASE_DESCRIPTION} on a bookshelf, warm indoor lighting",
    "studio": f"a professional studio product photo of {BASE_DESCRIPTION} on a white background",
    "dramatic": f"a photo of {BASE_DESCRIPTION} on a wooden table, dramatic side lighting",
}

SCALES = (0.75, 1.0)
SEEDS = (42, 123, 456, 789)


def generate(pipe, output_dir, label):
    for scene_name, prompt in SCENES.items():
        for seed in SEEDS:
            image = pipe(
                prompt=prompt,
                height=512,
                width=512,
                num_inference_steps=50,
                guidance_scale=4.0,
                generator=torch.Generator(device="cpu").manual_seed(seed),
            ).images[0]
            output_path = output_dir / f"{scene_name}_{label}_seed{seed}.png"
            image.save(output_path)
            print(f"Saved: {output_path}", flush=True)


def parse_args():
    parser = argparse.ArgumentParser(description="Validate a LoRA across multiple scenes.")
    parser.add_argument("--model-dir", required=True, type=Path)
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args()


def main():
    args = parse_args()
    weight_file = args.checkpoint / "pytorch_lora_weights.safetensors"
    if not weight_file.is_file():
        raise FileNotFoundError(weight_file)
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
    generate(pipe, args.output_dir, "base")
    pipe.load_lora_weights(
        str(args.checkpoint),
        weight_name="pytorch_lora_weights.safetensors",
        adapter_name="figurine",
    )

    for scale in SCALES:
        pipe.set_adapters("figurine", adapter_weights=scale)
        scale_name = str(scale).replace(".", "")
        generate(pipe, args.output_dir, f"scale{scale_name}")

    print("Scene validation complete: 36 images, including 12 base controls.", flush=True)


if __name__ == "__main__":
    main()
