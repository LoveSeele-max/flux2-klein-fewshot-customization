# 仓库提交说明

## 本机与服务器

训练在 SSH 登录的 Linux 服务器上执行，本机 Windows 不需要下载基础模型。Git 仓库可以在服务器或本机管理，但两边是不同的文件系统。

推荐先在本机提交公开代码和文档，服务器只保存模型、私有图片、LoRA 权重和实验结果。

## 本机允许提交

```text
README.md
.gitignore
requirements.txt
configs/
data_manifests/README.md
evaluation/
docs/
训练脚本和推理脚本
```

## 服务器不应提交的内容

```text
基础模型目录
LoRA checkpoint
训练图片和 holdout
生成图片目录
训练日志
Hugging Face 缓存
.venv
SSH 密钥、令牌和密码
服务器绝对路径
```

## 服务器后续需要补充

在 Linux 服务器上确认以下内容后，再决定是否迁移到仓库：

1. 经过脱敏的训练脚本和推理脚本；
2. 实际运行过的配置文件；
3. 不包含原图的 train/holdout manifest；
4. 评估协议和评分模板；
5. 去除隐私后的实验汇总表；
6. 少量允许公开的精选结果图。

模型权重、原始数据和完整结果始终保留在服务器，不通过 Git 提交。

## 提交前检查

```bash
git status
git diff --cached --name-status
git diff --cached --stat
git diff --cached --check
```

确认没有权重、图片、密钥和个人路径后，再执行：

```bash
git commit -m "chore: initialize project structure"
```

本地提交和 GitHub 推送是两个动作。只有在用户确认远程内容无误后，才执行：

```bash
git push -u origin main
```
