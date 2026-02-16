"""报告生成器

生成 Markdown 格式的 ESG 分析报告，包含评分、差距分析和改进建议。
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.esg.analysis.business_mapper import BusinessAlignmentMapper
from src.esg.analysis.competitor_analyzer import CompetitorAnalyzer
from src.esg.config import (
    ESG_COLORS,
    ESG_DIMENSION_NAMES,
    GAP_THRESHOLD_HIGH,
    GAP_THRESHOLD_MEDIUM,
    REQUIREMENT_MANDATORY,
)
from src.esg.core.compliance_checker import ComplianceChecker
from src.esg.core.models import AnalysisResult, ESGMetrics
from src.esg.extraction.multilingual import (
    Language,
    MultilingualReportGenerator,
    generate_multilingual_report,
)


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
        include_charts: bool = False,
        include_compliance: bool = True,
    ):
        """初始化报告生成器

        Args:
            template_dir: 自定义 Markdown 模板目录
            include_charts: 是否在报告中添加图表占位符
            include_compliance: 是否包含合规性检查部分
        """
        self.template_dir = Path(template_dir) if template_dir else None
        self.include_charts = include_charts
        self.include_compliance = include_compliance
        self.compliance_checker = ComplianceChecker()

    def generate(
        self, result: AnalysisResult, benchmark_scores: Optional[Dict[str, float]] = None
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

        # 执行摘要（包含合规率进度条）
        lines.extend(self._generate_executive_summary(result))

        # 国际标准合规检查
        if self.include_compliance:
            lines.extend(self._generate_compliance_section(result))

        # 总体评分
        lines.extend(self._generate_overall_score(result))

        # 各维度详细分析
        lines.extend(self._generate_dimension_details(result))

        # 差距分析
        lines.extend(self._generate_gap_analysis(result, benchmark_scores))

        # 竞争情报分析
        lines.extend(self._generate_competitive_intelligence(result, benchmark_scores))

        # 分业务ESG风险矩阵
        lines.extend(self._generate_business_risk_matrix())

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
        benchmark_scores: Optional[Dict[str, float]] = None,
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
                c if c.isalnum() or c in (" ", "-", "_") else "_"
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
            "",
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

        # 计算合规率
        compliance_rate = 0.0
        if self.include_compliance:
            compliance_rate = self.compliance_checker.get_compliance_rate(result.metrics)

        lines = [
            "## 执行摘要",
            "",
            f"**总体评级**: {rating} ({result.overall_score:.1f}/100)",
            "",
            f"> {rating_desc}",
            "",
            "### 关键发现",
            "",
        ]

        # 找出最强和最弱的维度
        dimension_scores = {
            "E": result.metrics.get_dimension_score("E"),
            "S": result.metrics.get_dimension_score("S"),
            "G": result.metrics.get_dimension_score("G"),
        }
        best_dim = max(dimension_scores, key=dimension_scores.get)
        worst_dim = min(dimension_scores, key=dimension_scores.get)

        lines.extend(
            [
                f"- **优势维度**: {ESG_DIMENSION_NAMES[best_dim]} ({dimension_scores[best_dim]:.1f}分)",
                f"- **待改进维度**: {ESG_DIMENSION_NAMES[worst_dim]} ({dimension_scores[worst_dim]:.1f}分)",
                f"- **数据置信度**: {result.confidence_level}",
                f"- **改进建议数**: {len(result.strategies)} 项",
            ]
        )

        # 添加合规率进度条
        if self.include_compliance:
            lines.extend(
                [
                    f"- **国际标准合规率**: {compliance_rate:.1%}",
                    "",
                    "#### 合规率进度",
                    "",
                    self._generate_compliance_progress_bar(compliance_rate),
                    "",
                ]
            )

        lines.extend(["", "---", ""])

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
            "|:----:|------|:----:|:----:|:--------:|",
        ]

        for dim in ["E", "S", "G"]:
            score = result.metrics.get_dimension_score(dim)
            weight = result.weights.get(dim, 0)
            weighted = score * weight
            dim_name = ESG_DIMENSION_NAMES[dim]
            lines.append(
                f"| **{dim}** | {dim_name} | {weight:.0%} | {score:.1f} | {weighted:.1f} |"
            )

        lines.extend(["", f"**加权总分**: {result.overall_score:.1f}", "", "---", ""])

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
        lines.extend(
            [
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
            ]
        )

        # 社会维度 (S)
        lines.extend(
            [
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
            ]
        )

        # 治理维度 (G)
        lines.extend(
            [
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
                "",
            ]
        )

        return lines

    def _generate_gap_analysis(
        self, result: AnalysisResult, benchmark_scores: Optional[Dict[str, float]] = None
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

        lines.extend(
            [
                "### 与目标差距",
                "",
                "| 维度 | 当前得分 | 目标得分 | 差距 | 状态 |",
                "|:----:|:--------:|:--------:|:----:|:----:|:--|",
            ]
        )

        for dim in ["E", "S", "G"]:
            gap_data = gap_analysis.get(dim, {})

            # 修复：处理 GapResult 对象或 dict 的情况
            if hasattr(gap_data, "current"):
                # GapResult 对象
                current = gap_data.current
                target = gap_data.benchmark
                gap = gap_data.gap
            else:
                # dict 对象
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
            lines.extend(
                [
                    "### 与行业基准对比",
                    "",
                    "| 维度 | 公司得分 | 行业平均 | 差异 |",
                    "|:----:|:--------:|:--------:|:----:|:--|",
                ]
            )

            for dim in ["E", "S", "G"]:
                company_score = result.metrics.get_dimension_score(dim)
                benchmark = benchmark_scores.get(dim, 0)
                diff = company_score - benchmark
                diff_str = f"+{diff:.1f}" if diff > 0 else f"{diff:.1f}"
                indicator = "🟢 领先" if diff > 5 else ("🔴 落后" if diff < -5 else "⚪ 持平")

                lines.append(
                    f"| **{dim}** | {company_score:.1f} | {benchmark:.1f} | {diff_str} | {indicator} |"
                )

            lines.append("")

        lines.extend(["---", ""])
        return lines

    def _generate_business_risk_matrix(self) -> List[str]:
        """生成分业务ESG风险矩阵

        展示各业务单元与ESG议题的关联影响矩阵。

        优化：预计算所有数据，避免循环中重复排序。

        Returns:
            Markdown 行列表
        """
        lines = [
            "## 分业务ESG风险矩阵",
            "",
            "> 本章节展示各业务单元面临的ESG风险分布，帮助识别关键业务领域和改进优先级。",
            "",
        ]

        try:
            mapper = BusinessAlignmentMapper()
            matrix_data = mapper.get_risk_matrix_data()
            topic_summary = mapper.get_topic_summary_by_unit()

            # 预计算：一次性获取所有需要的数据
            # 影响等级emoji映射（常量提取到循环外）
            impact_emoji_map = {"高": "🔴", "中": "🟡", "低": "🟢", "": "⚪"}

            # 汇总统计
            lines.extend(
                [
                    "### 业务单元风险概览",
                    "",
                    "| 业务单元 | 高风险议题 | 中风险议题 | 低风险议题 | 总计 |",
                    "|:---------|:----------:|:----------:|:----------:|:----:|",
                ]
            )

            # 按高风险数量排序（只排序一次）
            sorted_units = sorted(topic_summary.items(), key=lambda x: x[1]["高"], reverse=True)

            for unit_name, summary in sorted_units:
                lines.append(
                    f"| **{unit_name}** | "
                    f"{summary['高']} | "
                    f"{summary['中']} | "
                    f"{summary['低']} | "
                    f"{summary['总计']} |"
                )

            lines.append("")

            # 详细风险矩阵
            lines.extend(
                [
                    "### 业务-议题风险映射表",
                    "",
                    "以下表格展示各业务单元与ESG议题的关联影响等级：",
                    "- 🔴 高影响：该议题对业务单元具有重大影响",
                    "- 🟡 中影响：该议题对业务单元具有中等影响",
                    "- 🟢 低影响：该议题对业务单元影响较小",
                    "",
                ]
            )

            # 预计算：一次性获取所有议题名称（避免重复构建）
            all_topic_names = {}
            for row in matrix_data:
                for topic_id, topic_info in row["topics"].items():
                    if topic_id not in all_topic_names:
                        all_topic_names[topic_id] = topic_info["name"]

            # 构建表格表头（只构建一次）
            topic_ids = list(all_topic_names.keys())[:8]  # 限制显示前8个议题
            header = (
                "| 业务单元 | " + " | ".join([all_topic_names[tid] for tid in topic_ids]) + " |"
            )
            separator = "|:---------|" + "|".join([":" for _ in topic_ids]) + "|"

            lines.extend([header, separator])

            # 填充数据行（使用预计算的映射）
            for row in matrix_data:
                unit_name = row["business_unit"]
                cells = [f"**{unit_name}**"]

                for topic_id in topic_ids:
                    if topic_id in row["topics"]:
                        impact = row["topics"][topic_id]["impact"]
                        cells.append(impact_emoji_map.get(impact, "⚪"))
                    else:
                        cells.append("—")

                lines.append("| " + " | ".join(cells) + " |")

            lines.append("")

            # 各业务单元TOP风险
            lines.extend(
                [
                    "### 各业务单元TOP 3 ESG风险",
                    "",
                ]
            )

            # 预计算：一次性获取所有TOP风险（避免重复查询）
            top_risks_cache = {}
            for unit_name in mapper.business_units:
                top_risks_cache[unit_name] = mapper.get_top_risks_for_unit(unit_name, top_n=3)

            # 使用缓存渲染
            for unit_name in mapper.business_units:
                top_risks = top_risks_cache[unit_name]
                if top_risks:
                    lines.append(f"#### {unit_name}")
                    lines.append("")

                    for i, risk in enumerate(top_risks, 1):
                        dim_name = ESG_DIMENSION_NAMES.get(risk["dimension"], risk["dimension"])
                        emoji = impact_emoji_map.get(risk["impact_level"], "⚪")
                        lines.append(
                            f"{i}. **{risk['topic_name']}** ({dim_name}) {emoji} {risk['impact_level']}影响"
                        )

                    lines.append("")

            lines.extend(["---", ""])

        except Exception as e:
            lines.append(f"> 风险矩阵生成失败: {e}")
            lines.append("")

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
            "",
        ]

        # 按优先级排序
        priority_order = {"高": 0, "中": 1, "低": 2}
        sorted_strategies = sorted(
            result.strategies, key=lambda x: priority_order.get(x.get("priority", "中"), 1)
        )

        for i, strategy in enumerate(sorted_strategies, 1):
            dim = strategy.get("dimension", "")
            title = strategy.get("title", "")
            priority = strategy.get("priority", "中")
            actions = strategy.get("actions", [])
            channels = strategy.get("recommended_channels", [])

            priority_emoji = {"高": "🔴", "中": "🟡", "低": "🟢"}.get(priority, "⚪")

            lines.extend(
                [
                    f"### {i}. {title}",
                    "",
                    f"- **涉及维度**: {ESG_DIMENSION_NAMES.get(dim, dim)}",
                    f"- **优先级**: {priority_emoji} {priority}",
                    "",
                    "**具体行动项**:",
                    "",
                ]
            )

            for action in actions:
                lines.append(f"- [ ] {action}")

            # 添加推荐披露渠道
            if channels:
                lines.extend(["", "**推荐披露渠道**:", ""])
                for channel in channels:
                    channel_name = channel.get("channel_name", "")
                    reason = channel.get("reason", "")
                    priority_label = channel.get("priority", "")
                    priority_badge = "【主渠道】" if priority_label == "主渠道" else "【辅助渠道】"
                    lines.append(f"- **{channel_name}**{priority_badge}：{reason}")

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
        lines = ["## 数据质量评估", "", f"- **整体置信度**: {result.confidence_level}", ""]

        # 统计各维度数据完整性
        metrics = result.metrics
        dimension_completeness = {}

        # ===== 环境维度 (E) - 16个核心指标 =====
        e_fields = [
            metrics.carbon_intensity,
            metrics.scope3_coverage_percentage,
            metrics.sbti_target,
            metrics.renewable_energy_ratio,
            metrics.energy_efficiency,
            metrics.waste_recycling_rate,
            metrics.water_intensity,
            metrics.turbine_availability,
            metrics.curtailment_rate,
            metrics.battery_cycle_life,
            metrics.battery_recycling_rate,
            metrics.electrolysis_efficiency,
            metrics.energy_storage_safety_score,
            metrics.carbon_emissions,
            metrics.scope1_emissions,
            metrics.scope2_emissions_location,
        ]

        # ===== 社会维度 (S) - 11个核心指标 =====
        s_fields = [
            metrics.female_ratio,
            metrics.female_executive_ratio,
            metrics.training_hours,
            metrics.training_investment_per_employee,
            metrics.employee_count,
            metrics.trir,
            metrics.ltifr if metrics.ltifr is not None else metrics.lost_time_injury_rate,
            metrics.safety_investment_ratio,
            metrics.safety_incidents,
            metrics.community_investment_per_revenue,
            metrics.local_employment_ratio,
            metrics.community_investment,
        ]

        # ===== 治理维度 (G) - 9个核心指标 =====
        g_fields = [
            metrics.board_independence_ratio,
            metrics.esg_committee_independence,
            metrics.ethics_training_coverage,
            metrics.anti_corruption_training_coverage,
            metrics.whistleblower_protection,
            getattr(metrics, "climate_governance", None),
            getattr(metrics, "tcfd_disclosure", None),
            metrics.esg_report_quality,
            metrics.esg_committee_independence,
        ]

        dimension_completeness["E"] = sum(1 for f in e_fields if f is not None) / len(e_fields)
        dimension_completeness["S"] = sum(1 for f in s_fields if f is not None) / len(s_fields)
        dimension_completeness["G"] = sum(1 for f in g_fields if f is not None) / len(g_fields)

        lines.extend(
            [
                "### 数据完整度",
                "",
                "| 维度 | 检查项 | 完整度 | 可视化 |",
                "|:----:|:------:|:------:|--------|",
            ]
        )

        for dim, field_count in [("E", len(e_fields)), ("S", len(s_fields)), ("G", len(g_fields))]:
            completeness = dimension_completeness[dim]
            bar = "█" * int(completeness * 10) + "░" * (10 - int(completeness * 10))
            lines.append(f"| **{dim}** | {field_count}项 | {completeness:.0%} | {bar} |")

        lines.append("")

        # 数据质量警告
        if result.data_quality_warnings:
            lines.extend(
                [
                    "### ⚠️ 数据质量警告",
                    "",
                ]
            )
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
            "### 合规标准说明",
            "",
            "本报告依据以下国际标准进行合规检查：",
            "- **ISSB S1**: 国际可持续发展准则理事会可持续发展相关财务信息披露一般要求",
            "- **ISSB S2**: 国际可持续发展准则理事会气候相关披露标准",
            "- **GRI Standards**: 全球报告倡议组织可持续发展报告标准（2021版）",
            "",
            "### 数据来源",
            "",
            f"- 企业ESG报告: {result.metrics.source or '未指定'}",
            f"- 数据提取时间: {result.metrics.extracted_at}",
            "",
            "---",
            "",
            f"*报告由 ESG 分析系统自动生成 - {datetime.now().strftime('%Y-%m-%d')}*",
            "",
        ]

    def _generate_compliance_progress_bar(self, rate: float, width: int = 30) -> str:
        """生成合规率ASCII进度条

        Args:
            rate: 合规率 (0-1)
            width: 进度条宽度

        Returns:
            进度条字符串
        """
        filled = int(rate * width)
        empty = width - filled
        bar = "█" * filled + "░" * empty
        return f"```\n[{bar}] {rate:.1%}\n```"

    def _generate_competitive_intelligence(
        self, result: AnalysisResult, benchmark_scores: Optional[Dict[str, float]] = None
    ) -> List[str]:
        """生成竞争情报分析部分

        基于行业最佳实践数据，生成深度对标分析和竞争情报。

        Args:
            result: 分析结果
            benchmark_scores: 行业基准分数

        Returns:
            Markdown 行列表
        """
        lines = [
            "## 竞争情报分析",
            "",
            "> 本章节基于行业最佳实践数据，对贵司与标杆企业进行深度对标分析。",
            "",
        ]

        try:
            analyzer = CompetitorAnalyzer()
            metrics = result.metrics

            # 确定标杆企业（优先使用维斯塔斯或西门子歌美飒）
            benchmark = "行业平均"
            available_competitors = analyzer.get_competitor_list()
            for comp in available_competitors:
                if comp in ["维斯塔斯", "西门子歌美飒"]:
                    benchmark = comp
                    break

            # 准备差距数据 - 优先使用分析结果中的差距数据
            gap_data = {}
            if result.gap_analysis and "dimensions" in result.gap_analysis:
                gap_data = result.gap_analysis["dimensions"]
            else:
                # 如果没有差距分析数据，计算得分差距
                scores = metrics.get_all_dimension_scores()
                for dim in ["E", "S", "G"]:
                    current = scores.get(dim, 0)
                    target = benchmark_scores.get(dim, 80) if benchmark_scores else 80
                    gap_data[dim] = {"current": current, "target": target, "gap": target - current}

            # 生成深度分析（文字分析）
            lines.extend(
                [
                    "### 📊 深度对标分析",
                    "",
                ]
            )

            analysis_text = analyzer.generate_analysis(metrics, benchmark, gap_data)
            # 将分析文本分段显示，增强可读性
            for paragraph in analysis_text.split("\n\n"):
                if paragraph.strip():
                    lines.append(f"> {paragraph.strip()}")
                    lines.append("")

            # 生成对比表格（三列：我司现状、标杆做法、差距与机会）
            lines.extend(
                [
                    "### 📋 三维度对比详情",
                    "",
                    "**对比维度说明**：",
                    "- **我司现状**：当前企业在该维度的得分",
                    "- **标杆做法**：标杆企业在该维度的最佳实践经验",
                    "- **差距与机会**：包含差距分值、改进机会和优先级评估",
                    "",
                    "| 维度 | 我司现状 | 标杆做法 | 差距与机会 |",
                    "|:----:|:--------:|:---------|:-----------|",
                ]
            )

            comparison_table = analyzer.generate_comparison_table(metrics, benchmark, gap_data)

            for row in comparison_table:
                # 提取差距数值用于高亮
                gap_str = row["差距"].replace("+", "").replace("分", "")
                try:
                    gap_val = float(gap_str)
                    gap_display = (
                        f"**{row['差距']}** 📉"
                        if gap_val > 10
                        else f"{row['差距']} 📊" if gap_val > 5 else f"{row['差距']} ✅"
                    )
                except (ValueError, TypeError):
                    gap_display = row["差距"]

                # 组合差距与机会列的内容
                gap_opportunity = f"{gap_display}<br>{row['改进机会']}<br>优先级: {row['优先级']}"

                lines.append(
                    f"| **{row['维度']}** | {row['我司现状']} | {row['标杆做法']} | {gap_opportunity} |"
                )

            lines.append("")

            # 标杆企业创新亮点
            lines.extend(
                [
                    f"### 💡 {benchmark} 创新亮点",
                    "",
                ]
            )

            highlights = analyzer.get_innovation_highlights(benchmark)
            if highlights:
                for highlight in highlights:
                    lines.append(f"- {highlight}")
            else:
                lines.append("- 暂无创新亮点数据")

            lines.append("")

            # 整体对比排名
            lines.extend(
                [
                    "### 🏆 行业排名对比",
                    "",
                ]
            )

            overall_comparison = analyzer.get_overall_comparison(metrics)
            current_rank = overall_comparison["current_company"]

            lines.append(f"**贵司综合评分**: {current_rank['overall_score']}分")
            lines.append("")
            lines.append("| 企业 | 综合评分 | 环境(E) | 社会(S) | 治理(G) | 排名 |")
            lines.append("|:-----|:--------:|:-------:|:-------:|:-------:|:----:|")

            # 添加当前企业
            rank_badge = f"**#{current_rank['rank']}** / {current_rank['total_companies']}"
            lines.append(
                f"| **{current_rank['name']}** | **{current_rank['overall_score']}** | "
                f"{current_rank['e_score']} | {current_rank['s_score']} | {current_rank['g_score']} | {rank_badge} |"
            )

            # 添加竞争对手
            for comp in overall_comparison["competitors"][:3]:  # 只显示前3个
                lines.append(f"| {comp['name']} | {comp['overall_score']} | - | - | - | - |")

            lines.append("")

            # 添加行动建议总结
            lines.extend(
                [
                    "### 🎯 基于竞争情报的行动建议",
                    "",
                    "根据上述深度对标分析，建议贵司：",
                    "",
                ]
            )

            # 找出差距最大的维度
            max_gap_dim = None
            max_gap_value = 0
            for dim in ["E", "S", "G"]:
                gap_val = gap_data.get(dim, {}).get("gap", 0)
                if gap_val > max_gap_value:
                    max_gap_value = gap_val
                    max_gap_dim = dim

            if max_gap_dim and max_gap_value > 10:
                dim_name = ESG_DIMENSION_NAMES.get(max_gap_dim, max_gap_dim)
                lines.append(
                    f"1. **优先改进{dim_name}维度**：差距达{max_gap_value:.1f}分，建议参考{benchmark}的最佳实践"
                )
                lines.append(f"2. **借鉴标杆经验**：学习{benchmark}在{dim_name}方面的创新举措")
                lines.append(f"3. **制定分阶段目标**：参考标杆实施周期，设定合理的改进里程碑")
            else:
                lines.append("1. **保持当前优势**：各维度差距较小，继续巩固现有成果")
                lines.append("2. **关注行业趋势**：持续跟踪标杆企业的创新实践")
                lines.append("3. **寻求差异化发展**：在现有基础上探索独特的ESG竞争优势")

            lines.append("")

        except Exception as e:
            lines.append(f"> 竞争情报分析生成失败: {e}")
            lines.append("")

        lines.extend(["---", ""])
        return lines

    def _generate_compliance_section(self, result: AnalysisResult) -> List[str]:
        """生成合规检查部分

        生成Markdown表格展示各标准条款的合规状态。

        Args:
            result: 分析结果

        Returns:
            Markdown行列表
        """
        metrics = result.metrics

        # 获取合规检查结果
        compliance_results = self.compliance_checker.check_compliance(metrics)
        summary = self.compliance_checker.get_compliance_summary(metrics)

        lines = [
            "## 国际标准合规检查清单",
            "",
            f"**强制条款合规率**: {summary['overall_rate']:.1%} ({summary['mandatory_compliant']}/{summary['mandatory_total']})",
            "",
            "> 本部分依据ISSB S1/S2和GRI Standards对ESG披露数据进行合规性检查。",
            "",
            "### 合规总览",
            "",
            "| 标准 | 总条款数 | 已合规 | 部分合规 | 未合规 |",
            "|------|:--------:|:------:|:--------:|:------:|",
        ]

        # 按标准分组统计
        for standard_key, std_summary in summary.get("standards_summary", {}).items():
            lines.append(
                f"| {std_summary['name'][:20]}... | {std_summary['total']} | "
                f"{std_summary['compliant']} | {std_summary['partial']} | {std_summary['non_compliant']} |"
            )

        lines.extend(
            [
                "",
                "### 详细合规检查表",
                "",
                "| 标准 | 条款 | 要求类型 | 当前状态 | 缺失项 |",
                "|:----:|------|:--------:|:--------:|--------|",
            ]
        )

        # 按标准分组显示条款
        for standard_key, standard_config in self.compliance_checker.standards.items():
            standard_clauses = [c["standard_id"] for c in standard_config.get("clauses", [])]

            for clause_id in standard_clauses:
                if clause_id in compliance_results:
                    r = compliance_results[clause_id]
                    clause_name = r.get("clause_name", "")
                    req_type = r.get("requirement_type", "")
                    status = r.get("status", "")
                    missing = r.get("missing_items", [])

                    # 状态emoji
                    status_emoji = {"已合规": "✅", "部分合规": "🟡", "未合规": "❌"}.get(
                        status, "⚪"
                    )

                    # 缺失项摘要
                    missing_str = ", ".join(missing[:2]) + ("..." if len(missing) > 2 else "")
                    if not missing_str:
                        missing_str = "-"

                    # 要求类型标记
                    req_badge = "**强制**" if req_type == REQUIREMENT_MANDATORY else req_type

                    lines.append(
                        f"| {clause_id} | {clause_name} | {req_badge} | {status_emoji} {status} | {missing_str} |"
                    )

        lines.extend(
            [
                "",
                "### 需重点关注的缺失项",
                "",
            ]
        )

        # 获取强制但未合规的条款
        non_compliant_mandatory = self.compliance_checker.get_non_compliant_items(
            metrics, requirement_type=REQUIREMENT_MANDATORY
        )

        if non_compliant_mandatory:
            lines.append("**强制条款缺失（优先级：高）**：")
            lines.append("")
            for item in non_compliant_mandatory[:5]:  # 只显示前5个
                lines.append(
                    f"- **{item['standard_id']}** {item['clause_name']}: {', '.join(item['missing_items'])}"
                )
            if len(non_compliant_mandatory) > 5:
                lines.append(f"- ... 还有 {len(non_compliant_mandatory) - 5} 项强制条款需要完善")
            lines.append("")
        else:
            lines.append("✅ 所有强制条款均已合规或部分合规。")
            lines.append("")

        # 获取建议但未合规的条款
        non_compliant_recommended = self.compliance_checker.get_non_compliant_items(
            metrics, requirement_type="建议"
        )

        if non_compliant_recommended:
            lines.append("**建议条款缺失（优先级：中）**：")
            lines.append("")
            for item in non_compliant_recommended[:3]:  # 只显示前3个
                lines.append(f"- {item['standard_id']} {item['clause_name']}")
            if len(non_compliant_recommended) > 3:
                lines.append(f"- ... 还有 {len(non_compliant_recommended) - 3} 项建议条款可以完善")
            lines.append("")

        lines.extend(["---", ""])

        return lines

    def generate_multilingual(
        self,
        result: AnalysisResult,
        languages: Optional[List[Language]] = None,
        benchmark_scores: Optional[Dict[str, float]] = None,
    ) -> Dict[Language, str]:
        """生成多语言报告

        基于分析结果生成多种语言的ESG报告。

        Args:
            result: ESG 分析结果对象
            languages: 语言列表，默认为中文、英文、繁体中文
            benchmark_scores: 行业基准分数

        Returns:
            语言到报告内容的映射字典

        Example:
            >>> generator = ReportGenerator()
            >>> reports = generator.generate_multilingual(analysis_result)
            >>> for lang, content in reports.items():
            ...     print(f"{lang.value}: {len(content)} chars")
        """
        if languages is None:
            languages = [Language.ZH_CN, Language.EN, Language.ZH_TW]

        # 将 AnalysisResult 转换为 analysis_data 格式
        analysis_data = self._convert_to_analysis_data(result, benchmark_scores)

        # 使用 multilingual 模块生成报告
        reports = generate_multilingual_report(
            analysis_data=analysis_data,
            primary_language=languages[0],
            additional_languages=languages[1:] if len(languages) > 1 else None,
        )

        # 转换为字符串格式
        result_map = {}
        for lang, report in reports.items():
            result_map[lang] = report.to_markdown()

        return result_map

    def _convert_to_analysis_data(
        self,
        result: AnalysisResult,
        benchmark_scores: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """将 AnalysisResult 转换为 multilingual 模块所需的格式

        优化：使用策略模式和工厂方法，减少条件分支。

        Args:
            result: 分析结果
            benchmark_scores: 基准分数

        Returns:
            符合 multilingual 模块要求的字典格式
        """
        metrics = result.metrics
        scores = metrics.get_all_dimension_scores()

        # 构建基础数据
        data = {
            "company_name": metrics.company_name,
            "report_year": metrics.year,
            "generated_at": datetime.now().isoformat(),
            "overall_score": result.overall_score,
            "e_score": scores.get("E", 0),
            "s_score": scores.get("S", 0),
            "g_score": scores.get("G", 0),
            "executive_summary": self._generate_summary_text(result),
        }

        # 使用工厂方法构建碳足迹数据
        data["carbon_footprint"] = self._build_carbon_footprint(metrics)

        # 添加合规数据
        if self.include_compliance:
            data["compliance"] = {"ISSB S1": "compliant", "ISSB S2": "partial", "GRI": "compliant"}

        # 添加差距数据
        data["gaps"] = self._build_gaps_data(result)

        # 添加建议数据
        data["recommendations"] = self._build_recommendations(result)

        return data

    def _build_carbon_footprint(self, metrics) -> Dict[str, Any]:
        """构建碳足迹数据 - 使用工厂方法优化"""
        emissions_breakdown = metrics.get_emissions_breakdown()

        if emissions_breakdown:
            return {
                "scope1": emissions_breakdown.get("scope1", 0) or 0,
                "scope2": emissions_breakdown.get("scope2_used", 0) or 0,
                "scope3": emissions_breakdown.get("scope3_summary", 0) or 0,
                "total": emissions_breakdown.get("total_calculated")
                or metrics.carbon_emissions
                or 0,
                "intensity": metrics.carbon_intensity
                or (
                    metrics.carbon_emissions / (metrics.employee_count or 1) * 1000
                    if metrics.carbon_emissions
                    else 0
                ),
            }

        if not metrics.carbon_emissions:
            return {"scope1": 0, "scope2": 0, "scope3": 0, "total": 0, "intensity": 0}

        # 回退到简化计算
        return {
            "scope1": metrics.scope1_emissions or metrics.carbon_emissions * 0.6,
            "scope2": metrics.scope2_emissions_location
            or metrics.scope2_emissions_market
            or metrics.carbon_emissions * 0.3,
            "scope3": metrics.scope3_emissions or metrics.carbon_emissions * 0.1,
            "total": metrics.carbon_emissions,
            "intensity": metrics.carbon_intensity
            or (metrics.carbon_emissions / (metrics.employee_count or 1) * 1000),
        }

    def _build_gaps_data(self, result: AnalysisResult) -> List[Dict[str, Any]]:
        """构建差距数据 - 提取为独立方法"""
        gaps = []
        if not result.gap_analysis or "dimensions" not in result.gap_analysis:
            return gaps

        for dim, gap_data in result.gap_analysis["dimensions"].items():
            gap_value = gap_data.gap if hasattr(gap_data, "gap") else gap_data.get("gap", 0)
            if gap_value > 0:
                gaps.append(
                    {
                        "dimension": dim,
                        "gap": gap_value,
                        "priority": "high" if gap_value > 15 else "medium",
                        "description": f"{dim}维度存在{gap_value:.1f}分差距",
                    }
                )
        return gaps

    def _build_recommendations(self, result: AnalysisResult) -> List[Dict[str, Any]]:
        """构建建议数据 - 提取为独立方法"""
        if not result.strategies:
            return []
        return [
            {"priority": s.get("priority", "medium"), "description": s.get("title", "")}
            for s in result.strategies[:5]
        ]

    def _generate_summary_text(self, result: AnalysisResult) -> str:
        """生成执行摘要文本

        Args:
            result: 分析结果

        Returns:
            摘要文本
        """
        score = result.overall_score

        if score >= 80:
            return "公司在 ESG 方面表现卓越，具有明显的可持续发展优势。"
        elif score >= 60:
            return "公司在 ESG 方面有较好表现，仍有提升空间。"
        elif score >= 40:
            return "公司在 ESG 方面表现一般，需要制定明确的改进计划。"
        else:
            return "公司在 ESG 方面存在明显不足，急需采取行动。"
