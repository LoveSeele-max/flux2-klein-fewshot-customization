# 基于 FLUX.2 Klein 的少样本主体定制生成系统

本项目研究使用 FLUX.2 Klein 4B 基础模型和 LoRA，对少量主体图片进行定制化生成，并通过固定提示词、随机种子、checkpoint、LoRA 强度和场景设置进行对比评估。

## 当前状态

- 已完成：非蒸馏版 FLUX.2 Klein 本地加载、LoRA 训练、checkpoint 对比和多场景验证。
- 已完成：训练图片主体裁切与训练前预览检查流程。
- 已完成：训练、推理脚本中的服务器绝对路径参数化。
- 进行中：统一的 base/LoRA 归因消融、数据量实验、rank 容量实验和正式盲评。
- 不公开：基础模型权重、LoRA 权重、原始主体图片和完整生成结果。

历史探索结果不能替代最终统一评估；README 中只把已经实际验证的内容标记为已完成。

## 项目结构

```text
.
├── README.md
├── requirements.txt
├── .gitignore
├── configs/
│   └── environment.example
├── scripts/
├── data_manifests/
├── evaluation/
├── reports/
└── docs/
```

当前仓库根目录中的脚本是实验原型。后续稳定后，可以再迁移到 `scripts/` 和 `src/`。

## 环境准备

项目在 Linux + NVIDIA GPU 环境中开发。基础模型需要用户自行准备，并通过环境变量指定路径。

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

PyTorch 的 CUDA 安装应按照服务器 CUDA、驱动版本和官方安装命令单独完成，不建议仅依赖通用的 `requirements.txt`。

```bash
export MODEL_DIR=/path/to/FLUX.2-klein-base-4B
export DIFFUSERS_DIR=/path/to/diffusers
export HF_HUB_CACHE=/path/to/huggingface/cache
```

## 训练

训练脚本要求显式传入本地路径，避免依赖作者个人目录：

```bash
MODEL_DIR=/path/to/FLUX.2-klein-base-4B \
DATA_DIR=/path/to/train_cropped_candidate \
OUTPUT_DIR=/path/to/runs/figurine_lora \
DIFFUSERS_DIR=/path/to/diffusers \
HF_HUB_CACHE=/path/to/huggingface/cache \
GPU_ID=0 \
bash train_cropped_v1.sh
```

脚本会拒绝覆盖已有输出目录。训练前应确认数据划分、触发词、训练步数和 rank 已记录到实验配置中。

## 推理与验证

比较多个 checkpoint：

```bash
python compare_cropped_v1.py \
  --model-dir "$MODEL_DIR" \
  --run-dir /path/to/runs/figurine_lora \
  --output-dir /path/to/results/comparison \
  --steps 80 160 240 320 \
  --seeds 42 123
```

验证指定 checkpoint：

```bash
python validate_step240.py \
  --model-dir "$MODEL_DIR" \
  --checkpoint /path/to/runs/figurine_lora/checkpoint-240 \
  --output-dir /path/to/results/validate_step240
```

跨场景验证：

```bash
python validate_scenes_step240.py \
  --model-dir "$MODEL_DIR" \
  --checkpoint /path/to/runs/figurine_lora/checkpoint-240 \
  --output-dir /path/to/results/scene_validation
```

## 评估原则

正式结论应至少记录：

- base 与 LoRA 的同提示词对照；
- 触发词提示词与详细外观提示词的差异；
- checkpoint 和 LoRA scale；
- 随机种子、分辨率、推理步数和 guidance scale；
- 主体一致性、结构完整性、提示词遵循、画面质量和伪影；
- 数据量、训练步数和 rank 消融；
- 评估集是否参与训练或选参。

详细评估协议见 `evaluation/` 和 `docs/`。

## 许可证与第三方组件

仓库不包含 FLUX.2 Klein 权重，也不自动授予基础模型、训练图片或第三方代码的分发权。训练脚本保留其原有的 Hugging Face Apache-2.0 版权和许可证声明；使用前请同时遵守模型和依赖项目的许可证。
