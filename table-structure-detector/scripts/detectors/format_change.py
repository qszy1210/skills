from __future__ import annotations

from .base import BaseDetector, EffectiveRange, FlaggedRow


def _to_rgb(color) -> str | None:
    """尝试将 openpyxl 颜色对象转为 RGB hex 字符串"""
    if color is None:
        return None
    if hasattr(color, "rgb") and color.rgb and color.rgb != "00000000":
        rgb = str(color.rgb)
        if len(rgb) == 8:
            return rgb[2:]
        return rgb
    if hasattr(color, "theme") and color.theme is not None:
        return f"theme:{color.theme}"
    return None


def _get_row_format(sheet, row: int, eff: EffectiveRange) -> dict:
    """提取一行的格式特征"""
    bolds = []
    sizes = []
    fills = []

    for c in range(eff.min_col, eff.max_col + 1):
        cell = sheet.cell(row=row, column=c)
        font = cell.font
        fill = cell.fill

        bolds.append(bool(font.bold) if font.bold is not None else False)
        sizes.append(font.size if font.size else 11)

        fg = _to_rgb(fill.start_color) if fill and fill.patternType else None
        fills.append(fg)

    return {
        "all_bold": all(bolds) and any(bolds),
        "max_size": max(sizes) if sizes else 11,
        "has_fill": any(f is not None for f in fills),
        "fill_sig": tuple(fills),
        "bold_sig": tuple(bolds),
    }


class FormatChangeDetector(BaseDetector):
    """检测行间格式突变（加粗、字号、背景色）。

    排除周期性格式变化（斑马纹），只关注非周期性突变。
    """

    name = "format_change"

    def scan(self, sheet, eff: EffectiveRange) -> list[FlaggedRow]:
        results: list[FlaggedRow] = []
        prev_fmt: dict | None = None
        fmt_history: list[dict] = []

        for r in range(eff.min_row, eff.max_row + 1):
            fmt = _get_row_format(sheet, r, eff)
            changes: list[str] = []

            if fmt["all_bold"]:
                if prev_fmt is None or not prev_fmt["all_bold"]:
                    changes.append("全行加粗")

            if prev_fmt is not None and fmt["max_size"] > prev_fmt["max_size"] + 2:
                changes.append(f"字号增大: {prev_fmt['max_size']} → {fmt['max_size']}")

            if fmt["has_fill"] and (prev_fmt is None or not prev_fmt["has_fill"]):
                if not self._is_zebra(fmt, fmt_history):
                    changes.append("背景色突变")

            if changes:
                results.append(FlaggedRow(
                    row=r,
                    detector=self.name,
                    detail=", ".join(changes),
                    severity="medium",
                ))

            fmt_history.append(fmt)
            prev_fmt = fmt

        return results

    def _is_zebra(self, current_fmt: dict, history: list[dict]) -> bool:
        """检测是否为斑马纹（交替行底色）"""
        if len(history) < 4:
            return False
        recent = history[-4:]
        fills = [h["fill_sig"] for h in recent] + [current_fmt["fill_sig"]]
        unique = set(fills)
        if len(unique) == 2:
            a, b = list(unique)
            pattern = [f == a for f in fills]
            alternating = all(pattern[i] != pattern[i + 1] for i in range(len(pattern) - 1))
            return alternating
        return False
