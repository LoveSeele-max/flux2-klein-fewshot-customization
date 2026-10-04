# 基于 FLUX.2 Klein 的少样本主体定制生成系统

本项目研究使用 FLUX.2 Klein 4B 基础模型和 LoRA，对少量主体图片进行定制化生成，并通过固定提示词、随机种子、checkpoint、LoRA 强度和场景设置进行对比评估。

## 当前状态

- 2026-10-04 已收尾：训练与推理流程跑通，但当前配置未实现稳定的主体身份复现，停止追加实验。
- 收尾总结、尝试记录、失败分析和后续展望见 [项目收尾总结](reports/project_retrospective.md)。
- 已完成：非蒸馏版 FLUX.2 Klein 本地加载、LoRA 训练、checkpoint 对比和多场景验证。
- 已完成：训练图片主体裁切与训练前预览检查流程。
- 已完成：训练、推理脚本中的服务器绝对路径参数化。
- 已执行：base/LoRA 与提示词对照、新 rank4/16 对照和强度诊断；不代表完整任务书验收。
- 未完成：4/8/16 数据量训练对照、rank32、可靠独立盲评与最终保留场景测试。
- 不公开：基础模型权重、LoRA 权重、原始主体图片和完整生成结果。

历史场景验证属于探索性运行，不等于主体身份或跨场景泛化已经通过验收。早期“可用 LoRA”的推荐由收尾总结中的限定结论替代；历史记录保留，不回写当时判断。

## 项目结构

```text
.
├── README.md
├── requirements.txt
├── .gitignore
├── configs/
│   └── environment.example
├── data_manifests/
├── evaluation/
├── reports/
└── docs/
```

当前仓库根目录中的脚本是实验原型。项目已收尾，不再为目录重构追加工作。

## 留作纪念

这是一份练手项目的记录，不是成功的主体定制产品，也不作为算法创新或稳定身份复现的证明。

保留下来的，是从拍摄数据、训练、推理到对照诊断的实践，以及对失败的诚实复盘。公开仓库只保存代码、规则和脱敏总结，不包含私人照片、权重、完整生成图片或原始日志。

失败并不可怕，愿不忘初心，砥砺前行。

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

## 后续诊断脚本

新 rank4/16 对照使用各自从底模训练的 240 步权重，并保持 alpha/rank 比例为 1：

```bash
MODEL_DIR=/path/to/FLUX.2-klein-base-4B \
DATA_DIR=/path/to/16-cropped-images \
DIFFUSERS_DIR=/path/to/diffusers \
RUN_ROOT=/path/to/new-rank-pair-run \
GPU_ID=0 \
bash train_rank_pair.sh
```

对已有 rank 对照进行强度检查，不重新训练：

```bash
python evaluate_rank_strength.py \
  --model-dir /path/to/FLUX.2-klein-base-4B \
  --run-root /path/to/existing-rank-pair-run
```

该脚本要求运行目录中已有 `rank4/checkpoint-240`、`rank16/checkpoint-240` 和 `comparison` 中的短提示词图片。它生成 8 张 scale1.0 图片及对照拼图，拒绝覆盖已有输出。

公开入口已去掉个人路径。本次只检查参数入口与语法，未在新机器重新执行完整训练或推理。4/8/16 子集名单仅表示完成了数据准备，不表示数据量实验已经运行。

## 许可证与第三方组件

仓库不包含 FLUX.2 Klein 权重，也不自动授予基础模型、训练图片或第三方代码的分发权。训练脚本保留其原有的 Hugging Face Apache-2.0 版权和许可证声明；使用前请同时遵守模型和依赖项目的许可证。
