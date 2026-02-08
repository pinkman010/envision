"""AHP层次分析法引擎

实现层次分析法（Analytic Hierarchy Process），用于ESG指标权重计算和一致性检验。
支持判断矩阵构建、权重计算、一致性检验和自动修正功能。
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union

import numpy as np

from src.esg.config import AHP_CONSISTENCY_THRESHOLD, AHP_RI_TABLE

logger = logging.getLogger(__name__)


class ConsistencyStatus(Enum):
    """一致性状态"""

    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"


@dataclass
class AHPResult:
    """AHP计算结果"""

    weights: np.ndarray
    weights_dict: Dict[str, float] = field(default_factory=dict)
    max_eigenvalue: float = 0.0
    consistency_index: float = 0.0
    consistency_ratio: float = 0.0
    random_index: float = 0.0
    is_consistent: bool = False
    status: ConsistencyStatus = ConsistencyStatus.FAIL
    matrix: Optional[np.ndarray] = None
    messages: List[str] = field(default_factory=list)


class AHPFusionEngine:
    """AHP融合引擎

    用于ESG指标权重计算的AHP层次分析法引擎，支持：
    - 判断矩阵构建
    - 权重计算（特征值法）
    - 一致性检验
    - 自动矩阵修正

    Attributes:
        matrix: 判断矩阵
        labels: 指标标签列表
        n: 矩阵维度
        weights: 计算得到的权重向量
        cr: 一致性比率
    """

    def __init__(self):
        self.matrix: Optional[np.ndarray] = None
        self.labels: List[str] = []
        self.n: int = 0
        self.weights: Optional[np.ndarray] = None
        self.cr: Optional[float] = None
        self.ci: Optional[float] = None
        self.max_eigenvalue: Optional[float] = None
        self.ri: Optional[float] = None

    def build_matrix(
        self, labels: List[str], comparisons: Dict[Tuple[int, int], float], validate: bool = True
    ) -> None:
        """构建判断矩阵

        Args:
            labels: 指标标签列表，长度n
            comparisons: 两两比较字典，键为(i, j)元组，值为比较值
                        i < j 时，value > 1 表示i比j重要
                        例如 {(0, 1): 3.0} 表示指标0比指标1稍微重要
            validate: 是否验证输入数据

        Raises:
            ValueError: 输入数据不合法时抛出
        """
        if not labels:
            raise ValueError("指标标签列表不能为空")

        if validate:
            # 检查重复标签
            if len(labels) != len(set(labels)):
                raise ValueError("指标标签不能重复")

            # 检查比较值范围
            for (i, j), val in comparisons.items():
                if not (1 / 9 <= val <= 9):
                    raise ValueError(f"比较值必须在[1/9, 9]范围内，got ({i},{j}): {val}")
                if i >= j:
                    raise ValueError(f"只接受上三角矩阵比较，要求 i < j，got ({i}, {j})")
                if i >= len(labels) or j >= len(labels):
                    raise ValueError(f"索引超出范围，最大索引为 {len(labels)-1}")

        self.labels = labels.copy()
        self.n = len(labels)
        self.matrix = np.ones((self.n, self.n), dtype=np.float64)

        # 填充上三角和下三角
        for (i, j), val in comparisons.items():
            self.matrix[i, j] = float(val)
            self.matrix[j, i] = 1.0 / float(val)

        # 重置计算结果
        self.weights = None
        self.cr = None
        self.ci = None
        self.max_eigenvalue = None

        logger.info(f"构建 {self.n}x{self.n} 判断矩阵，标签: {labels}")

    def build_matrix_from_array(
        self, labels: List[str], matrix: Union[List[List[float]], np.ndarray]
    ) -> None:
        """直接从完整矩阵构建

        Args:
            labels: 指标标签列表
            matrix: 完整的n×n判断矩阵
        """
        matrix = np.array(matrix, dtype=np.float64)

        if matrix.shape[0] != matrix.shape[1]:
            raise ValueError("判断矩阵必须是方阵")

        if len(labels) != matrix.shape[0]:
            raise ValueError("标签数量必须与矩阵维度一致")

        # 验证对角线为1
        if not np.allclose(np.diag(matrix), 1.0):
            raise ValueError("判断矩阵对角线必须为1")

        # 验证互反性
        for i in range(matrix.shape[0]):
            for j in range(i + 1, matrix.shape[1]):
                if not np.isclose(matrix[i, j] * matrix[j, i], 1.0, rtol=1e-5):
                    raise ValueError(f"矩阵不满足互反性: matrix[{i},{j}] * matrix[{j},{i}] != 1")

        self.labels = labels.copy()
        self.n = len(labels)
        self.matrix = matrix.copy()
        self.weights = None
        self.cr = None

        logger.info(f"从数组构建 {self.n}x{self.n} 判断矩阵")

    def calculate_weights(self, method: str = "eigenvalue") -> AHPResult:
        """计算权重和一致性指标

        Args:
            method: 权重计算方法，支持 "eigenvalue"（特征值法）

        Returns:
            AHPResult: 包含权重、一致性指标等的计算结果

        Raises:
            ValueError: 未构建矩阵时抛出
        """
        if self.matrix is None:
            raise ValueError("请先调用build_matrix构建判断矩阵")

        if self.n == 1:
            return self._handle_single_criterion()

        if method == "eigenvalue":
            return self._calculate_by_eigenvalue()
        else:
            raise ValueError(f"不支持的计算方法: {method}")

    def _handle_single_criterion(self) -> AHPResult:
        """处理单准则情况"""
        weights = np.array([1.0])
        result = AHPResult(
            weights=weights,
            weights_dict={self.labels[0]: 1.0},
            max_eigenvalue=1.0,
            consistency_index=0.0,
            consistency_ratio=0.0,
            random_index=0.0,
            is_consistent=True,
            status=ConsistencyStatus.PASS,
            matrix=self.matrix.copy() if self.matrix is not None else None,
        )
        self.weights = weights
        self.cr = 0.0
        self.ci = 0.0
        self.max_eigenvalue = 1.0
        return result

    def _calculate_by_eigenvalue(self) -> AHPResult:
        """使用特征值法计算权重"""
        # 特征值分解
        eigenvalues, eigenvectors = np.linalg.eig(self.matrix)

        # 找到最大特征值及其索引
        max_idx = np.argmax(eigenvalues.real)
        max_eigenvalue = eigenvalues[max_idx].real

        # 计算权重向量（最大特征值对应的特征向量归一化）
        weights = eigenvectors[:, max_idx].real
        weights = weights / np.sum(weights)

        # 计算一致性指标
        ci = (max_eigenvalue - self.n) / (self.n - 1)
        ri = AHP_RI_TABLE.get(self.n, 1.49)
        cr = ci / ri if ri > 0 else 0.0

        # 判断是否通过一致性检验
        is_consistent = cr < AHP_CONSISTENCY_THRESHOLD

        if cr < AHP_CONSISTENCY_THRESHOLD:
            status = ConsistencyStatus.PASS
        elif cr < AHP_CONSISTENCY_THRESHOLD * 2:
            status = ConsistencyStatus.WARNING
        else:
            status = ConsistencyStatus.FAIL

        # 构建结果
        weights_dict = {label: float(w) for label, w in zip(self.labels, weights)}

        result = AHPResult(
            weights=weights,
            weights_dict=weights_dict,
            max_eigenvalue=float(max_eigenvalue),
            consistency_index=float(ci),
            consistency_ratio=float(cr),
            random_index=float(ri),
            is_consistent=is_consistent,
            status=status,
            matrix=self.matrix.copy(),
            messages=self._generate_messages(cr, is_consistent),
        )

        # 保存到实例属性
        self.weights = weights
        self.max_eigenvalue = max_eigenvalue
        self.ci = ci
        self.ri = ri
        self.cr = cr

        logger.info(f"AHP计算完成: CR={cr:.4f}, " f"一致性{'通过' if is_consistent else '不通过'}")

        return result

    def _generate_messages(self, cr: float, is_consistent: bool) -> List[str]:
        """生成一致性检验信息"""
        messages = []
        if is_consistent:
            messages.append(f"一致性检验通过 (CR={cr:.4f} < {AHP_CONSISTENCY_THRESHOLD})")
        else:
            messages.append(f"一致性检验不通过 (CR={cr:.4f} >= {AHP_CONSISTENCY_THRESHOLD})")
            messages.append("建议：请重新评估判断矩阵中的比较值，或启用自动修正功能")
        return messages

    def is_consistent(self, threshold: Optional[float] = None) -> bool:
        """检查一致性是否通过

        Args:
            threshold: 一致性阈值，默认使用配置值

        Returns:
            bool: 是否通过一致性检验
        """
        if self.cr is None:
            self.calculate_weights()

        threshold = threshold or AHP_CONSISTENCY_THRESHOLD
        return self.cr < threshold

    def auto_correct_matrix(
        self, max_iterations: int = 10, correction_factor: float = 0.5
    ) -> AHPResult:
        """自动修正判断矩阵以提高一致性

        使用迭代修正算法，通过调整矩阵元素使一致性比率达标。
        修正策略：基于权重反馈调整不一致的比较值。

        Args:
            max_iterations: 最大迭代次数
            correction_factor: 修正因子，控制每次修正的幅度 (0-1)

        Returns:
            AHPResult: 修正后的计算结果

        Raises:
            ValueError: 无法收敛到可接受的一致性时抛出
        """
        if self.matrix is None:
            raise ValueError("请先构建判断矩阵")

        if self.n <= 2:
            # 2阶及以下矩阵天然一致
            return self.calculate_weights()

        original_matrix = self.matrix.copy()

        for iteration in range(max_iterations):
            result = self.calculate_weights()

            if result.is_consistent:
                logger.info(f"矩阵修正成功，迭代{iteration + 1}次后CR达标")
                result.messages.append(f"矩阵经过{iteration + 1}次迭代修正")
                return result

            # 修正矩阵
            self._apply_correction(correction_factor)
            logger.debug(f"第{iteration + 1}次修正，当前CR={result.consistency_ratio:.4f}")

        # 未能收敛，恢复原矩阵并抛出异常
        self.matrix = original_matrix
        self.weights = None
        self.cr = None

        raise ValueError(f"经过{max_iterations}次迭代仍无法达到一致性要求，" "请手动调整判断矩阵")

    def _apply_correction(self, factor: float) -> None:
        """应用矩阵修正

        基于权重向量调整判断矩阵，使其更接近完全一致矩阵。
        """
        if self.weights is None:
            return

        # 构建完全一致矩阵的理论值: a_ij = w_i / w_j
        for i in range(self.n):
            for j in range(i + 1, self.n):
                theoretical = self.weights[i] / self.weights[j]
                # 限制在1/9到9之间
                theoretical = np.clip(theoretical, 1 / 9, 9)

                # 加权修正
                current = self.matrix[i, j]
                corrected = current * (1 - factor) + theoretical * factor

                self.matrix[i, j] = corrected
                self.matrix[j, i] = 1.0 / corrected

    def get_weights_dict(self) -> Dict[str, float]:
        """获取权重字典

        Returns:
            Dict[str, float]: 标签到权重的映射
        """
        if self.weights is None:
            self.calculate_weights()
        return {label: float(w) for label, w in zip(self.labels, self.weights)}

    def get_consistency_report(self) -> Dict[str, Union[float, bool, str]]:
        """获取一致性检验报告

        Returns:
            包含一致性各项指标的字典
        """
        if self.cr is None:
            self.calculate_weights()

        return {
            "max_eigenvalue": float(self.max_eigenvalue) if self.max_eigenvalue else 0.0,
            "consistency_index": float(self.ci) if self.ci else 0.0,
            "random_index": float(self.ri) if self.ri else 0.0,
            "consistency_ratio": float(self.cr) if self.cr else 0.0,
            "threshold": AHP_CONSISTENCY_THRESHOLD,
            "is_consistent": self.is_consistent(),
            "dimension": self.n,
        }

    def sensitivity_analysis(
        self, perturbation: float = 0.1, samples: int = 100
    ) -> Dict[str, Dict[str, float]]:
        """敏感性分析

        通过随机扰动判断矩阵元素，分析权重结果的稳定性。

        Args:
            perturbation: 扰动幅度
            samples: 采样次数

        Returns:
            各指标权重的统计信息（均值、标准差、最小、最大）
        """
        if self.matrix is None or self.n <= 1:
            raise ValueError("需要至少2个准则才能进行敏感性分析")

        original_matrix = self.matrix.copy()
        weights_samples = []

        for _ in range(samples):
            # 创建扰动矩阵
            perturbed = original_matrix.copy()
            for i in range(self.n):
                for j in range(i + 1, self.n):
                    # 随机扰动
                    noise = np.random.uniform(1 - perturbation, 1 + perturbation)
                    new_val = np.clip(perturbed[i, j] * noise, 1 / 9, 9)
                    perturbed[i, j] = new_val
                    perturbed[j, i] = 1.0 / new_val

            self.matrix = perturbed
            self.weights = None

            try:
                result = self.calculate_weights()
                weights_samples.append(result.weights)
            except Exception:
                continue

        # 恢复原矩阵
        self.matrix = original_matrix
        self.weights = None

        if not weights_samples:
            raise ValueError("敏感性分析失败，没有有效样本")

        # 统计各权重的稳定性
        weights_array = np.array(weights_samples)
        stats = {}
        for i, label in enumerate(self.labels):
            stats[label] = {
                "mean": float(np.mean(weights_array[:, i])),
                "std": float(np.std(weights_array[:, i])),
                "min": float(np.min(weights_array[:, i])),
                "max": float(np.max(weights_array[:, i])),
                "cv": (
                    float(np.std(weights_array[:, i]) / np.mean(weights_array[:, i]))
                    if np.mean(weights_array[:, i]) > 0
                    else 0
                ),
            }

        return stats

    def reset(self) -> None:
        """重置引擎状态"""
        self.matrix = None
        self.labels = []
        self.n = 0
        self.weights = None
        self.cr = None
        self.ci = None
        self.max_eigenvalue = None
        self.ri = None
        logger.debug("AHP引擎已重置")
