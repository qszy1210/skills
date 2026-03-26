---
name: table-structure-detector
description: >-
  Identifies structural regions (headers, data areas, footers, subtotals)
  in Excel sheets containing complex layouts. Use when a sheet has multiple
  sub-tables, merged header rows, subtotal/summary rows mixed into data,
  or ambiguous data region boundaries. Outputs flagged rows for AI judgment.
  NOT for file I/O (use xlsx) or accounting semantics (use account-code).
---

# Excel 表结构检测

## 触发条件

当需要从 Excel 表格中**定位结构区域边界**时使用此 skill，典型场景：

- Sheet 中包含**多个子表**（纵向拼接，中间有空行或重复表头）
- 表头占据**多行**（合并单元格、多级表头）
- 数据区中**穿插小计/合计行**
- 表格前后有**元信息行**（标题、单位、制表人、附注等）
- 不确定数据从**第几行开始、到第几行结束**

**不适用场景（使用其他 skill）**：
- 文件读写操作 → 使用 `xlsx` skill
- 科目编码/名称语义理解 → 使用 `account-code-understanding` skill
- 账簿与分支机构匹配 → 使用 `book-branch-matching` skill

---

## 两层架构

```
┌─────────────────────────────────┐     ┌─────────────────────────────────┐
│  第一层：Python 确定性扫描        │     │  第二层：AI 判断                  │
│  (全量行, 0 token)               │     │  (只看标记行, 极少 token)          │
│                                 │     │                                 │
│  ● 数据类型突变检测               │     │  ● 判断行的角色                   │
│  ● 非空列数变化检测               │ ──→ │    表头 / 小计 / 脏数据？          │
│  ● 合并单元格检测                 │ 只传 │  ● 判断表结构边界                 │
│  ● 数值统计异常检测               │ 异常 │    第几行到第几行是数据区？          │
│  ● 关键词匹配                    │ 行   │  ● 更新解析规则                   │
│  ● 空行检测                      │     │    发现新子表 → 输出新 schema      │
│  ● 序号连续性检测                 │     │  ● 输出决策                       │
│  ● 格式突变检测                   │     │    skip / use_new_schema /        │
│                                 │     │    flag_error                     │
└─────────────────────────────────┘     └─────────────────────────────────┘
```

**核心思路**：第一层用 Python 脚本在毫秒级扫描全量行，将万行数据压缩为数个标记行；第二层 AI 只需审阅这些标记行即可做出判断，token 消耗极低。

---

## 第一层：8 个检测器

### 1. type_mutation — 数据类型突变

计算每行的**类型签名** `(S,N,N,_,N)` 并与前一行对比。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| change_threshold | 0.5 | 签名差异比例阈值 |

**标记条件**：可比列中 ≥ 50% 类型发生变化。

**类型分类规则**：
- `number`：int/float，或可解析为数字的字符串（如 "1,234.56"）
- `str`：文本
- `date`：datetime/date/time 对象
- `none`：None 或空白字符串
- `bool`：布尔值

**边缘场景处理**：
- 数字存储为文本 → 尝试解析后再判定
- 日期格式多样 → 统一归类为 `date`
- 首行无前行可比 → 不标记（由其他检测器覆盖）

### 2. column_count — 非空列数变化

统计每行非空列数，与全表非零行中位数对比。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| low_ratio | 0.5 | 低于中位数此比例则标记 |
| high_ratio | 1.5 | 高于中位数此比例则标记 |

**标记条件**：
- 非空列数 ≤ 2 且中位数 > 3 → 标记为「单值行」（元信息行候选）
- 非空列数 < 中位数 × 0.5 → 标记为偏少
- 非空列数 > 中位数 × 1.5 → 标记为偏多

### 3. merged_cells — 合并单元格

通过 `sheet.merged_cells.ranges` 读取合并区域。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| min_col_span | 3 | 跨列合并最少列数 |
| min_coverage | 0.5 | 合并覆盖有效列宽比例 |

**标记条件**：
- 跨列合并 ≥ 3 列或覆盖 ≥ 50% 有效列宽 → severity: high
- 跨行合并 ≥ 2 行（不满足跨列条件时）→ 单独记录

**边缘场景**：仅合并 2 列通常是排版需要，不标记。

### 4. numeric_stats — 数值统计异常

对数值列检查某行值是否 ≈ 前 N 行之和。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| rel_tol | 0.001 | 相对误差阈值 |
| abs_tol | 0.01 | 绝对误差阈值（当 sum=0 时使用） |
| min_rows_before | 2 | 至少有 N 行才做求和比较 |

**标记条件**：≥ 半数数值列的当前行值与前段求和近似相等。

