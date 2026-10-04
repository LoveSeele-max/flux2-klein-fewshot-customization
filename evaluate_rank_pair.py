import argparse
from pathlib import Path


PROMPTS = {
    "short": "a photo of zqv figurine",
    "D2": (
        "a photo of a zqv figurine on a wooden table, a small collectible toy "
        "with spiky black hair, two tall tan rabbit-like ears rising from the top "
        "of the head behind the black hair, with distinct dark inner ear panels, "
        "separate from the small rounded ears on the sides of the face, "
        "natural light tan skin tone, large anime eyes, red jacket, blue shorts, "
        "sandals, and a round gold display base"
    ),
}
SEEDS = (42, 123, 456, 789)


def main():
    parser = argparse.ArgumentParser(description="Compare fresh rank4/rank16 runs at step 240.")
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    args = parser.parse_args()
    checkpoints = {
        f"rank{rank}": args.run_root / f"rank{rank}" / "checkpoint-240"
        for rank in (4, 16)
    }
    for checkpoint in checkpoints.values():
        weight = checkpoint / "pytorch_lora_weights.safetensors"
        if not weight.is_file():
            raise FileNotFoundError(weight)
    output = args.run_root / "comparison"
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite: {output}")

    import torch
    from diffusers import Flux2KleinPipeline

    pipe = Flux2KleinPipeline.from_pretrained(
        args.model_dir, dtype=torch.bfloat16, local_files_only=True
    )
    if pipe.config.is_distilled:
        raise ValueError("Expected the non-distilled base model")
    pipe.enable_model_cpu_offload()
    output.mkdir(parents=True)
    for group in ("base", "rank4", "rank16"):
        if group != "base":
            pipe.load_lora_weights(
                str(checkpoints[group]),
                weight_name="pytorch_lora_weights.safetensors",
                adapter_name="figurine",
            )
            pipe.set_adapters("figurine", adapter_weights=0.75)
        try:
            for name, prompt in PROMPTS.items():
                for seed in SEEDS:
                    image = pipe(
                        prompt=prompt, height=512, width=512,
                        num_inference_steps=50, guidance_scale=4.0,
                        generator=torch.Generator(device="cpu").manual_seed(seed),
                    ).images[0]
                    path = output / f"{group}_{name}_seed{seed}.png"
                    image.save(path)
                    print(f"Saved: {path}", flush=True)
        finally:
            if group != "base":
                pipe.unload_lora_weights()
    print(f"Finished: 24 images in {output}", flush=True)


if __name__ == "__main__":
    main()
