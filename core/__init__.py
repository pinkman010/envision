"""核心模块"""

from core.data_models import ESGMetrics, AnalysisResult, BenchmarkData
from core.constants import (
    DEFAULT_DIMENSION_SCORE,
    ESG_DIMENSIONS,
    AHP_RI_TABLE,
    AHP_CONSISTENCY_THRESHOLD
)

try:
    from core.rag_engine import RAGEngine, get_rag_engine, RAGResponse
    HAS_RAG = True
except ImportError:
    HAS_RAG = False
    RAGEngine = None
    get_rag_engine = None
    RAGResponse = None

__all__ = [
    'ESGMetrics',
    'AnalysisResult', 
    'BenchmarkData',
    'DEFAULT_DIMENSION_SCORE',
    'ESG_DIMENSIONS',
    'AHP_RI_TABLE',
    'AHP_CONSISTENCY_THRESHOLD',
]

if HAS_RAG:
    __all__.extend(['RAGEngine', 'get_rag_engine', 'RAGResponse', 'HAS_RAG'])
