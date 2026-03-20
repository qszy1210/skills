---
name: book-branch-matching
description: >-
  Maps 核算账簿名称 strings to branch master rows (中心支行 / 基层支行) using
  contiguous subsequence matching rules based on bank naming patterns. Use when
  linking ledger book names from auxiliary ledgers to 分支机构清单 or branch
  lists.
---

# 核算账簿 ↔ 分支机构 匹配 Skill

## 背景

辅助明细账中，`核算账簿名称` 字段标识了数据所属的账簿（如 "XX银行A市中心支行本部基准账簿"）。同时存在一份分支机构清单，列出了所有中心支行和基层支行。需要建立两者之间的映射关系。

## 数据结构

### 核算账簿名称

格式: `{银行前缀}{地理名称}{组织层级}{账簿后缀}`

| 组成部分 | 示例 |
|---------|------|
| 银行前缀 | "XX银行" / "XX银行股份有限公司" |
| 地理名称 | "A市"、"B市"、"C区" |
| 组织层级 | "中心支行本部"、"支行汇总" |
| 账簿后缀 | "基准账簿" |

### 分支机构清单

来源: 分支机构清单 Excel 文件

列: `序号 | 地区 | 中心支行/支行名称`

层级: 每个地区有 1 个中心支行 + N 个基层支行。大部分基层支行没有独立的核算账簿，其数据在中心支行账簿中汇总。

## 匹配算法

### 第一步：提取地理关键词

从支行名称中剥离组织后缀，提取核心地理词汇：

**剥离的组织后缀**（按优先级排序）:
1. `中心支行`
2. `执行支行`
3. `中支`
4. `支行`
5. `总行`

**进一步剥离行政区划后缀**（可选，获得更短候选词）:
- `区`、`市`、`县`、`旗`、`盟`

**示例**:
| 支行名称 | 候选关键词 |
|---------|----------|
| A市中心支行 | ["A市"] |
| B区支行 | ["B区", "B"] |
| C盟中心支行 | ["C盟", "C"] |
| D地区执行支行 | ["D地区"] |

**过滤规则**:
- 关键词长度 < 2 字 → 丢弃
- 关键词与银行全称相同（过于宽泛）→ 丢弃

### 第二步：子串匹配

依次用候选关键词（从具体到模糊）在所有账簿名称中做 `in` 子串匹配：
- 匹配到多个账簿 → 选最短的（最具体的匹配）
- 所有候选词都未匹配 → 标记为 "未匹配"

### 已知限制

1. **简称无法识别**: 地名简称（如 "X市支行" 中的 "X市"）可能无法匹配到完整地名（如 "X林浩特"）
2. **总行特殊**: 总行级账簿的关键词过于宽泛，被过滤规则排除
3. **基层支行**: 大部分基层支行没有独立账簿，属于上级中心支行汇总范围内

## 脚本位置

`scripts/book_branch_matcher.py`

主要接口:
```python
from book_branch_matcher import load_branch_list, match_branches_to_books

branches = load_branch_list('path/to/branch_list.xls')
matches, unmatched_branches, unmatched_books = match_branches_to_books(branches, book_names)
```
