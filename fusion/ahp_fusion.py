"""AHP融合引擎

实现层次分析法(AHP)的权重计算和一致性检验。
"""

import numpy as np
from typing import Dict, List, Tuple, Optional

from core.constants import AHP_RI_TABLE, AHP_CONSISTENCY_THRESHOLD
from core.data_models import ESGMetrics


class AHPFusionEngine:
    """AHP层次分析法引擎
    
    提供判断矩阵构建、权重计算、一致性检验和自动修正功能。
    """
    
    def __init__(self):
        self.matrix: Optional[np.ndarray] = None
        self.weights: Optional[np.ndarray] = None
        self.cr: Optional[float] = None
        self.labels: List[str] = []
        self.n: int = 0
    
    def build_matrix(self, labels: List[str], comparisons: Dict[Tuple[int, int], float]) -> np.ndarray:
        """构建判断矩阵
        
        Args:
            labels: 准则标签列表
            comparisons: 两两比较值字典，键为(i, j)元组，值为相对重要性
            
        Returns:
            构建的判断矩阵
        """
        self.labels = labels
        self.n = len(labels)
        self.matrix = np.ones((self.n, self.n))
        
        for (i, j), value in comparisons.items():
            if not (0 <= i < self.n and 0 <= j < self.n):
                raise ValueError(f"矩阵索引越界: ({i}, {j})")
            if value <= 0:
                raise ValueError(f"比较值必须为正数，得到: {value}")
            
            self.matrix[i, j] = value
            self.matrix[j, i] = 1.0 / value
        
        return self.matrix
    
    def calculate_weights(self) -> Tuple[np.ndarray, float, float]:
        """计算权重和一致性
        
        使用特征向量法计算权重，并计算一致性指标。
        
        Returns:
            (权重数组, CI值, CR值)
        """
        if self.matrix is None:
            raise ValueError("请先构建判断矩阵")
        
        if self.n < 2:
            # 单准则情况
            self.weights = np.array([1.0])
            self.cr = 0.0
            return self.weights, 0.0, 0.0
        
        # 计算特征值和特征向量
        eigenvalues, eigenvectors = np.linalg.eig(self.matrix)
        max_eigenvalue = np.max(eigenvalues.real)
        idx = np.argmax(eigenvalues.real)
        
        # 提取主特征向量并归一化
        weights = eigenvectors[:, idx].real
        weights = weights / np.sum(weights)
        self.weights = weights
        
        # 计算一致性指标
        ci = (max_eigenvalue - self.n) / (self.n - 1)
        ri = AHP_RI_TABLE.get(self.n, 1.49)
        cr = ci / ri if ri > 0 else 0.0
        self.cr = cr
        
        return weights, ci, cr
    
    def is_consistent(self, threshold: float = AHP_CONSISTENCY_THRESHOLD) -> bool:
        """检查一致性
        
        Args:
            threshold: 一致性比率阈值，默认0.1
            
        Returns:
            是否通过一致性检验
        """
        if self.cr is None:
            self.calculate_weights()
        return self.cr is not None and self.cr < threshold
    
    def auto_correct(self, max_iterations: int = 100, target_cr: float = AHP_CONSISTENCY_THRESHOLD) -> np.ndarray:
        """自动修正矩阵使其通过一致性检验
        
        使用加权平均法逐步修正判断矩阵。
        
        Args:
            max_iterations: 最大迭代次数
            target_cr: 目标一致性比率
            
        Returns:
            修正后的判断矩阵
        """
        if self.is_consistent(target_cr):
            return self.matrix
        
        corrected = self.matrix.copy()
        
        for iteration in range(max_iterations):
            weights, ci, cr = self.calculate_weights()
            
            if cr < target_cr:
                break
            
            # 构建一致性矩阵
            consistent_matrix = np.outer(weights, 1 / weights)
            
            # 加权平均修正
            alpha = 0.5
            corrected = (1 - alpha) * corrected + alpha * consistent_matrix
            
            # 保持互反性
            for i in range(self.n):
                for j in range(i + 1, self.n):
                    corrected[j, i] = 1.0 / corrected[i, j]
                    # 确保对角线为1
                    corrected[i, i] = 1.0
                    corrected[j, j] = 1.0
            
            self.matrix = corrected
        
        return corrected
    
    def get_weights_dict(self) -> Dict[str, float]:
        """获取权重字典
        
        Returns:
            准则标签到权重的映射字典
        """
        if self.weights is None:
            self.calculate_weights()
        
        return {
            label: float(weight) 
            for label, weight in zip(self.labels, self.weights)
        }
    
    def generate_suggestions(self, perspective: str = "balanced") -> Dict:
        """基于视角生成权重建议
        
        Args:
            perspective: 评估视角，可选 financial/compliance/brand/balanced
            
        Returns:
            包含建议权重、理由和置信度的字典
        """
        suggestions = {
            'financial': {
                'E': 0.25, 
                'S': 0.30, 
                'G': 0.45,
                'reasoning': '投资者视角：重视治理透明度和财务稳健性',
                'confidence': 0.8
            },
            'compliance': {
                'E': 0.40, 
                'S': 0.25, 
                'G': 0.35,
                'reasoning': '监管视角：强调环境合规和风险管理',
                'confidence': 0.8
            },
            'brand': {
                'E': 0.30, 
                'S': 0.45, 
                'G': 0.25,
                'reasoning': '公众视角：关注社会责任和环境影响',
                'confidence': 0.8
            },
            'balanced': {
                'E': 0.333, 
                'S': 0.333, 
                'G': 0.334,
                'reasoning': '均衡视角：ESG三维度同等重要',
                'confidence': 0.9
            }
        }
        
        return suggestions.get(perspective, suggestions['balanced'])
    
    def get_consistency_details(self) -> Dict[str, float]:
        """获取一致性检验详细信息
        
        Returns:
            包含lambda_max、CI、RI、CR的字典
        """
        if self.weights is None:
            self.calculate_weights()
        
        eigenvalues, _ = np.linalg.eig(self.matrix)
        lambda_max = np.max(eigenvalues.real)
        ci = (lambda_max - self.n) / (self.n - 1)
        ri = AHP_RI_TABLE.get(self.n, 1.49)
        
        return {
            'lambda_max': float(lambda_max),
            'ci': float(ci),
            'ri': float(ri),
            'cr': float(self.cr) if self.cr is not None else None
        }
