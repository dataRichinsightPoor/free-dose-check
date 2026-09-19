"""Free-Dose Check: a research-use equilibrium design aid."""

__version__ = "0.1.0"

from .report import analyze, dumps, to_csv
from .schema import ValidationError

__all__ = ["analyze", "dumps", "to_csv", "ValidationError", "__version__"]
