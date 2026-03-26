from __future__ import annotations

from .base import BaseDetector, EffectiveRange, FlaggedRow, get_row_values, classify_value


class TypeMutationDetector(BaseDetector):
    """检测行间数据类型签名的突变。

    计算每行的类型签名 (str, number, number, none, ...)，
    当相邻行的签名差异超过阈值时标记。
    """

    name = "type_mutation"

    def __init__(self, change_threshold: float = 0.5):
        self.change_threshold = change_threshold

    def scan(self, sheet, eff: EffectiveRange) -> list[FlaggedRow]:
        results: list[FlaggedRow] = []
        prev_sig: list[str] | None = None

        for r in range(eff.min_row, eff.max_row + 1):
            values = get_row_values(sheet, r, eff)
            sig = [classify_value(v) for v in values]

            if prev_sig is not None:
                diff_count = sum(
                    1 for a, b in zip(sig, prev_sig)
                    if a != b and a != "none" and b != "none"
                )
                comparable = sum(
                    1 for a, b in zip(sig, prev_sig)
                    if a != "none" or b != "none"
                )
                if comparable > 0 and diff_count / comparable >= self.change_threshold:
                    detail = f"类型签名突变: {_fmt_sig(prev_sig)} → {_fmt_sig(sig)}, 差异{diff_count}/{comparable}列"
                    results.append(FlaggedRow(
                        row=r,
                        detector=self.name,
                        detail=detail,
                        severity="high" if diff_count / comparable >= 0.8 else "medium",
                    ))

            prev_sig = sig

        return results


def _fmt_sig(sig: list[str]) -> str:
    abbr = {"number": "N", "str": "S", "none": "_", "date": "D", "bool": "B"}
    return "(" + ",".join(abbr.get(s, "?") for s in sig) + ")"
