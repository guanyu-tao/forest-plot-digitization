---
name: forest-plot-digitization
description: 将森林样地纸质清查表扫描 PDF 逐页 OCR、按格线录入、复核物种中文名及编号、换算坐标单位并输出可追溯 Excel。适用于后河 HHBX 版式或经配置的同类固定表格扫描件。
---

# 森林样地清查表电子化

本 Skill 把可重复的文件处理、OCR、格线定位、单位换算、质检和制表交给脚本；图像判读由执行任务的 Codex 完成。用户只需提供扫描件目录和目标输出目录。不得把“脚本运行成功”当成逐行图像复核完成。

整批任务持续推进，不为普通疑字、越界值或单页格线异常中途向用户追问；先自行放大复核，仍不能判定就留空或保留原值并标记待核。只有缺少输入文件、输出规则互相冲突或必须由用户决定的业务含义阻断工作时才请求澄清。

## 启动

1. 阅读本 Skill 的 [复核与决策规则](references/review-rules.md)。若表格不是后河 HHBX 版式，先修改或新建 profile，不套用后河的编号、面积或物种规则。
2. 如环境有 PDF 与 Spreadsheets skill，可用它们辅助看图和验证；命令行流程只依赖公开 Python 包及 Poppler。依赖与安装见仓库 README。
3. 使用 `scripts/forest_plot.py doctor` 检查 PDF 渲染器、Paddle Python 环境和输入文件。OCR 环境可由 `--ocr-python` 或 `PADDLE_OCR_PYTHON` 指定；PaddleOCR 需按官方说明单独安装合适的推理引擎。
4. 用 `inventory` 只读列出 PDF、页数、哈希；按用户排除清单跳过示例/旧文件。原 PDF 始终只读，临时图片和 OCR 放在工作目录，不写进交付目录。

## 逐页处理

以下 PowerShell 命令可分批运行，并从已有结果续跑。`--profile` 默认是本 Skill 的后河配置；其他样地须传入自己的配置。`--workdir` 要与最终 Excel 分开。`--limit-pages` 只用于试运行。

```powershell
$skill = "$env:USERPROFILE/.codex/skills/forest-plot-digitization"
$workdir = "$env:TEMP/forest-entry"
$source = "C:/scans"
python "$skill/scripts/forest_plot.py" inventory --input-dir $source --workdir $workdir --exclude EXAMPLE.pdf
python "$skill/scripts/forest_plot.py" render --workdir $workdir --dpi 220
& $env:PADDLE_OCR_PYTHON "$skill/scripts/forest_plot.py" ocr --workdir $workdir
python "$skill/scripts/forest_plot.py" candidates --workdir $workdir
```

- `inventory.json` 记录 PDF 页数及 SHA-256；`pages/` 是逐页扫描图；`ocr/` 保存原始候选和框；`candidates.jsonl` 为按真实格线分配的候选。格线检测失败或 OCR 文字落在相邻格时，打开原图确定行列，不靠记录顺序修复。
- 每页先核扫描方向、清晰度、表头日期/样方号、实际记录条数与附记；逐行逐字段检查小方、标牌、物种、X/Y/DBH、D1–D6、备注。难辨单元格可裁切放大。空白模板页也写入页级复核清单。
- 在 `reviewed.jsonl` 写入**图像复核后**的一行一记录数据，在 `page_reviews.json` 写入每页记录数、坐标单位及依据。数据格式见 [复核文件格式](references/review-schema.md)。OCR 只是候选；不要直接把 `candidates.jsonl` 改名为 `reviewed.jsonl`。
- 物种名只在原图字形支持且中文植物名录能确认时统一，优先植物智/中国植物志等权威来源；需要当前名录时联网核对。主表只保留一列最终中文名，原候选留在“原始OCR”。同属或相似名不必然同种；难辨时保留可辨原文和候选，标记待核。
- 写完 `reviewed.jsonl` 后，优先用取得使用许可的中文植物名录快照运行 `names --workdir $workdir --catalog <CSV或XLSX路径> --catalog-source <来源> --catalog-version <版本>`。对照 `species_audit.json` 的精确命中、异名、重名和未命中状态逐项核名；没有名录时可运行 `names --workdir $workdir`，但缺少逐条名录证据的名称会留待核。名录只证明名称被该版本收录，不证明扫描字形或植株鉴定正确；不得据此自动替换物种名。详细格式见 [README](README.md)。

## 终版与交付

```powershell
python "$skill/scripts/forest_plot.py" finalize --workdir $workdir
python "$skill/scripts/export_xlsx.py" --payload "$workdir/final_payload.json" --output-dir C:/output
python "$skill/scripts/forest_plot.py" validate --workdir $workdir --output-dir C:/output
```

`finalize` 只处理已复核的记录，核对每页行数、缺页、重复位置，并按页级或逐行确认的单位把 X/Y 换成 m；不能判定单位的值不进入确定的数值列。它标记 0–5 m 之外的坐标、重复标牌、样方号与标牌前缀不符、小方超界、非正或可疑 DBH、分枝胸径和缺项。异常规则是质检提示，不自动改写原图值。保留 D1–D6 的 g/z 类型。

每份 PDF 输出一份独立 Excel：`主表`、`原始OCR`、`质检汇总`、`修订记录`、`物种名录核对`。保留原 PDF 和原始 OCR；每一处改值记录原值、新值、扫描页/行、依据和置信度。导出后重新打开 Excel，核总条数与页数、表头/筛选、中文、数值类型、重复标牌、名录状态和未决项，再交付链接及每份文件的页数、条数、待核条数、主要疑点。可靠范围按实际图像复核覆盖报告，不宣称零错误。

如果用户给的是现成 Excel 的窄范围修订，仍用相同证据和质检原则，但保留其现有表结构；不要强行重跑 OCR 或覆盖原件，除非用户明确要求。
