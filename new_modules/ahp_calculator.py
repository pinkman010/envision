# -*- coding: utf-8 -*-
"""
模块二：智能权重配置
技术：AHP层次分析法 + 一致性检验
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
import json


class AHPCalculator:
    """AHP层次分析法计算器"""
    
    # 语义标度映射：自然语言 -> 数值 (1-9标度)
    SEMANTIC_SCALE = {
        '极端重要': 9,
        '明显重要': 7,
        '强烈重要': 5,
        '稍微重要': 3,
        '同等重要': 1,
        '稍微次要': 1/3,
        '强烈次要': 1/5,
        '明显次要': 1/7,
        '极端次要': 1/9
    }
    
    # 中间值
    INTERMEDIATE_VALUES = {
        '极端重要-明显重要': 8,
        '明显重要-强烈重要': 6,
        '强烈重要-稍微重要': 4,
        '稍微重要-同等重要': 2,
        '同等重要-稍微次要': 1/2,
        '稍微次要-强烈次要': 1/4,
        '强烈次要-明显次要': 1/6,
        '明显次要-极端次要': 1/8
    }
    
    def __init__(self):
        self.matrix = None
        self.weights = None
        self.cr = None
        self.n = 0
        self.labels = []
    
    def create_comparison_matrix(
        self, 
        labels: List[str],
        comparisons: Dict[Tuple[int, int], float]
    ) -> np.ndarray:
        """
        创建判断矩阵
        
        Args:
            labels: 指标名称列表 ['E', 'S', 'G']
            comparisons: {(i,j): value} 两两比较结果
        
        Returns:
            判断矩阵
        """
        self.labels = labels
        self.n = len(labels)
        self.matrix = np.ones((self.n, self.n))
        
        for (i, j), value in comparisons.items():
            self.matrix[i, j] = value
            self.matrix[j, i] = 1.0 / value
        
        return self.matrix
    
    def calculate_weights(self) -> Tuple[np.ndarray, float, float]:
        """
        计算权重向量、一致性指标CI、一致性比率CR
        
        Returns:
            (weights, ci, cr)
        
        [FIXED] 增加特征值有效性验证，防止数值异常导致错误结果
        """
        if self.matrix is None:
            raise ValueError("请先创建判断矩阵")
        
        # 特征向量法计算权重
        eigenvalues, eigenvectors = np.linalg.eig(self.matrix)
        
        # [ADDED] 验证特征值有效性
        if np.any(np.iscomplex(eigenvalues)):
            # 如果存在显著虚部，发出警告但仍取实部（对称矩阵应为实数）
            if np.any(np.abs(eigenvalues.imag) > 1e-10):
                import warnings
                warnings.warn("判断矩阵可能不满足互反性，产生了复数特征值")
        
        # 取最大特征值
        max_eigenvalue = np.max(eigenvalues.real)
        idx = np.argmax(eigenvalues.real)
        
        # [ADDED] 验证最大特征值是否在合理范围内（n <= max_eigenvalue <= 2n）
        n = self.n
        if not (n <= max_eigenvalue <= 2 * n):
            raise ValueError(
                f"最大特征值 {max_eigenvalue:.4f} 超出理论范围 [{n}, {2*n}]،"
                "请检查判断矩阵是否满足互反性和正定性"
            )
        
        # 对应特征向量（权重）
        weights = eigenvectors[:, idx].real
        weights = weights / np.sum(weights)  # 归一化
        
        self.weights = weights
        
        # 一致性检验
        ci = (max_eigenvalue - self.n) / (self.n - 1)
        
        # 随机一致性指标RI
        ri_table = {1: 0, 2: 0, 3: 0.58, 4: 0.90, 5: 1.12, 
                   6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45}
        ri = ri_table.get(self.n, 1.49)
        
        cr = ci / ri if ri > 0 else 0
        self.cr = cr
        
        return weights, ci, cr
    
    def is_consistent(self, threshold: float = 0.1) -> bool:
        """检查一致性"""
        if self.cr is None:
            self.calculate_weights()
        return self.cr < threshold
    
    def auto_correct(self, max_iterations: int = 100) -> np.ndarray:
        """
        自动修正矩阵使其通过一致性检验
        
        使用最小二乘法找到一个最接近原矩阵的一致矩阵
        
        Returns:
            修正后的矩阵
        """
        if self.matrix is None:
            raise ValueError("请先创建判断矩阵")
        
        # 如果已经一致，直接返回
        if self.is_consistent():
            return self.matrix
        
        # 迭代修正
        corrected_matrix = self.matrix.copy()
        
        for _ in range(max_iterations):
            # 计算当前权重
            weights, _, cr = self.calculate_weights()
            
            if cr < 0.1:
                break
            
            # 构建一致矩阵: a_ij = w_i / w_j
            consistent_matrix = np.outer(weights, 1/weights)
            
            # 加权平均: 向一致矩阵靠近
            alpha = 0.5  # 修正强度
            corrected_matrix = (1 - alpha) * corrected_matrix + alpha * consistent_matrix
            
            # 保持互反性
            for i in range(self.n):
                for j in range(i+1, self.n):
                    corrected_matrix[j, i] = 1.0 / corrected_matrix[i, j]
            
            self.matrix = corrected_matrix
            self.calculate_weights()
        
        return corrected_matrix
    
    def get_weights_dict(self) -> Dict[str, float]:
        """获取权重字典"""
        if self.weights is None:
            self.calculate_weights()
        
        return {label: float(weight) for label, weight in zip(self.labels, self.weights)}
    
    def generate_ai_suggestions(self, perspective: str) -> Dict:
        """
        生成AI专家评估建议
        
        Args:
            perspective: 'financial'(财务稳健性), 'compliance'(合规风险), 'brand'(品牌影响力)
        
        Returns:
            {
                'matrix': 建议的判断矩阵,
                'confidence': 置信度,
                'reasoning': 推理说明
            }
        """
        n = len(self.labels)
        suggestions = {}
        
        if perspective == 'financial':
            # 投资者视角：更关注治理和长期财务可持续性
            base_values = {
                ('E', 'S'): 1/2,  # E比S稍次要
                ('E', 'G'): 1/3,  # E比G明显次要
                ('S', 'G'): 1/2   # S比G稍次要
            }
            reasoning = "投资者视角下，公司治理(G)最为重要，其次是社会责任(S)，环境因素(E)相对次要但长期影响财务风险"
            
        elif perspective == 'compliance':
            # 监管视角：更关注合规性和风险
            base_values = {
                ('E', 'S'): 2,    # E比S稍重要（环境法规趋严）
                ('E', 'G'): 1,    # E和G同等（都受严格监管）
                ('S', 'G'): 1/2   # S比G稍次要
            }
            reasoning = "监管视角下，环境合规(E)和公司治理(G)同等重要，社会责任(S)合规要求相对较低"
            
        else:  # brand
            # 公众视角：更关注社会影响和透明度
            base_values = {
                ('E', 'S'): 1/2,  # E比S稍次要（公众更关注劳工等社会议题）
                ('E', 'G'): 1/2,  # E比G稍次要
                ('S', 'G'): 2     # S比G稍重要
            }
            reasoning = "公众视角下，社会责任(S)最受关注，环境和治理同等重要"
        
        # 构建建议矩阵
        matrix = np.ones((n, n))
        label_idx = {label: i for i, label in enumerate(self.labels)}
        
        for (label1, label2), value in base_values.items():
            if label1 in label_idx and label2 in label_idx:
                i, j = label_idx[label1], label_idx[label2]
                matrix[i, j] = value
                matrix[j, i] = 1.0 / value
        
        return {
            'matrix': matrix,
            'confidence': 0.85,
            'reasoning': reasoning,
            'suggestions': {
                'EvsS': base_values.get(('E', 'S'), 1),
                'EvsG': base_values.get(('E', 'G'), 1),
                'SvsG': base_values.get(('S', 'G'), 1)
            }
        }
    
    def adjust_for_risk(self, sentiment_scores: Dict[str, float], threshold: float = -0.6):
        """
        根据舆情风险动态调整权重
        
        Args:
            sentiment_scores: {'E': -0.7, 'S': 0.3, 'G': 0.5}
            threshold: 风险阈值
        """
        if self.weights is None:
            self.calculate_weights()
        
        adjusted_weights = self.weights.copy()
        
        for i, label in enumerate(self.labels):
            if label in sentiment_scores:
                score = sentiment_scores[label]
                if score < threshold:
                    # 负面舆情增加权重
                    risk_factor = 1 + abs(score) * 0.5  # 最大增加50%
                    adjusted_weights[i] *= risk_factor
        
        # 重新归一化
        adjusted_weights = adjusted_weights / np.sum(adjusted_weights)
        self.weights = adjusted_weights
        
        return self.get_weights_dict()


def create_three_level_ahp():
    """
    创建三层AHP结构（目标层-准则层-指标层）
    """
    # 第一层：E、S、G权重
    level1 = AHPCalculator()
    level1.create_comparison_matrix(
        ['E', 'S', 'G'],
        {(0, 1): 1.0, (0, 2): 1.0, (1, 2): 1.0}  # 默认同等重要
    )
    
    # 第二层：各维度下的二级指标
    e_indicators = AHPCalculator()
    e_indicators.create_comparison_matrix(
        ['气候变化', '能源管理', '水资源', '废弃物', '生物多样性'],
        {(0, 1): 2, (0, 2): 3, (0, 3): 3, (0, 4): 4}  # 气候变化最重要
    )
    
    s_indicators = AHPCalculator()
    s_indicators.create_comparison_matrix(
        ['员工权益', '供应链管理', '社区关系', '产品责任', '数据安全'],
        {(0, 1): 2, (0, 2): 2, (0, 3): 3, (0, 4): 2}
    )
    
    g_indicators = AHPCalculator()
    g_indicators.create_comparison_matrix(
        ['公司治理', '商业道德', '风险管理', '信息披露', '利益相关方'],
        {(0, 1): 1, (0, 2): 2, (0, 3): 2, (0, 4): 3}
    )
    
    return {
        'level1': level1,
        'E_indicators': e_indicators,
        'S_indicators': s_indicators,
        'G_indicators': g_indicators
    }