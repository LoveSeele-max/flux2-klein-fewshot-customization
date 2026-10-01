# 项目开发与 Git 提交流程规范

## 1. 总原则

本项目使用以下分工：

- Linux 服务器：运行训练、推理和评估，保存模型、数据和实验产物；
- GitHub：保存公开代码、配置、协议、脱敏记录和少量允许公开的结果；
- Windows 本机：审查代码、整理文档、检查提交内容，也可以运行不依赖 GPU 的检查。

GitHub 仓库不是模型存储盘，也不是训练输出备份盘。任何文件在提交前都必须回答：

1. 是否能够公开；
2. 是否对复现或理解项目有价值；
3. 是否不包含个人路径、隐私和密钥；
4. 是否已经经过相应检查。

---

## 2. 服务器代码是否可以直接提交

可以提交服务器上的代码，但**不能未经检查直接执行 `git add .` 和提交**。

服务器上的代码通常是项目实际运行版本，适合作为代码来源；但服务器目录中还混有：

- 基础模型；
- LoRA 权重；
- 原始图片；
- holdout 图片；
- 生成图；
- 训练日志；
- Hugging Face 缓存；
- 个人绝对路径；
- 临时脚本和调试文件。

正确做法是：

1. 从服务器代码中挑选可公开文件；
2. 删除或参数化个人路径；
3. 用 `.gitignore` 排除模型、数据和结果；
4. 查看暂存区内容；
5. 做最小语法或运行检查；
6. 再进行提交。

服务器上的训练输出不应通过 Git 提交。需要记录时，提交配置、指标、摘要和 manifest，而不是提交权重和完整图片。

---

## 3. 分支规范

### 3.1 `main` 分支

`main` 只保存已经确认可用的稳定版本：

- README 能解释当前状态；
- 代码至少通过语法检查；
- 关键脚本已经在 Linux 服务器验证；
- 不包含私密文件和大文件；
- 提交记录可以被别人理解。

不要把正在调试、可能破坏现有流程的代码直接提交到 `main`。

### 3.2 实验或功能分支

每个相对独立的任务使用一个分支，例如：

```bash
git switch -c exp/rank-ablation
git switch -c exp/data-size-comparison
git switch -c feat/evaluation-protocol
git switch -c docs/update-readme
```

分支名建议使用：

```text
类型/简短主题
```

推荐类型：

- `feat/`：新增功能；
- `fix/`：修复问题；
- `exp/`：实验配置或实验流程；
- `docs/`：文档；
- `refactor/`：不改变行为的代码整理；
- `chore/`：依赖、目录和工程配置。

如果项目规模较小，也可以直接在 `main` 上提交，但仍然要保持每次提交逻辑单一。

---

## 4. 每完成一部分内容，什么时候提交

不要按“写了几行代码”提交，而要按“完成了一个可解释的逻辑单元”提交。

适合提交的节点：

### 4.1 代码功能完成

例如：

```text
将训练脚本中的服务器绝对路径改为命令行参数
增加 checkpoint 对比推理脚本
增加多场景验证脚本
```

### 4.2 实验协议完成

例如：

```text
固定 prompt、seed、分辨率和推理步数
增加 base/LoRA 归因消融配置
增加 4/8/16 张数据量实验配置
```

### 4.3 一轮实验完成

实验结果不应提交完整图片目录，而应提交：

```text
实验配置
运行命令
checkpoint
seed
LoRA scale
耗时和显存
评分结果
失败原因
结论
```

### 4.4 文档完成

例如：

```text
补充训练环境说明
补充评估协议
补充实验结论
补充复现命令
```

### 4.5 不适合单独提交的情况

以下内容不建议单独形成提交：

- 只改了一个无关紧要的空格；
- 只增加了一张未确认可公开的图片；
- 只上传训练日志；
- 只上传一次失败实验的临时输出；
- 同时混入代码、无关重命名和大批生成图片。

---

## 5. 推荐的提交粒度

一次提交尽量只表达一个主题。

推荐示例：

```text
chore: add repository ignore rules
feat: parameterize inference paths
feat: add checkpoint comparison script
exp: add fixed-seed scene validation
docs: document evaluation protocol
docs: record rank ablation results
fix: refuse to overwrite existing output
```

不推荐：

```text
update
fix
test
最终版
杂项修改
```

提交信息使用英文或中文都可以，但应说明“做了什么”，不要只写“改了”。

---

## 6. 服务器端标准操作流程

### 6.1 开始工作前

```bash
cd /path/to/flux2-klein-fewshot-customization
git switch main
git pull --ff-only origin main
git switch -c exp/your-topic
```

如果已有对应分支，使用：

```bash
git switch exp/your-topic
git pull --ff-only origin exp/your-topic
```

不要在服务器和本机同时修改同一个分支后互相覆盖。

### 6.2 完成代码或实验后

先查看状态：

```bash
git status --short
```

查看新增文件：

```bash
git status --short --untracked-files=all
```

检查大文件：

```bash
find . -type f -size +50M -print
```

检查敏感路径和凭据：

```bash
rg -n \
  '/home/|/root/|C:\\Users\\|HF_TOKEN|HUGGINGFACE_TOKEN|BEGIN OPENSSH|ghp_|github_pat_|hf_' \
  --glob '!*.png' \
  --glob '!*.jpg' \
  --glob '!*.jpeg' \
  --glob '!*.webp' \
  .
```

只添加明确允许提交的文件：

```bash
git add README.md
git add scripts/ configs/ docs/ evaluation/
```

