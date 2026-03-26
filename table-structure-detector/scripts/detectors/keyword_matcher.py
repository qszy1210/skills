from __future__ import annotations

import re

from .base import BaseDetector, EffectiveRange, FlaggedRow, get_row_values

KEYWORDS = {
    "summary": {
        "words": ["合计", "小计", "总计", "本页合计", "累计", "期末余额",
                  "Total", "Subtotal", "Grand Total"],
        "severity": "high",
    },
    "period": {
        "words": ["期初", "期末", "本期发生", "本期合计", "本年累计",
                  "Beginning", "Ending"],
        "severity": "medium",
    },
    "meta": {
        "words": ["单位：", "单位:", "注：", "注:", "备注", "说明",
                  "制表人", "审核人", "复核人", "日期：", "日期:",
                  "编制单位", "报表日期", "币种",
                  "Unit:", "Note:", "Prepared by"],
        "severity": "medium",
    },
    "title": {
        "words": ["附表", "附件", "续表", "接上页", "转下页",
                  "Appendix", "Continued"],
        "severity": "high",
    },
}

_EXACT_MATCH_CATEGORIES = {"summary", "period"}

_PREFIX_RE_CACHE: dict[str, re.Pattern] = {}


def _is_match(cell_text: str, keyword: str, category: str) -> bool:
    """位置敏感匹配：汇总/期间类关键词要求完整值或前缀匹配，
    避免 '应付合计利息' 中的 '合计' 被误标记。"""
    if category in _EXACT_MATCH_CATEGORIES:
        stripped = cell_text.strip()
        if stripped == keyword:
            return True
        if stripped.startswith(keyword) and len(stripped) - len(keyword) <= 4:
            return True
        if stripped.endswith(keyword) and len(stripped) == len(keyword):
            return True
        return False
    return keyword in cell_text


class KeywordMatcherDetector(BaseDetector):
    """关键词匹配检测。

    对每行所有单元格执行关键词匹配。
    汇总类/期间类使用位置敏感匹配（完整值或前缀），
    元信息类/标题类使用子串匹配。
    """

    name = "keyword_match"

    def scan(self, sheet, eff: EffectiveRange) -> list[FlaggedRow]:
        results: list[FlaggedRow] = []

        for r in range(eff.min_row, eff.max_row + 1):
            values = get_row_values(sheet, r, eff)
            matches: list[str] = []
            best_severity = "low"

            for v in values:
                if v is None:
                    continue
                text = str(v).strip()
                if not text:
                    continue

                for category, info in KEYWORDS.items():
                    for kw in info["words"]:
                        if _is_match(text, kw, category):
                            matches.append(f"'{kw}'({category})")
                            if _severity_rank(info["severity"]) > _severity_rank(best_severity):
                                best_severity = info["severity"]

            if matches:
                seen = []
                for m in matches:
                    if m not in seen:
                        seen.append(m)
                results.append(FlaggedRow(
                    row=r,
                    detector=self.name,
                    detail=f"关键词命中: {', '.join(seen)}",
                    severity=best_severity,
                ))

        return results


def _severity_rank(s: str) -> int:
    return {"low": 0, "medium": 1, "high": 2}.get(s, 0)
