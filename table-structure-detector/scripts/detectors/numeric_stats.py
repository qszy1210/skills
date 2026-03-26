from __future__ import annotations

from .base import BaseDetector, EffectiveRange, FlaggedRow, get_row_values, classify_value


class NumericStatsDetector(BaseDetector):
    """检测数值统计异常行（某行值 ≈ 前 N 行之和）。

    对每个数值列，检查当前行值是否近似等于从上一个标记行（或起始行）
    到当前行之间所有数据行的求和。容忍浮点误差。
    """

    name = "numeric_stats"

    def __init__(self, rel_tol: float = 0.001, abs_tol: float = 0.01, min_rows_before: int = 2):
        self.rel_tol = rel_tol
        self.abs_tol = abs_tol
        self.min_rows_before = min_rows_before

    def scan(self, sheet, eff: EffectiveRange) -> list[FlaggedRow]:
        all_rows: list[tuple[int, list]] = []
        for r in range(eff.min_row, eff.max_row + 1):
            values = get_row_values(sheet, r, eff)
            all_rows.append((r, values))

        if len(all_rows) < 3:
            return []

        num_cols = self._find_numeric_cols(all_rows, eff)
        if not num_cols:
            return []

        results: list[FlaggedRow] = []
        segment_start = 0

        for i in range(self.min_rows_before, len(all_rows)):
            row_num, values = all_rows[i]
            match_cols = []

            for ci in num_cols:
                cur_val = self._to_float(values[ci])
                if cur_val is None or cur_val == 0:
                    continue

                running_sum = 0.0
                count = 0
                for j in range(segment_start, i):
                    prev_val = self._to_float(all_rows[j][1][ci])
                    if prev_val is not None:
                        running_sum += prev_val
                        count += 1

                if count < self.min_rows_before:
                    continue

                if self._approx_equal(cur_val, running_sum):
                    match_cols.append(ci)

            if len(match_cols) >= max(1, len(num_cols) // 2):
                col_names = ", ".join(
                    f"col{ci + eff.min_col}" for ci in match_cols
                )
                results.append(FlaggedRow(
                    row=row_num,
                    detector=self.name,
                    detail=f"数值求和匹配: [{col_names}] ≈ 前{i - segment_start}行之和",
                    severity="high",
                ))
                segment_start = i + 1

        return results

    def _find_numeric_cols(self, all_rows: list[tuple[int, list]], eff: EffectiveRange) -> list[int]:
        """找到以数值为主的列（>= 60% 行为数值）"""
        if not all_rows:
            return []
        n_cols = eff.col_count
        num_counts = [0] * n_cols
        total = len(all_rows)

        sample_rows = all_rows[:min(50, total)]
        for _, values in sample_rows:
            for ci in range(min(n_cols, len(values))):
                if classify_value(values[ci]) == "number":
                    num_counts[ci] += 1

        sample_size = len(sample_rows)
        return [ci for ci in range(n_cols) if num_counts[ci] >= sample_size * 0.6]

    def _to_float(self, val) -> float | None:
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return float(val)
        s = str(val).strip().replace(",", "").replace(" ", "")
        try:
            return float(s)
        except (ValueError, TypeError):
            return None

    def _approx_equal(self, a: float, b: float) -> bool:
        if b == 0 and a == 0:
            return True
        if b == 0:
            return abs(a) < self.abs_tol
        return abs(a - b) / max(abs(b), 1e-10) < self.rel_tol
