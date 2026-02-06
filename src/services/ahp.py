"""AHP层次分析服务"""

import numpy as np
from typing import Dict, List, Tuple

from src.config import AHP_RI_TABLE, AHP_CONSISTENCY_THRESHOLD


class AHPService:
    """AHP计算服务"""
    
    def __init__(self):
        self.matrix = None
        self.weights = None
        self.cr = None
        self.labels = []
        self.n = 0
    
    def build_matrix(self, labels: List[str], comparisons: Dict[Tuple[int, int], float]):
        """构建判断矩阵"""
        self.labels = labels
        self.n = len(labels)
        self.matrix = np.ones((self.n, self.n))
        
        for (i, j), val in comparisons.items():
            self.matrix[i, j] = val
            self.matrix[j, i] = 1.0 / val
    
    def calculate(self) -> Tuple[np.ndarray, float, float]:
        """计算权重和一致性"""
        if self.matrix is None:
            raise ValueError("请先构建判断矩阵")
        
        if self.n < 2:
            self.weights = np.array([1.0])
            self.cr = 0.0
            return self.weights, 0.0, 0.0
        
        # 特征值分解
        eigenvalues, eigenvectors = np.linalg.eig(self.matrix)
        max_idx = np.argmax(eigenvalues.real)
        max_eigen = eigenvalues[max_idx].real
        
        # 权重
        weights = eigenvectors[:, max_idx].real
        self.weights = weights / np.sum(weights)
        
        # 一致性
        ci = (max_eigen - self.n) / (self.n - 1)
        ri = AHP_RI_TABLE.get(self.n, 1.49)
        self.cr = ci / ri if ri > 0 else 0
        
        return self.weights, ci, self.cr
    
    def is_consistent(self) -> bool:
        """检查一致性"""
        if self.cr is None:
            self.calculate()
        return self.cr < AHP_CONSISTENCY_THRESHOLD
    
    def get_weights_dict(self) -> Dict[str, float]:
        """获取权重字典"""
        if self.weights is None:
            self.calculate()
        return {label: float(w) for label, w in zip(self.labels, self.weights)}
