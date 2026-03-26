from .base import FlaggedRow, BaseDetector
from .type_mutation import TypeMutationDetector
from .column_count import ColumnCountDetector
from .merged_cells import MergedCellsDetector
from .numeric_stats import NumericStatsDetector
from .keyword_matcher import KeywordMatcherDetector
from .empty_row import EmptyRowDetector
from .sequence_break import SequenceBreakDetector
from .format_change import FormatChangeDetector

ALL_DETECTORS = [
    TypeMutationDetector,
    ColumnCountDetector,
    MergedCellsDetector,
    NumericStatsDetector,
    KeywordMatcherDetector,
    EmptyRowDetector,
    SequenceBreakDetector,
    FormatChangeDetector,
]
