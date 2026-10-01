#!/usr/bin/env bash
set -euo pipefail

MODEL_DIR=${MODEL_DIR:?Set MODEL_DIR to the local FLUX.2 Klein base directory}
DATA_DIR=${DATA_DIR:?Set DATA_DIR to the cropped training-image directory}
OUTPUT_DIR=${OUTPUT_DIR:?Set OUTPUT_DIR to a new run directory}
DIFFUSERS_DIR=${DIFFUSERS_DIR:?Set DIFFUSERS_DIR to the diffusers source checkout}
LOG_FILE=${LOG_FILE:-"$OUTPUT_DIR/train.log"}
GPU_ID=${GPU_ID:-0}

if [[ ! -f "$MODEL_DIR/model_index.json" || ! -d "$DATA_DIR" ]]; then
  printf 'Missing model config or candidate dataset: %s\n' "$DATA_DIR" >&2
  exit 1
fi
if [[ -e "$OUTPUT_DIR" ]]; then
  printf 'Output already exists; refusing to overwrite: %s\n' "$OUTPUT_DIR" >&2
  exit 1
fi

cd "$DIFFUSERS_DIR"
export CUDA_VISIBLE_DEVICES="$GPU_ID"
export HF_HUB_OFFLINE=1
export HF_HUB_CACHE="${HF_HUB_CACHE:?Set HF_HUB_CACHE to the local Hugging Face cache}"

accelerate launch \
  --num_processes=1 \
  --num_machines=1 \
  --dynamo_backend=no \
  --mixed_precision=bf16 \
  examples/dreambooth/train_dreambooth_lora_flux2_klein.py \
  --pretrained_model_name_or_path="$MODEL_DIR" \
  --instance_data_dir="$DATA_DIR" \
  --instance_prompt="a photo of zqv figurine" \
  --output_dir="$OUTPUT_DIR" \
  --resolution=512 \
  --use_aspect_ratio_buckets \
  --train_batch_size=1 \
  --gradient_accumulation_steps=1 \
  --max_train_steps=320 \
  --checkpointing_steps=80 \
  --learning_rate=1e-4 \
  --lr_scheduler=constant \
  --rank=4 \
  --lora_alpha=4 \
  --guidance_scale=1 \
  --gradient_checkpointing \
  --cache_latents \
  --offload \
  --skip_final_inference \
  --seed=0 \
  2>&1 | tee "$LOG_FILE"
