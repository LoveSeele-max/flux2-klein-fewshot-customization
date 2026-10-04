#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
MODEL_DIR=${MODEL_DIR:?Set MODEL_DIR to the local FLUX.2 Klein base directory}
DATA_DIR=${DATA_DIR:?Set DATA_DIR to the 16 cropped training-image directory}
DIFFUSERS_DIR=${DIFFUSERS_DIR:?Set DIFFUSERS_DIR to the diffusers source checkout}
TRAIN_SCRIPT="$DIFFUSERS_DIR/examples/dreambooth/train_dreambooth_lora_flux2_klein.py"
RUN_ROOT=${RUN_ROOT:?Set RUN_ROOT to a new rank-pair output directory}
export CUDA_VISIBLE_DEVICES=${GPU_ID:-0}
export HF_HUB_OFFLINE=1
export PYTHONUNBUFFERED=1

for file in "$MODEL_DIR/model_index.json" "$TRAIN_SCRIPT" "$SCRIPT_DIR/evaluate_rank_pair.py"; do
  [[ -f "$file" ]] || { printf 'Missing file: %s\n' "$file" >&2; exit 1; }
done
[[ -d "$DATA_DIR" ]] || { printf 'Missing data: %s\n' "$DATA_DIR" >&2; exit 1; }
[[ ! -e "$RUN_ROOT" ]] || { printf 'Refusing to overwrite: %s\n' "$RUN_ROOT" >&2; exit 1; }
python - "$DATA_DIR" <<'PY'
import sys
from pathlib import Path
from PIL import Image
files = list(Path(sys.argv[1]).iterdir())
if len(files) != 16 or any(not p.is_file() for p in files):
    raise SystemExit("Expected exactly 16 image files in the training directory")
for path in files:
    with Image.open(path) as image:
        image.verify()
print("Checked: 16 readable training images")
PY

mkdir -p "$RUN_ROOT"
printf '%s\n' "$RUN_ROOT"
sha256sum "$TRAIN_SCRIPT" > "$RUN_ROOT/training_script.sha256"
python -m pip freeze > "$RUN_ROOT/environment.txt"
cd "$DIFFUSERS_DIR"
for rank in 4 16; do
  output="$RUN_ROOT/rank$rank"
  accelerate launch --num_processes=1 --num_machines=1 \
    --dynamo_backend=no --mixed_precision=bf16 "$TRAIN_SCRIPT" \
    --pretrained_model_name_or_path="$MODEL_DIR" \
    --instance_data_dir="$DATA_DIR" \
    --instance_prompt="a photo of zqv figurine" \
    --output_dir="$output" --resolution=512 --use_aspect_ratio_buckets \
    --train_batch_size=1 --gradient_accumulation_steps=1 \
    --max_train_steps=240 --checkpointing_steps=80 \
    --learning_rate=1e-4 --lr_scheduler=constant \
    --rank="$rank" --lora_alpha="$rank" --guidance_scale=1 \
    --gradient_checkpointing --cache_latents --offload \
    --skip_final_inference --seed=0 \
    2>&1 | tee "$RUN_ROOT/rank${rank}_train.log"
done

python "$SCRIPT_DIR/evaluate_rank_pair.py" \
  --model-dir "$MODEL_DIR" --run-root "$RUN_ROOT"
printf '\nFinished. Results: %s/comparison\n' "$RUN_ROOT"
