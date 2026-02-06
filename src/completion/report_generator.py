"""报告生成器

生成 Markdown 格式的 ESG 分析报告，包含评分、差距分析和改进建议。
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

from src.core.models import ESGMetrics, AnalysisResult
from src.config import ESG_DIMENSION_NAMES, ESG_COLORS, GAP_THRESHOLD_HIGH, GAP_THRESHOLD_MEDIUM


class ReportGenerator:
    """ESG报告生成器
    
    用于生成标准化的 Markdown 格式 ESG 分析报告。报告包含：
    - 公司基本信息和总体评分
    - 各维度（E/S/G）详细得分和权重
    - 与行业基准的差距分析
    - 针对性的改进建议
    - 数据质量评估
    
    Attributes:
        template_dir: 自定义模板目录（可选）
        include_charts: 是否在报告中包含图表占位符
    """
    
    def __init__(
        self, 
        template_dir: Optional[str] = None,
        include_charts: bool = False
    ):
        """初始化报告生成器
        
        Args:
            template_dir: 自定义 Markdown 模板目录
            include_charts: 是否在报告中添加图表占位符
        """
        self.template_dir = Path(template_dir) if template_dir else None
        self.include_charts = include_charts
    
    def generate(
        self, 
        result: AnalysisResult,
        benchmark_scores: Optional[Dict[str, float]] = None
    ) -> str:
        """生成 Markdown 格式 ESG 报告
        
        根据分析结果生成完整的 ESG 评估报告。
        
        Args:
            result: ESG 分析结果对象
            benchmark_scores: 行业基准分数 {"E": score, "S": score, "G": score}
            
        Returns:
            Markdown 格式的报告文本
            
        Example:
            >>> generator = ReportGenerator()
            >>> report_md = generator.generate(analysis_result)
            >>> print(report_md)
        """
        metrics = result.metrics
        lines: List[str] = []
        
        # 报告标题
        lines.extend(self._generate_header(metrics))
        
        # 执行摘要
        lines.extend(self._generate_executive_summary(result))
        
        # 总体评分
        lines.extend(self._generate_overall_score(result))
        
        # 各维度详细分析
        lines.extend(self._generate_dimension_details(result))
        
        # 差距分析
        lines.extend(self._generate_gap_analysis(result, benchmark_scores))
        
        # 改进建议
        lines.extend(self._generate_recommendations(result))
        
        # 数据质量评估
        lines.extend(self._generate_data_quality(result))
        
        # 附录
        lines.extend(self._generate_appendix(result))
        
        return "\n".join(lines)
    
    def save(
        self, 
        result: AnalysisResult, 
        output_dir: str = "reports",
        filename: Optional[str] = None,
        benchmark_scores: Optional[Dict[str, float]] = None
    ) -> str:
        """保存报告到文件
        
        生成报告并保存到指定目录。
        
        Args:
            result: ESG 分析结果
            output_dir: 输出目录路径
            filename: 自定义文件名，None 则使用默认命名
            benchmark_scores: 行业基准分数
            
        Returns:
            保存的文件路径
        """
        # 确保输出目录存在
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        if filename is None:
            safe_company_name = "".join(
                c if c.isalnum() or c in (' ', '-', '_') else '_'
                for c in result.metrics.company_name
            ).strip()
            filename = f"{safe_company_name}_ESG报告_{result.metrics.year}_{datetime.now().strftime('%Y%m%d')}.md"
        
        filepath = output_path / filename
        
        # 生成并保存报告
        content = self.generate(result, benchmark_scores)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        return str(filepath)
    
    def _generate_header(self, metrics: ESGMetrics) -> List[str]:
        """生成报告标题部分
        
        Args:
            metrics: ESG 指标数据
            
        Returns:
            Markdown 标题行列表
        """
        return [
            f"# {metrics.company_name} ESG 分析报告",
            "",
            "---",
            "",
            "## 基本信息",
            "",
            f"| 项目 | 内容 |",
            f"|------|------|",
            f"| **公司名称** | {metrics.company_name} |",
            f"| **数据年份** | {metrics.year} |",
            f"| **报告生成时间** | {datetime.now().strftime('%Y年%m月%d日 %H:%M')} |",
            f"| **数据来源** | {metrics.source or '企业披露'} |",
            "",
            "---",
            ""
        ]
    
    def _generate_executive_summary(self, result: AnalysisResult) -> List[str]:
        """生成执行摘要
        
        Args:
            result: 分析结果
            
        Returns:
            Markdown 行列表
        """
        score = result.overall_score
        
        # 根据分数确定评级
        if score >= 80:
            rating = "优秀"
            rating_desc = "公司在 ESG 方面表现卓越，具有明显的可持续发展优势。"
        elif score >= 60:
            rating = "良好"
            rating_desc = "公司在 ESG 方面有较好表现，仍有提升空间。"
        elif score >= 40:
            rating = "一般"
            rating_desc = "公司在 ESG 方面表现一般，需要制定明确的改进计划。"
        else:
            rating = "需改进"
            rating_desc = "公司在 ESG 方面存在明显不足，急需采取行动。"
        
        lines = [
            "## 执行摘要",
            "",
            f"**总体评级**: {rating} ({result.overall_score:.1f}/100)",
            "",
            f"> {rating_desc}",
            "",
            "### 关键发现",
            ""
        ]
        
        # 找出最强和最弱的维度
        dimension_scores = {
            "E": result.metrics.get_dimension_score("E"),
            "S": result.metrics.get_dimension_score("S"),
            "G": result.metrics.get_dimension_score("G")
        }
        best_dim = max(dimension_scores, key=dimension_scores.get)
        worst_dim = min(dimension_scores, key=dimension_scores.get)
        
        lines.extend([
            f"- **优势维度**: {ESG_DIMENSION_NAMES[best_dim]} ({dimension_scores[best_dim]:.1f}分)",
            f"- **待改进维度**: {ESG_DIMENSION_NAMES[worst_dim]} ({dimension_scores[worst_dim]:.1f}分)",
            f"- **数据置信度**: {result.confidence_level}",
            f"- **改进建议数**: {len(result.strategies)} 项",
            "",
            "---",
            ""
        ])
        
        return lines
    
    def _generate_overall_score(self, result: AnalysisResult) -> List[str]:
        """生成总体评分部分
        
        Args:
            result: 分析结果
            
        Returns:
            Markdown 行列表
        """
        lines = [
            "## 总体评分",
            "",
            f"### ESG 综合得分: {result.overall_score:.1f}/100",
            "",
            "```",
            f"得分分布: {'█' * int(result.overall_score / 5)}{'░' * (20 - int(result.overall_score / 5))}",
            "```",
            "",
            "### 各维度得分明细",
            "",
            "| 维度 | 名称 | 权重 | 得分 | 加权得分 |",
            "|:----:|------|:----:|:----:|:--------:|"
        ]
        
        for dim in ["E", "S", "G"]:
            score = result.metrics.get_dimension_score(dim)
            weight = result.weights.get(dim, 0)
            weighted = score * weight
            dim_name = ESG_DIMENSION_NAMES[dim]
            lines.append(f"| **{dim}** | {dim_name} | {weight:.0%} | {score:.1f} | {weighted:.1f} |")
        
        lines.extend([
            "",
            f"**加权总分**: {result.overall_score:.1f}",
            "",
            "---",
            ""
        ])
        
        return lines
    
    def _generate_dimension_details(self, result: AnalysisResult) -> List[str]:
        """生成各维度详细分析
        
        Args:
            result: 分析结果
            
        Returns:
            Markdown 行列表
        """
        lines = ["## 维度详细分析", ""]
        
        metrics = result.metrics
        
        # 环境维度 (E)
        lines.extend([
            f"### E - 环境 ({ESG_DIMENSION_NAMES['E']})",
            "",
            f"**维度得分**: {metrics.get_dimension_score('E'):.1f}",
            "",
            "| 指标 | 数值 | 单位 |",
            "|------|------|------|",
            f"| 碳排放量 | {metrics.carbon_emissions or 'N/A'} | 吨CO₂ |",
            f"| 可再生能源占比 | {metrics.renewable_energy_ratio or 'N/A'} | % |",
            f"| 能源效率 | {metrics.energy_efficiency or 'N/A'} | % |",
            f"| 用水量 | {metrics.water_consumption or 'N/A'} | 立方米 |",
            f"| 废物回收率 | {metrics.waste_recycling_rate or 'N/A'} | % |",
            "",
        ])
        
        # 社会维度 (S)
        lines.extend([
            f"### S - 社会 ({ESG_DIMENSION_NAMES['S']})",
            "",
            f"**维度得分**: {metrics.get_dimension_score('S'):.1f}",
            "",
            "| 指标 | 数值 | 单位 |",
            "|------|------|------|",
            f"| 员工总数 | {metrics.employee_count or 'N/A'} | 人 |",
            f"| 女性员工比例 | {metrics.female_ratio or 'N/A'} | % |",
            f"| 人均培训时长 | {metrics.training_hours or 'N/A'} | 小时 |",
            f"| 安全事故数 | {metrics.safety_incidents or 'N/A'} | 起 |",
            f"| 社区投资 | {metrics.community_investment or 'N/A'} | 元 |",
            "",
        ])
        
        # 治理维度 (G)
        lines.extend([
            f"### G - 治理 ({ESG_DIMENSION_NAMES['G']})",
            "",
            f"**维度得分**: {metrics.get_dimension_score('G'):.1f}",
            "",
            "| 指标 | 数值 | 单位 |",
            "|------|------|------|",
            f"| 董事会独立性 | {metrics.board_independence_ratio or 'N/A'} | % |",
            f"| 道德培训覆盖率 | {metrics.ethics_training_coverage or 'N/A'} | % |",
            f"| ESG报告质量 | {metrics.esg_report_quality or 'N/A'} | 分 |",
            "",
            "---",
            ""
        ])
        
        return lines
    
    def _generate_gap_analysis(
        self, 
        result: AnalysisResult,
        benchmark_scores: Optional[Dict[str, float]] = None
    ) -> List[str]:
        """生成差距分析部分
        
        Args:
            result: 分析结果
            benchmark_scores: 行业基准分数
            
        Returns:
            Markdown 行列表
        """
        lines = ["## 差距分析", ""]
        
        # 使用分析结果中的差距数据
        gap_analysis = result.gap_analysis.get("dimensions", {})
        
        lines.extend([
            "### 与目标差距",
            "",
            "| 维度 | 当前得分 | 目标得分 | 差距 | 状态 |",
            "|:----:|:--------:|:--------:|:----:|:----:|:--|"
        ])
        
        for dim in ["E", "S", "G"]:
            gap_data = gap_analysis.get(dim, {})
            current = gap_data.get("current", result.metrics.get_dimension_score(dim))
            target = gap_data.get("target", 80.0)
            gap = gap_data.get("gap", target - current)
            
            # 确定状态
            if gap <= 0:
                status = "✅ 达标"
            elif gap <= GAP_THRESHOLD_MEDIUM:
                status = "🟡 轻微"
            elif gap <= GAP_THRESHOLD_HIGH:
                status = "🟠 中等"
            else:
                status = "🔴 严重"
            
            lines.append(f"| **{dim}** | {current:.1f} | {target:.1f} | {gap:.1f} | {status} |")
        
        lines.append("")
        
        # 与行业基准对比
        if benchmark_scores:
            lines.extend([
                "### 与行业基准对比",
                "",
                "| 维度 | 公司得分 | 行业平均 | 差异 |",
                "|:----:|:--------:|:--------:|:----:|:--|"
            ])
            
            for dim in ["E", "S", "G"]:
                company_score = result.metrics.get_dimension_score(dim)
                benchmark = benchmark_scores.get(dim, 0)
                diff = company_score - benchmark
                diff_str = f"+{diff:.1f}" if diff > 0 else f"{diff:.1f}"
                indicator = "🟢 领先" if diff > 5 else ("🔴 落后" if diff < -5 else "⚪ 持平")
                
                lines.append(f"| **{dim}** | {company_score:.1f} | {benchmark:.1f} | {diff_str} | {indicator} |")
            
            lines.append("")
        
        lines.extend(["---", ""])
        return lines
    
    def _generate_recommendations(self, result: AnalysisResult) -> List[str]:
        """生成改进建议部分
        
        Args:
            result: 分析结果
            
        Returns:
            Markdown 行列表
        """
        lines = [
            "## 改进建议",
            "",
            f"基于差距分析，我们为公司制定了 **{len(result.strategies)}** 项改进建议：",
            ""
        ]
        
        # 按优先级排序
        priority_order = {"高": 0, "中": 1, "低": 2}
        sorted_strategies = sorted(
            result.strategies,
            key=lambda x: priority_order.get(x.get("priority", "中"), 1)
        )
        
        for i, strategy in enumerate(sorted_strategies, 1):
            dim = strategy.get("dimension", "")
            title = strategy.get("title", "")
            priority = strategy.get("priority", "中")
            actions = strategy.get("actions", [])
            
            priority_emoji = {"高": "🔴", "中": "🟡", "低": "🟢"}.get(priority, "⚪")
            
            lines.extend([
                f"### {i}. {title}",
                "",
                f"- **涉及维度**: {ESG_DIMENSION_NAMES.get(dim, dim)}",
                f"- **优先级**: {priority_emoji} {priority}",
                "",
                "**具体行动项**:",
                ""
            ])
            
            for action in actions:
                lines.append(f"- [ ] {action}")
            
            lines.append("")
        
        lines.extend(["---", ""])
        return lines
    
    def _generate_data_quality(self, result: AnalysisResult) -> List[str]:
        """生成数据质量评估部分
        
        Args:
            result: 分析结果
            
        Returns:
            Markdown 行列表
        """
        lines = [
            "## 数据质量评估",
            "",
            f"- **整体置信度**: {result.confidence_level}",
            ""
        ]
        
        # 统计各维度数据完整性
        metrics = result.metrics
        dimension_completeness = {}
        
        e_fields = [metrics.carbon_emissions, metrics.renewable_energy_ratio, 
                   metrics.energy_efficiency, metrics.water_consumption, metrics.waste_recycling_rate]
        s_fields = [metrics.employee_count, metrics.female_ratio, 
                   metrics.training_hours, metrics.safety_incidents, metrics.community_investment]
        g_fields = [metrics.board_independence_ratio, metrics.ethics_training_coverage, metrics.esg_report_quality]
        
        dimension_completeness["E"] = sum(1 for f in e_fields if f is not None) / len(e_fields)
        dimension_completeness["S"] = sum(1 for f in s_fields if f is not None) / len(s_fields)
        dimension_completeness["G"] = sum(1 for f in g_fields if f is not None) / len(g_fields)
        
        lines.extend([
            "### 数据完整度",
            "",
            "| 维度 | 完整度 | 可视化 |",
            "|:----:|:------:|--------|"
        ])
        
        for dim in ["E", "S", "G"]:
            completeness = dimension_completeness[dim]
            bar = "█" * int(completeness * 10) + "░" * (10 - int(completeness * 10))
            lines.append(f"| **{dim}** | {completeness:.0%} | {bar} |")
        
        lines.append("")
        
        # 数据质量警告
        if result.data_quality_warnings:
            lines.extend([
                "### ⚠️ 数据质量警告",
                "",
            ])
            for warning in result.data_quality_warnings:
                lines.append(f"- {warning}")
            lines.append("")
        
        lines.extend(["---", ""])
        return lines
    
    def _generate_appendix(self, result: AnalysisResult) -> List[str]:
        """生成附录部分
        
        Args:
            result: 分析结果
            
        Returns:
            Markdown 行列表
        """
        return [
            "## 附录",
            "",
            "### 评分方法说明",
            "",
            "本报告采用加权评分法，各维度权重可在配置中调整：",
            "- **环境(E)**: 反映企业在气候变化、资源利用、污染控制方面的表现",
            "- **社会(S)**: 反映企业在员工权益、社区关系、产品责任方面的表现",
            "- **治理(G)**: 反映企业在公司治理、商业道德、信息披露方面的表现",
            "",
            "### 数据来源",
            "",
            f"- 企业ESG报告: {result.metrics.source or '未指定'}",
            f"- 数据提取时间: {result.metrics.extracted_at}",
            "",
            "---",
            "",
            f"*报告由 ESG 分析系统自动生成 - {datetime.now().strftime('%Y-%m-%d')}*",
            ""
        ]
