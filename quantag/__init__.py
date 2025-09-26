# Keep it minimal – just namespace exposure
__version__ = "0.1.0"

from .qaoa import QAOASolver
from .qimage import QImageCompressor

__version__ = "0.2.0"

__all__ = ["QAOASolver", "QImageCompressor"]

