from __future__ import annotations

import re

from .base import BaseDetector, EffectiveRange, FlaggedRow


_SEQ_PATTERNS = [
    re.compile(r"^\s*(\d+)\s*\.?\s*$"),          # "1", "1.", " 2 "
    re.compile(r"^\s*\((\d+)\)\s*$"),             # "(1)"
    re.compile(r"^\s*（(\d+)）\s*$"),              # "（1）"
]

_CN_NUMS = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
            "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
_CIRCLED = {chr(0x2460 + i): i + 1 for i in range(20)}  # ① - ⑳


def _extract_seq(val) -> int | None:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        n = int(val)
        if n == val and 0 < n < 100000:
            return n
        return None

    s = str(val).strip()
    if not s:
        return None

    for pat in _SEQ_PATTERNS:
        m = pat.match(s)
        if m:
            return int(m.group(1))

    if s in _CN_NUMS:
        return _CN_NUMS[s]
    if s in _CIRCLED:
        return _CIRCLED[s]

    return None


class SequenceBreakDetector(BaseDetector):
    """检测序号列的连续性中断。

    自动检测哪列是序号列（前 30 行中整数递增比例最高的列）。
    标记序号重置（重新从1开始）和大幅跳跃。
    """

    name = "sequence_break"

    def scan(self, sheet, eff: EffectiveRange) -> list[FlaggedRow]:
        seq_col = self._detect_seq_col(sheet, eff)
        if seq_col is None:
            return []

        results: list[FlaggedRow] = []
        prev_seq: int | None = None

        for r in range(eff.min_row, eff.max_row + 1):
            val = sheet.cell(row=r, column=seq_col).value
            cur_seq = _extract_seq(val)

            if cur_seq is None:
                if prev_seq is not None and val is not None and str(val).strip():
                    results.append(FlaggedRow(
                        row=r,
                        detector=self.name,
                        detail=f"序号列(col{seq_col})出现非序号值: '{val}'",
                        severity="medium",
                    ))
                continue

            if prev_seq is not None:
                if cur_seq == 1 and prev_seq > 1:
                    results.append(FlaggedRow(
                        row=r,
                        detector=self.name,
                        detail=f"序号重置: {prev_seq} → 1 (可能是新子表)",
                        severity="high",
                    ))
                elif cur_seq > prev_seq + 5:
                    results.append(FlaggedRow(
                        row=r,
                        detector=self.name,
                        detail=f"序号跳跃: {prev_seq} → {cur_seq}",
                        severity="low",
                    ))

            prev_seq = cur_seq

        return results

    def _detect_seq_col(self, sheet, eff: EffectiveRange) -> int | None:
        """在前几列中找到最像序号列的那一列"""
        best_col = None
        best_score = 0
        scan_rows = min(30, eff.max_row - eff.min_row + 1)

        for c in range(eff.min_col, min(eff.min_col + 4, eff.max_col + 1)):
            seqs = []
            for r in range(eff.min_row, eff.min_row + scan_rows):
                val = sheet.cell(row=r, column=c).value
                s = _extract_seq(val)
                if s is not None:
                    seqs.append(s)

            if len(seqs) < 3:
                continue

            increasing = sum(
                1 for i in range(1, len(seqs)) if seqs[i] == seqs[i - 1] + 1
            )
            score = increasing / len(seqs)
            if score > best_score:
                best_score = score
                best_col = c

        if best_score >= 0.5:
            return best_col
        return None