**边缘场景**：
- 浮点精度 → 使用相对误差容忍
- sum = 0 → 改用绝对差
- 累计值模式 → 每行 = 前行 + 增量，不满足"等于多行之和"条件，不会误标
- 多层小计 → 每次命中后重置 segment 起点，自然处理嵌套

### 5. keyword_match — 关键词匹配

对每行所有单元格执行关键词匹配。

**关键词表**：

| 类别 | 关键词 | 匹配方式 |
|------|--------|---------|
| summary（汇总） | 合计、小计、总计、本页合计、累计、期末余额、Total、Subtotal、Grand Total | 精确/前缀匹配 |
| period（期间） | 期初、期末、本期发生、本期合计、本年累计、Beginning、Ending | 精确/前缀匹配 |
| meta（元信息） | 单位：、注：、备注、说明、制表人、审核人、日期：、编制单位、币种、Unit:、Note: | 子串匹配 |
| title（标题） | 附表、附件、续表、接上页、转下页、Appendix、Continued | 子串匹配 |

**位置敏感**：summary 和 period 类使用精确值/前缀匹配，避免「应付合计利息」中的「合计」被误标。meta 和 title 类使用子串匹配。

### 6. empty_row — 空行检测

检测所有单元格为 None 或空白的行。

**特殊处理**：
- 连续空行合并为一个分隔事件
- 仅含空格/换行符 → strip() 后判定为空
- 仅有格式（背景色）无值 → 视为空行

### 7. sequence_break — 序号连续性检测

自动检测序号列，监测序号重置和跳跃。

**序号列自动检测**：扫描前 4 列的前 30 行，选择整数递增比例最高的列（≥ 50% 则认定）。

**支持的序号格式**：`1`、`1.`、`(1)`、`（1）`、`一`~`十`、`①`~`⑳`

**标记条件**：
- 序号重置为 1（前值 > 1）→ severity: high（新子表信号）
- 序号跳跃 > 5 → severity: low
- 非序号值出现在序号列 → severity: medium

### 8. format_change — 格式突变检测

读取单元格的 font.bold、font.size、fill 等静态格式属性。

**标记条件**：
- 全行加粗（前行非全部加粗）→ 表头或小计行信号
- 字号增大 > 2pt → 标题行信号
- 背景色从无到有且非斑马纹 → 分组/分隔信号

**斑马纹排除**：检查最近 4 行的填充模式，若为严格交替则排除。

**限制**：openpyxl 无法读取条件格式的运行时效果，仅检测静态格式。主题色转为 `theme:N` 标识用于对比。

---

## 更多边缘场景

| 场景 | 表现 | 检测方式 |
|------|------|---------|
| 冻结窗格 | `freeze_panes` 不为 None | 作为辅助信号记录在 sheet 元信息中 |
| 隐藏行 | `row_dimensions[r].hidden` | 记录在 `hidden_rows` 中，不跳过扫描 |
| 分组折叠行 | `outline_level > 0` | 记录在 `outlined_rows` 中，level 变化边界 = 潜在区域边界 |
| 打印区域 | `print_area` 有值 | 记录在 sheet 元信息中，辅助确认表格边界 |
| 重复表头（翻页） | 相同内容多次出现 | type_mutation 检测器会标记签名突变 |
| 交叉表/矩阵表 | 行列都有表头 | merged_cells + 左上角空值 + 首行首列同为文本 |
| 百分比/占比行 | 值在 0-1 或 0-100 | keyword_match 覆盖「占比」关键词 |
| 多子表拼接 | 同 Sheet 内多个独立表 | empty_row 分隔 + sequence_break 序号重置 |
| 日期列断点 | 日期序列跳跃 | sequence_break 的扩展检测 |
| 续表标记 | 「续表」「接上页」 | keyword_match 覆盖 |

---

## 第二层：AI 判断指南

### 输入

AI 收到第一层输出的 JSON，核心关注：
1. `flagged_rows` — 每个标记行的检测器名称和详情
2. `preliminary_regions` — 脚本的初步区域划分（可能不完全准确）
3. sheet 元信息（freeze_pane、hidden_rows 等辅助信号）

### 判断任务

1. **确认或修正每个区域的类型**：header / data / subtotal / footer / meta_info / separator
2. **确定每个子表的 schema**：列名映射
3. **输出最终决策**：
   - `skip` — 跳过此行（分隔符、无关内容）
   - `use_new_schema` — 发现新子表，使用新 schema 解析后续数据
   - `flag_error` — 无法判定，需人工审查

### Prompt 模板

