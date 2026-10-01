import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "train"
OUTPUT = ROOT / "crop_diagnostic_v1"
ASPECT_RATIOS = (
    (1, 1), (4, 5), (5, 4), (2, 3), (3, 2), (3, 4),
    (4, 3), (9, 16), (16, 9), (1, 2), (2, 1),
)
CROP_BOXES = {
    "IMG_20260930_000747.jpg": (0.23, 0.17, 0.69, 0.85),
    "IMG_20260930_000753.jpg": (0.30, 0.13, 0.80, 0.80),
    "IMG_20260930_000757.jpg": (0.32, 0.29, 0.82, 0.87),
    "IMG_20260930_000809.jpg": (0.32, 0.30, 0.82, 0.82),
    "IMG_20260930_000821.jpg": (0.27, 0.08, 0.82, 0.80),
    "IMG_20260930_000824.jpg": (0.28, 0.14, 0.83, 0.84),
    "IMG_20260930_000830.jpg": (0.28, 0.24, 0.83, 0.90),
    "IMG_20260930_000836.jpg": (0.35, 0.35, 0.90, 0.92),
    "IMG_20260930_000843.jpg": (0.18, 0.20, 0.80, 0.88),
    "IMG_20260930_000850.jpg": (0.22, 0.12, 0.80, 0.85),
    "IMG_20260930_000901.jpg": (0.21, 0.20, 0.83, 0.88),
    "IMG_20260930_000905.jpg": (0.24, 0.30, 0.86, 0.92),
    "IMG_20260930_000926.jpg": (0.14, 0.12, 0.74, 0.85),
    "IMG_20260930_000937.jpg": (0.24, 0.11, 0.88, 0.90),
    "IMG_20260930_000942.jpg": (0.18, 0.14, 0.83, 0.90),
    "IMG_20260930_000947.jpg": (0.15, 0.16, 0.84, 0.91),
}


def bucket_for_image(image):
    width, height = image.size
    resolution = min(512, round((height * width) ** 0.5))
    buckets = []
    for ratio_width, ratio_height in ASPECT_RATIOS:
        aspect = ratio_width / ratio_height
        bucket_height = (resolution ** 2 / aspect) ** 0.5
        bucket_width = bucket_height * aspect
        bucket = (
            max(16, round(bucket_height / 16) * 16),
            max(16, round(bucket_width / 16) * 16),
        )
        if bucket not in buckets:
            buckets.append(bucket)
    selected = None
    smallest_distance = float("inf")
    for bucket_height, bucket_width in buckets:
        distance = abs(height * bucket_width - width * bucket_height)
        if distance <= smallest_distance:
            smallest_distance = distance
            selected = (bucket_height, bucket_width)
    return selected


def preview_at_training_size(image):
    target_height, target_width = bucket_for_image(image)
    scale = max(target_height / image.height, target_width / image.width)
    resized = image.resize(
        (round(image.width * scale), round(image.height * scale)),
        Image.Resampling.BILINEAR,
    )
    left = (resized.width - target_width) // 2
    top = (resized.height - target_height) // 2
    return resized.crop((left, top, left + target_width, top + target_height))


def make_sheet(records, page):
    sheet = Image.new("RGB", (1400, 1820), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 8), "LEFT: original preview / RIGHT: candidate crop preview", fill="black")
    draw.text((12, 26), "512 pixel budget; representative CENTER crop, not server RandomCrop", fill="black")
    for index, record in enumerate(records):
        left = (index % 2) * 700
        top = (index // 2) * 440 + 52
        for offset, folder in ((0, "original_preview_512"), (350, "crop_preview_512")):
            path = OUTPUT / folder / f"{Path(record['filename']).stem}.png"
            with Image.open(path) as source:
                thumbnail = ImageOps.contain(source, (340, 392))
                sheet.paste(thumbnail, (left + offset + (350 - thumbnail.width) // 2, top))
        draw.text((left + 8, top + 397), record["filename"], fill="black")
    sheet.save(OUTPUT / f"comparison_page{page}.jpg", quality=94)


def main():
    if OUTPUT.exists() and "--refresh" not in sys.argv:
        raise SystemExit(f"Refusing to overwrite existing output: {OUTPUT}")
    missing = [name for name in CROP_BOXES if not (SOURCE / name).is_file()]
    if missing:
        raise SystemExit(f"Missing source files: {missing}")
    for folder in ("train_cropped_candidate", "original_preview_512", "crop_preview_512"):
        (OUTPUT / folder).mkdir(parents=True, exist_ok=True)

    records = []
    for filename, fractions in CROP_BOXES.items():
        with Image.open(SOURCE / filename) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
        crop_box = tuple(
            round(fraction * dimension)
            for fraction, dimension in zip(
                fractions, (image.width, image.height, image.width, image.height)
            )
        )
        cropped = image.crop(crop_box)
        cropped.save(OUTPUT / "train_cropped_candidate" / filename, quality=95, subsampling=0)
        original_preview = preview_at_training_size(image)
        cropped_preview = preview_at_training_size(cropped)
        original_preview.save(OUTPUT / "original_preview_512" / f"{Path(filename).stem}.png")
        cropped_preview.save(OUTPUT / "crop_preview_512" / f"{Path(filename).stem}.png")
        records.append({
            "filename": filename,
            "original_size": list(image.size),
            "crop_box_pixels": list(crop_box),
            "cropped_size": list(cropped.size),
            "original_preview_size": list(original_preview.size),
            "cropped_preview_size": list(cropped_preview.size),
        })

    manifest = {
        "resolution": 512,
        "bucket_divisibility": 16,
        "preview_crop": "center; representative geometry, not actual server random crop",
        "candidate_status": "visually review all ears, hands, feet and bases before training",
        "records": records,
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    make_sheet(records[:8], 1)
    make_sheet(records[8:], 2)
    print(f"Prepared {len(records)} candidates in {OUTPUT}")
    print(f"Original preview size: {records[0]['original_preview_size']}")


if __name__ == "__main__":
    main()
