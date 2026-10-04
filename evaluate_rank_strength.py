import argparse
from pathlib import Path


SEEDS = (42, 123, 456, 789)
PROMPT = "a photo of zqv figurine"


def make_sheet(run_root, output):
    from PIL import Image, ImageDraw

    cell_width, cell_height = 384, 414
    sheet = Image.new("RGB", (cell_width * 4, cell_height * 4), "white")
    draw = ImageDraw.Draw(sheet)
    for row, (rank, scale) in enumerate(
        ((4, "0.75"), (4, "1.0"), (16, "0.75"), (16, "1.0"))
    ):
        folder = run_root / "comparison" if scale == "0.75" else output
        for col, seed in enumerate(SEEDS):
            path = folder / f"rank{rank}_short_seed{seed}.png"
            with Image.open(path) as source:
                image = source.convert("RGB")
                image.thumbnail((384, 384))
                x = col * cell_width + (cell_width - image.width) // 2
                y = row * cell_height + 30 + (384 - image.height) // 2
                sheet.paste(image, (x, y))
            draw.text(
                (col * cell_width + 8, row * cell_height + 8),
                f"rank{rank} / scale {scale} / seed {seed}",
                fill="black",
            )
    sheet.save(output / "strength_comparison.jpg", quality=95)


def main():
    parser = argparse.ArgumentParser(
        description="Check existing step-240 LoRAs at strength 1.0 without retraining."
    )
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    args = parser.parse_args()
    output = args.run_root / "strength_1p0"
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite: {output}")
    for rank in (4, 16):
        checkpoint = args.run_root / f"rank{rank}" / "checkpoint-240"
        weight = checkpoint / "pytorch_lora_weights.safetensors"
        if not weight.is_file():
            raise FileNotFoundError(weight)
        for seed in SEEDS:
            image = args.run_root / "comparison" / f"rank{rank}_short_seed{seed}.png"
            if not image.is_file():
                raise FileNotFoundError(image)

    import torch
    from diffusers import Flux2KleinPipeline

    pipe = Flux2KleinPipeline.from_pretrained(
        args.model_dir, dtype=torch.bfloat16, local_files_only=True
    )
    if pipe.config.is_distilled:
        raise ValueError("Expected the non-distilled base model")
    pipe.enable_model_cpu_offload()
    output.mkdir(parents=True)
    for rank in (4, 16):
        pipe.load_lora_weights(
            str(args.run_root / f"rank{rank}" / "checkpoint-240"),
            weight_name="pytorch_lora_weights.safetensors",
            adapter_name="figurine",
        )
        try:
            pipe.set_adapters("figurine", adapter_weights=1.0)
            for seed in SEEDS:
                image = pipe(
                    prompt=PROMPT, height=512, width=512,
                    num_inference_steps=50, guidance_scale=4.0,
                    generator=torch.Generator(device="cpu").manual_seed(seed),
                ).images[0]
                path = output / f"rank{rank}_short_seed{seed}.png"
                image.save(path)
                print(f"Saved: {path}", flush=True)
        finally:
            pipe.unload_lora_weights()
    make_sheet(args.run_root, output)
    print(f"Finished: 8 new images and comparison sheet in {output}", flush=True)


if __name__ == "__main__":
    main()