不要默认使用：

```bash
git add .
```

### 6.3 检查暂存区

```bash
git diff --cached --name-status
git diff --cached --stat
git diff --cached --check
git diff --cached
```

重点确认：

- 没有模型权重；
- 没有原始图片；
- 没有生成图片目录；
- 没有 `.venv` 和缓存；
- 没有 SSH 密钥或 token；
- 没有服务器绝对路径；
- 没有无关临时文件。

### 6.4 本地提交

```bash
git commit -m "feat: add evaluation configuration"
```

提交后确认：

```bash
git status --short --branch
git log -1 --oneline --decorate
```

### 6.5 推送分支

```bash
git push -u origin exp/your-topic
```

如果只是个人仓库，也可以在确认无误后合并到 `main`；如果使用 Pull Request，则在 GitHub 上检查差异后再合并。

---

## 7. Windows 本机标准操作流程

本机主要负责审查和整理，不需要下载模型。

### 7.1 拉取服务器提交

```powershell
cd C:\path\to\flux2-klein-fewshot-customization
git switch main
git pull --ff-only origin main
```

### 7.2 查看改动

```powershell
git status
git log --oneline --decorate -5
git show --stat --oneline HEAD
```

### 7.3 本机新增文档后提交

```powershell
git add docs\README.md
git diff --cached --check
git commit -m "docs: improve reproduction instructions"
git push origin main
```

如果服务器正在使用 `main` 做实验，本机先不要直接推送到 `main`，应先拉取最新版本，或新建自己的分支。

---

## 8. 实验结果应该如何进入仓库

### 8.1 可以提交

```text
configs/
evaluation/protocol/
evaluation/results/*.csv
reports/*.md
脱敏后的运行参数
模型版本和 Git commit
耗时、显存和 loss 摘要
少量允许公开的精选结果
```

### 8.2 不应提交

```text
*.safetensors
checkpoint-*/
models/
runs/
outputs/
train/
holdout/
完整生成图片目录
完整训练日志
服务器 Hugging Face 缓存
```

### 8.3 结果记录模板

每轮实验至少记录：

```text
实验名称：
实验分支：
代码 commit：
基础模型：
Diffusers commit：
训练图片数量：
训练步数：
rank / alpha：
学习率：
分辨率：
推理步数：
guidance scale：
LoRA scale：
prompt：
seed：
输出目录（仅本地记录）：
定性结果：
人工评分：
问题与限制：
下一步：
```

公开报告中不要填写私人服务器路径；可以使用“本地模型目录”“私有数据目录”等描述。

---

## 9. 给 Agent 的标准提交指令

以后让 agent 操作 Git 时，建议直接使用以下模板：

```text
请在当前仓库完成本次 Git 提交，但不要自动推送到远程。

任务：
<说明本次完成的功能、实验或文档>

允许提交：
<列出明确允许添加的文件或目录>

禁止提交：
模型权重、LoRA checkpoint、原始图片、holdout 图片、生成图目录、
训练日志、缓存、虚拟环境、服务器绝对路径、token、SSH 密钥和密码。

请依次执行：
1. 查看 git status；
2. 检查敏感路径和大文件；
3. 只暂存允许提交的文件；
4. 展示 git diff --cached --stat 和 git diff --cached --name-status；
5. 做必要的语法或最小运行检查；
6. 确认没有禁止内容后再 commit；
7. 最后报告 commit hash、提交文件和未提交文件。

除非我明确说“推送到 GitHub”，不要执行 git push。
不要执行 git add .，不要使用 git commit --amend，不要强制推送。
```

如果需要推送，另行明确说明：

```text
请将刚才已经审查过的提交推送到当前分支的 origin。
推送前再次确认远程分支、提交 hash 和工作区状态。
不要使用 --force。
```

---

## 10. 发生冲突时的处理

如果 Git 提示远程有新提交：

```bash
git fetch origin
git status
```

确认当前没有未保存的重要修改后，再选择：

```bash
git pull --rebase origin main
```

不要直接使用：

```bash
git push --force
```

如果出现冲突：

1. 查看冲突文件；
2. 保留正确内容；
3. 删除冲突标记；
4. 运行语法检查；
5. `git add` 已解决文件；
6. 继续 rebase 或提交；
7. 再次查看完整 diff。

---

## 11. 项目阶段与提交建议

建议按下面顺序形成提交：

1. 项目骨架、README 和 `.gitignore`；
2. 训练脚本参数化；
3. 推理和 checkpoint 对比脚本；
4. 数据清单和裁切协议；
5. base/LoRA 归因消融配置；
6. rank 4/16/32 实验配置；
7. 4/8/16 图片数量实验配置；
8. checkpoint 和 LoRA scale 实验记录；
9. 评分协议和结果 CSV；
10. 脱敏后的最终报告和精选结果。

每一步都应该能单独解释，不要把“代码、实验图片、日志、权重和文档”混成一个提交。

---

## 12. 当前项目的推荐习惯

当前最推荐的工作循环是：

```text
服务器拉取最新代码
    ↓
创建实验分支
    ↓
修改代码或配置
    ↓
在服务器运行最小验证
    ↓
记录实验参数和结果
    ↓
筛选可公开文件
    ↓
查看暂存区
    ↓
本地提交
    ↓
推送实验分支
    ↓
确认后合并 main
```

对于本项目，模型和图片永远留在服务器；Git 只负责版本化代码、配置、评估协议和可公开的实验结论。
