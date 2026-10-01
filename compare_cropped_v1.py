import argparse
from pathlib import Path

import torch
from diffusers import Flux2KleinPipeline


def generate(pipe, output_dir, label, seeds):
    for seed in seeds:
        image = pipe(
            prompt="a photo of zqv figurine on a wooden table",
            height=512,
            width=512,
            num_inference_steps=50,
            guidance_scale=4.0,
            generator=torch.Generator(device="cpu").manual_seed(seed),
        ).images[0]
        output_path = output_dir / f"{label}_seed{seed}.png"
        image.save(output_path)
        print(f"Saved: {output_path}", flush=True)


def parse_args():
    parser = argparse.ArgumentParser(description="Compare FLUX.2 Klein base and LoRA checkpoints.")
    parser.add_argument("--model-dir", required=True, type=Path)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--steps", nargs="+", type=int, default=(80, 160, 240, 320))
    parser.add_argument("--seeds", nargs="+", type=int, default=(42, 123))
    return parser.parse_args()


def main():
    args = parse_args()
    run_dir = args.run_dir
    output_dir = args.output_dir or run_dir / "comparison"
    steps = tuple(args.steps)
    seeds = tuple(args.seeds)
    for step in steps:
        weights = run_dir / f"checkpoint-{step}" / "pytorch_lora_weights.safetensors"
        if not weights.is_file():
            raise FileNotFoundError(f"Missing checkpoint: {weights}")
    if output_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing comparison: {output_dir}")
    output_dir.mkdir(parents=True)
    pipe = Flux2KleinPipeline.from_pretrained(
        args.model_dir,
        dtype=torch.bfloat16,
        local_files_only=True,
    )
    if pipe.config.is_distilled:
        raise ValueError("Expected the non-distilled base pipeline")
    pipe.enable_model_cpu_offload()
    generate(pipe, output_dir, "base", seeds)
    for step in steps:
        pipe.load_lora_weights(
            str(run_dir / f"checkpoint-{step}"),
            weight_name="pytorch_lora_weights.safetensors",
        )
        try:
            generate(pipe, output_dir, f"lora_step{step}", seeds)
        finally:
            pipe.unload_lora_weights()
    print("Finished: 10 comparison images.", flush=True)


if __name__ == "__main__":
    main()
