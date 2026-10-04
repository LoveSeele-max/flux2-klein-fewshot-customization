from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "refer"
OUTPUT = ROOT / "refer_cropped_v1"

# Pixel boxes on the EXIF-oriented 3072x4096 source images.
CROP_BOXES = {
    "IMG_20261001_164226.jpg": (400, 250, 2600, 3650),
    "IMG_20261001_164231.jpg": (450, 180, 2700, 3800),
    "IMG_20261001_164239.jpg": (500, 120, 2550, 3550),
    "IMG_20261001_164242.jpg": (700, 600, 2700, 3650),
    "IMG_20261001_164247.jpg": (700, 450, 2650, 3700),
    "IMG_20261001_164251.jpg": (450, 300, 2600, 3700),
    "IMG_20261001_164302.jpg": (350, 100, 2750, 3900),
    "IMG_20261001_164313.jpg": (400, 80, 2700, 3900),
}


def main():
    missing = [name for name in CROP_BOXES if not (SOURCE / name).is_file()]
    if missing:
        raise SystemExit(f"Missing reference photos: {missing}")
    if OUTPUT.exists():
        raise SystemExit(f"Refusing to overwrite existing crops: {OUTPUT}")

    OUTPUT.mkdir()
    for name, box in CROP_BOXES.items():
        with Image.open(SOURCE / name) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
        if not (0 <= box[0] < box[2] <= image.width and
                0 <= box[1] < box[3] <= image.height):
            raise ValueError(f"Crop box outside image: {name}, {box}, {image.size}")
        image.crop(box).save(OUTPUT / name, quality=95, subsampling=0)
        print(f"{name}: {image.size} -> {box}")


if __name__ == "__main__":
    main()
