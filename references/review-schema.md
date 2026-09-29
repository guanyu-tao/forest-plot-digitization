# 复核文件格式

`candidates.jsonl` 每行给出 `pdf`, `page`, `row`, `ocr_cells`, `ocr_tokens`, `grid`。`row` 是页面表格正文自上而下的序号，从 1 开始；表格外手写附记可用后续序号并在 `issue` 中说明。

当 `grid_issues.json` 指出格线推算不可靠时，可在工作目录放 `grid_overrides.json`，以 PDF 文件名和页码给出原图像素坐标的递增 `x`、`y` 格线数组，然后重跑 `candidates`。后河表需要 13 或 14 条竖线、42 条横线；横线包含表头上/下边及 40 行记录边界。示意：`{"SAMPLE.pdf":{"1":{"x":[...],"y":[...]}}}`。覆盖值须先在原图上核对，不能从 OCR 文本位置猜线。

扫描方向不正时，可在工作目录放 `page_rotations.json`，按 PDF 文件名与页码指定顺时针角度 90、180 或 270，例如 `{"SAMPLE.pdf":{"3":90}}`。之后用 `render --force` 重渲染受影响页；脚本会删除该页旧 OCR 候选，再重跑 OCR 和格线定位。中间图片可以改，原 PDF 不改。

逐页查看图像后，建立 `page_reviews.json`：

```json
{
  "SAMPLE.pdf": {
    "1": {"expected_rows": 40, "xy_unit": "cm", "unit_evidence": "页眉注明 cm，逐格对照", "checked": true},
    "2": {"expected_rows": 0, "xy_unit": null, "unit_evidence": "空白表", "checked": true}
  }
}
```

如果同页混用单位，`xy_unit` 设为 `mixed`，各行分别写 `xy_unit` 和 `unit_evidence`。若无法确定，写 `unknown`，`finalize` 会把 X/Y 留空并标记待核。不要只根据数值范围选择单位。

`reviewed.jsonl` 每行至少含 `pdf`, `page`, `row`, `checked`, `sample`, `small`, `tag`, `species`, `x`, `y`, `dbh`, `d1`…`d6`, `remark`。可加 `date`, `xy_unit`, `unit_evidence`, `small_source`, `species_source`, `status`, `issue`, `confidence`, `edits`。示例：

```json
{"pdf":"SAMPLE.pdf","page":1,"row":1,"checked":true,"sample":"0304","small":2,"small_source":"原格明确","tag":"HHBX03040014","species":"尖连蕊茶","x":240,"y":310,"dbh":2.34,"d1":"1.25g1","d2":null,"d3":null,"d4":null,"d5":null,"d6":null,"remark":null,"confidence":"高","issue":"标牌原写疑似0055；结合字形及重号修订","edits":[{"field":"tag","from":"HHBX03040055","to":"HHBX03040014","evidence":"第1页第14行原图及两侧编号"}]}
```

`checked=true` 意味着此行已对照扫描图复核所有字段，不能由脚本批量伪造。字段值不确定时写 `null` 并用 `issue` 描述原字形和候选；不要用顺序自动补号。`edits` 只放实际修订，含字段、原值、新值和图像或名录依据。自动单位换算由终版脚本另外记录。

从 OCR 生成复核草稿时可以先填候选文本，但 `checked` 必须为 `false`；最终脚本拒绝未复核记录和未签收页面。