```
你是一个 Excel 表结构分析专家。以下是对一个 Excel sheet 的第一层自动扫描结果。

## Sheet 元信息
{sheet_meta_json}

## 标记行
{flagged_rows_json}

## 初步区域划分
{preliminary_regions_json}

## 你的任务

1. 审阅标记行和初步划分，判断每个区域的真实类型
2. 特别注意：
   - 标记为 header 的区域是否确实是表头？有没有漏掉的表头行？
   - 数据区中穿插的小计行是否正确识别？
   - 是否存在未被检测到的子表边界？
3. 输出修正后的结构，格式如下：

```json
{
  "tables": [
    {
      "name": "描述性名称",
      "header_rows": [起始行, 结束行],
      "data_rows": [起始行, 结束行],
      "footer_rows": [行号列表],
      "schema": {"A": "列名", "B": "列名", ...}
    }
  ],
  "meta_rows": [行号列表],
  "skipped_rows": [行号列表],
  "decision": "skip | use_new_schema | flag_error"
}
```
```

---

## 区域推断逻辑

第一层脚本在输出 `preliminary_regions` 时使用以下规则：

1. **空行** → `separator` 类型，将行范围分割为独立段
2. 每个段内部：
   - **段首连续标记行**（merged_cells / format_change / type_mutation / column_count）→ `header` 候选
   - 其中 keyword_match 命中 meta 类或 column_count 命中「单值行」的 → 从 header 中分离为 `meta_info`
   - **段中无标记行** → `data` 区域
   - **段尾标记行**（keyword_match / numeric_stats）→ `subtotal` 或 `footer`
3. 数据区内部的标记行：
   - sequence_break 命中「序号重置」→ 在此处拆分，插入新 `header`
   - keyword_match / numeric_stats 命中 → 插入 `subtotal`
4. 每个区域附带 `confidence`（high / medium），基于标记数量和检测器一致性

---

## 脚本接口

### 脚本位置

`scripts/table_structure_detector.py`

### CLI 用法

```bash
# 扫描默认 sheet
python scripts/table_structure_detector.py input.xlsx

# 指定 sheet
python scripts/table_structure_detector.py input.xlsx --sheet "Sheet1"

# 扫描所有 sheet
python scripts/table_structure_detector.py input.xlsx --all-sheets

# 紧凑输出
python scripts/table_structure_detector.py input.xlsx --indent 0
```

### Python API

```python
from table_structure_detector import detect_structure, detect_all_sheets

# 单个 sheet
result = detect_structure("input.xlsx", sheet_name="Sheet1")
print(result["flagged_rows"])
print(result["preliminary_regions"])

# 所有 sheet
results = detect_all_sheets("input.xlsx")
for r in results:
    print(r["sheet"], len(r.get("flagged_rows", [])), "flagged rows")
```

### 依赖

仅需 `openpyxl`（xlsx skill 中已有）。

### 输出格式

```json
{
  "file": "input.xlsx",
  "sheet": "Sheet1",
  "total_rows": 150,
  "total_cols": 6,
  "effective_col_range": [1, 6],
  "freeze_pane": "A3",
  "print_area": "A1:F100",
  "hidden_rows": [75, 76],
  "outlined_rows": [{"row": 50, "level": 1}],
  "flagged_rows": [
    {
      "row": 1,
      "flags": [
        {"detector": "merged_cells", "detail": "A1:F1 横向合并6列", "severity": "high"},
        {"detector": "format_change", "detail": "全行加粗", "severity": "medium"}
      ]
    }
  ],
  "preliminary_regions": [
    {"type": "meta_info", "rows": [1, 1], "confidence": "medium"},
    {"type": "header", "rows": [2, 3], "confidence": "high"},
    {"type": "data", "rows": [4, 49], "confidence": "high"},
    {"type": "subtotal", "rows": [50, 50], "confidence": "high"},
    {"type": "separator", "rows": [51, 51], "confidence": "high"},
    {"type": "header", "rows": [52, 52], "confidence": "medium"},
    {"type": "data", "rows": [53, 99], "confidence": "medium"},
    {"type": "footer", "rows": [100, 100], "confidence": "medium"}
  ]
}
```

### 检测器列表

| 检测器 | 类名 | 关注信号 |
|--------|------|---------|
| type_mutation | TypeMutationDetector | 行间类型签名突变 |
| column_count | ColumnCountDetector | 非空列数偏离中位数 |
| merged_cells | MergedCellsDetector | 合并单元格 |
| numeric_stats | NumericStatsDetector | 数值求和匹配 |
| keyword_match | KeywordMatcherDetector | 关键词命中 |
| empty_row | EmptyRowDetector | 空行/分隔行 |
| sequence_break | SequenceBreakDetector | 序号重置/跳跃 |
| format_change | FormatChangeDetector | 格式突变 |
