# Forest Plot Digitization / 森林样地清查表电子化

将固定版式的纸质森林样地清查表扫描 PDF 转为可追溯的 Excel。仓库同时提供 Codex Skill 指令、命令行辅助脚本和后河 HHBX 表的示例配置。

**适用边界：** OCR 与格线检测只生成候选。手写物种名、标牌号、小方、坐标小数点和跨格文字必须逐页对照扫描图；无法确认的值保留疑点并标记待人工核对。本项目不会承诺只上传扫描件就能得到零错误终版。

## 安装

1. 安装 Python 3.10+、[Poppler](https://poppler.freedesktop.org/)（使 `pdftoppm` 可在 PATH 中运行），再在虚拟环境安装 `requirements.txt`。
2. 按 [PaddleOCR 3.x 官方安装说明](https://www.paddleocr.ai/main/en/version3.x/installation.html) 安装 PaddleOCR 和适合机器的 PaddlePaddle 推理环境；OCR Python 可与主环境不同。
3. 如要作为 Codex Skill 使用，把仓库目录复制到 `~/.codex/skills/forest-plot-digitization/`。脚本也可独立运行。

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
$env:PADDLE_OCR_PYTHON = "C:/path/to/paddle-venv/Scripts/python.exe"
.venv/Scripts/python scripts/forest_plot.py doctor --input-dir C:/scans
```

在 macOS/Linux 把上述虚拟环境 Python 路径改为 `.venv/bin/python`。`doctor` 显示工具状态；即使 OCR 尚未配置，也能先完成清单和渲染。

## 工作流

把输入 PDF、临时工作目录、最终输出目录分开；原 PDF 只读。执行命令时按实际路径替换变量。

```powershell
$py = ".venv/Scripts/python"
$work = "C:/temp/forest-work"
& $py scripts/forest_plot.py inventory --input-dir C:/scans --workdir $work --exclude EXAMPLE.pdf
& $py scripts/forest_plot.py render --workdir $work --dpi 220
& $env:PADDLE_OCR_PYTHON scripts/forest_plot.py ocr --workdir $work
& $py scripts/forest_plot.py candidates --workdir $work
```

逐页检查方向、清晰度、格线、实际记录数，按 [复核文件格式](references/review-schema.md) 填写工作目录中的 `page_reviews.json` 与 `reviewed.jsonl`。`reviewed_draft.jsonl` 只是 OCR 草稿，其中 `checked=false`；必须逐条看图后才能改成 `true`。格线或方向需要调整时，按该文档提供覆盖文件并重跑受影响步骤。非 HHBX 表须另建 profile 并核实表头、列数、小方范围、标牌规则、坐标范围、单位、备注规则。

```powershell
& $py scripts/forest_plot.py names --workdir $work
& $py scripts/forest_plot.py finalize --workdir $work
& $py scripts/export_xlsx.py --payload "$work/final_payload.json" --output-dir C:/output
& $py scripts/forest_plot.py validate --workdir $work --output-dir C:/output
```

`names` 仅列出候选别名；**不会自动改写物种名**。坐标仅在页或行有明确单位证据时换算为米；超过配置范围的原值会标记，不自动修正。已有输出默认拒绝覆盖；确认要替换时，导出命令显式加 `--overwrite`。

每个 PDF 得到一份 Excel，含主表、原始OCR、质检汇总、修订记录。主表只有一列最终中文物种名。OCR 原文与人工修订分开保存，便于追溯。

## 隐私与局限

本仓库不包含样地 PDF、图片、OCR 结果、复核数据或工作簿。扫描件可能含调查人员信息；不要把工作目录或输出目录提交到公开仓库。OCR 模型首次运行可能按 PaddleOCR 设置下载权重。格线检测参数基于后河 HHBX 表；其他版式必须校准。名录候选不能代替图像证据或分类学审核。

## 测试

```powershell
& $py -m unittest discover -s tests -v
```

License: MIT. 贡献新表格配置时请只用人工构造的示例，不上传真实调查表。
