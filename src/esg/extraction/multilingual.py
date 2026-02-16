"""多语言报告生成模块

提供多语言ESG报告生成和翻译功能。
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

# 配置日志
logger = logging.getLogger(__name__)


class Language(Enum):
    """支持的语言"""

    EN = "en"  # 英语
    ZH_CN = "zh_CN"  # 简体中文
    ZH_TW = "zh_TW"  # 繁体中文
    JA = "ja"  # 日语
    KO = "ko"  # 韩语
    DE = "de"  # 德语
    FR = "fr"  # 法语
    ES = "es"  # 西班牙语


# 翻译字典示例（实际应用中应使用更完整的翻译）
TRANSLATIONS = {
    Language.EN: {
        "report_title": "ESG Analysis Report",
        "executive_summary": "Executive Summary",
        "environmental": "Environmental",
        "social": "Social",
        "governance": "Governance",
        "overall_score": "Overall Score",
        "recommendations": "Recommendations",
        "high_priority": "High Priority",
        "medium_priority": "Medium Priority",
        "low_priority": "Low Priority",
        "gap_analysis": "Gap Analysis",
        "benchmark_comparison": "Benchmark Comparison",
        "carbon_footprint": "Carbon Footprint",
        "scope1_emissions": "Scope 1 Emissions",
        "scope2_emissions": "Scope 2 Emissions",
        "scope3_emissions": "Scope 3 Emissions",
        "compliance_status": "Compliance Status",
        "compliant": "Compliant",
        "non_compliant": "Non-Compliant",
        "partially_compliant": "Partially Compliant",
        "not_applicable": "Not Applicable",
        # New translation keys
        "esg_scores": "ESG Scores",
        "compliance": "Compliance",
        "total": "Total",
        "intensity": "Carbon Intensity",
        "no_gaps_found": "No significant gaps identified.",
        "no_recommendations": "No recommendations available.",
    },
    Language.ZH_CN: {
        "report_title": "ESG分析报告",
        "executive_summary": "执行摘要",
        "environmental": "环境",
        "social": "社会",
        "governance": "治理",
        "overall_score": "综合评分",
        "recommendations": "改进建议",
        "high_priority": "高优先级",
        "medium_priority": "中优先级",
        "low_priority": "低优先级",
        "gap_analysis": "差距分析",
        "benchmark_comparison": "标杆对比",
        "carbon_footprint": "碳足迹",
        "scope1_emissions": "范围1排放",
        "scope2_emissions": "范围2排放",
        "scope3_emissions": "范围3排放",
        "compliance_status": "合规状态",
        "compliant": "合规",
        "non_compliant": "不合规",
        "partially_compliant": "部分合规",
        "not_applicable": "不适用",
        # 新增翻译键
        "esg_scores": "ESG评分",
        "compliance": "合规",
        "total": "总计",
        "intensity": "碳强度",
        "no_gaps_found": "未发现显著差距",
        "no_recommendations": "暂无建议",
    },
    Language.ZH_TW: {
        "report_title": "ESG分析報告",
        "executive_summary": "執行摘要",
        "environmental": "環境",
        "social": "社會",
        "governance": "治理",
        "overall_score": "綜合評分",
        "recommendations": "改進建議",
        "high_priority": "高優先級",
        "medium_priority": "中優先級",
        "low_priority": "低優先級",
        "gap_analysis": "差距分析",
        "benchmark_comparison": "標竿對比",
        "carbon_footprint": "碳足跡",
        "scope1_emissions": "範圍1排放",
        "scope2_emissions": "範圍2排放",
        "scope3_emissions": "範圍3排放",
        "compliance_status": "合規狀態",
        "compliant": "合規",
        "non_compliant": "不合規",
        "partially_compliant": "部分合規",
        "not_applicable": "不適用",
        # 新增翻譯鍵
        "esg_scores": "ESG評分",
        "compliance": "合規",
        "total": "總計",
        "intensity": "碳強度",
        "no_gaps_found": "未發現顯著差距",
        "no_recommendations": "暫無建議",
    },
}


@dataclass
class ReportSection:
    """报告章节"""

    title: str
    content: str
    order: int = 0
    subsections: List["ReportSection"] = field(default_factory=list)


@dataclass
class MultilingualReport:
    """多语言报告"""

    language: Language
    title: str
    sections: List[ReportSection]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "language": self.language.value,
            "title": self.title,
            "sections": [
                {
                    "title": s.title,
                    "content": s.content,
                    "order": s.order,
                    "subsections": [
                        {"title": sub.title, "content": sub.content} for sub in s.subsections
                    ],
                }
                for s in self.sections
            ],
            "metadata": self.metadata,
        }

    def to_markdown(self) -> str:
        """转换为Markdown格式"""
        lines = [f"# {self.title}\n"]

        for section in sorted(self.sections, key=lambda x: x.order):
            lines.append(f"\n## {section.title}\n")
            lines.append(f"{section.content}\n")

            for sub in section.subsections:
                lines.append(f"\n### {sub.title}\n")
                lines.append(f"{sub.content}\n")

        return "\n".join(lines)


class MultilingualReportGenerator:
    """多语言报告生成器

    生成多语言的ESG分析报告。

    Example:
        >>> generator = MultilingualReportGenerator()
        >>>
        >>> # 生成中文报告
        >>> report = generator.generate_report(
        ...     language=Language.ZH_CN,
        ...     analysis_data={...}
        ... )
        >>>
        >>> # 生成英文报告
        >>> en_report = generator.generate_report(
        ...     language=Language.EN,
        ...     analysis_data={...}
        ... )
    """

    def __init__(self):
        """初始化报告生成器"""
        self.translations = TRANSLATIONS

    def get_translation(self, key: str, language: Language) -> str:
        """获取翻译文本

        Args:
            key: 翻译键
            language: 目标语言

        Returns:
            翻译后的文本
        """
        if language in self.translations:
            return self.translations[language].get(key, key)
        return key

    def generate_report(
        self,
        language: Language,
        analysis_data: Dict[str, Any],
        include_sections: Optional[List[str]] = None,
    ) -> MultilingualReport:
        """生成多语言报告

        Args:
            language: 报告语言
            analysis_data: 分析数据
            include_sections: 包含的章节列表，None表示全部

        Returns:
            多语言报告对象
        """
        t = lambda key: self.get_translation(key, language)

        sections = []

        # 执行摘要
        if not include_sections or "executive_summary" in include_sections:
            sections.append(self._generate_executive_summary(t, analysis_data))

        # ESG评分
        if not include_sections or "esg_scores" in include_sections:
            sections.append(self._generate_esg_scores_section(t, analysis_data))

        # 差距分析
        if not include_sections or "gap_analysis" in include_sections:
            sections.append(self._generate_gap_analysis_section(t, analysis_data))

        # 碳足迹
        if not include_sections or "carbon_footprint" in include_sections:
            carbon_data = analysis_data.get("carbon_footprint")
            if carbon_data:
                sections.append(self._generate_carbon_footprint_section(t, carbon_data))

        # 合规状态
        if not include_sections or "compliance" in include_sections:
            compliance_data = analysis_data.get("compliance")
            if compliance_data:
                sections.append(self._generate_compliance_section(t, compliance_data))

        # 改进建议
        if not include_sections or "recommendations" in include_sections:
            sections.append(self._generate_recommendations_section(t, analysis_data))

        return MultilingualReport(
            language=language,
            title=t("report_title"),
            sections=sections,
            metadata={
                "generated_at": analysis_data.get("generated_at"),
                "company_name": analysis_data.get("company_name"),
                "report_year": analysis_data.get("report_year"),
                "language": language.value,
            },
        )

    def _generate_executive_summary(self, t: callable, data: Dict[str, Any]) -> ReportSection:
        """生成执行摘要"""
        content = f"""
{t("overall_score")}: {data.get('overall_score', 'N/A')}/100

{t("environmental")}: {data.get('e_score', 'N/A')}/100
{t("social")}: {data.get('s_score', 'N/A')}/100
{t("governance")}: {data.get('g_score', 'N/A')}/100

{data.get('executive_summary', 'No summary available.')}
"""

        return ReportSection(title=t("executive_summary"), content=content.strip(), order=1)

    def _generate_esg_scores_section(self, t: callable, data: Dict[str, Any]) -> ReportSection:
        """生成ESG评分章节"""
        content = f"""
### {t("environmental")}: {data.get('e_score', 'N/A')}/100
{data.get('e_analysis', '')}

### {t("social")}: {data.get('s_score', 'N/A')}/100
{data.get('s_analysis', '')}

### {t("governance")}: {data.get('g_score', 'N/A')}/100
{data.get('g_analysis', '')}
"""

        return ReportSection(title=t("esg_scores"), content=content.strip(), order=2)

    def _generate_gap_analysis_section(self, t: callable, data: Dict[str, Any]) -> ReportSection:
        """生成差距分析章节"""
        gaps = data.get("gaps", [])

        if not gaps:
            content = t("no_gaps_found")
        else:
            content_parts = []
            for gap in gaps:
                priority = gap.get("priority", "medium")
                priority_label = t(f"{priority}_priority")
                content_parts.append(f"- [{priority_label}] {gap.get('description', '')}")
            content = "\n".join(content_parts)

        return ReportSection(title=t("gap_analysis"), content=content, order=3)

    def _generate_carbon_footprint_section(
        self, t: callable, carbon_data: Dict[str, Any]
    ) -> ReportSection:
        """生成碳足迹章节"""
        content = f"""
### {t("scope1_emissions")}
{carbon_data.get('scope1', 'N/A')} 吨CO2e

### {t("scope2_emissions")}
{carbon_data.get('scope2', 'N/A')} 吨CO2e

### {t("scope3_emissions")}
{carbon_data.get('scope3', 'N/A')} 吨CO2e

### 总计
{carbon_data.get('total', 'N/A')} 吨CO2e

### 碳强度
{carbon_data.get('intensity', 'N/A')} 吨CO2e/万元
"""

        return ReportSection(title=t("carbon_footprint"), content=content.strip(), order=4)

    def _generate_compliance_section(
        self, t: callable, compliance_data: Dict[str, Any]
    ) -> ReportSection:
        """生成合规性章节"""
        content_parts = [f"### {t('compliance_status')}\n"]

        for standard, status in compliance_data.items():
            status_label = t(status.lower().replace(" ", "_"))
            content_parts.append(f"- {standard}: {status_label}")

        return ReportSection(title=t("compliance"), content="\n".join(content_parts), order=5)

    def _generate_recommendations_section(self, t: callable, data: Dict[str, Any]) -> ReportSection:
        """生成改进建议章节"""
        recommendations = data.get("recommendations", [])

        if not recommendations:
            content = t("no_recommendations")
        else:
            content_parts = []
            for i, rec in enumerate(recommendations, 1):
                priority = rec.get("priority", "medium")
                priority_label = t(f"{priority}_priority")
                content_parts.append(f"{i}. [{priority_label}] {rec.get('description', '')}")
            content = "\n".join(content_parts)

        return ReportSection(title=t("recommendations"), content=content, order=6)

    def generate_reports_for_all_languages(
        self, analysis_data: Dict[str, Any], languages: Optional[List[Language]] = None
    ) -> Dict[Language, MultilingualReport]:
        """为所有语言生成报告

        Args:
            analysis_data: 分析数据
            languages: 语言列表，None表示全部支持的语言

        Returns:
            语言到报告的映射
        """
        if languages is None:
            languages = [Language.EN, Language.ZH_CN, Language.ZH_TW]

        reports = {}
        for lang in languages:
            try:
                reports[lang] = self.generate_report(lang, analysis_data)
                logger.info(f"Generated report for {lang.value}")
            except Exception as e:
                logger.error(f"Failed to generate report for {lang.value}: {e}")

        return reports


def translate_report(report: MultilingualReport, target_language: Language) -> MultilingualReport:
    """翻译报告到目标语言

    Args:
        report: 源报告
        target_language: 目标语言

    Returns:
        翻译后的报告
    """
    # 简化实现，实际应用应使用翻译API
    generator = MultilingualReportGenerator()

    # 提取数据并重新生成
    data = report.metadata.copy()
    # ... 提取更多数据

    return generator.generate_report(target_language, data)


def generate_multilingual_report(
    analysis_data: Dict[str, Any],
    primary_language: Language = Language.ZH_CN,
    additional_languages: Optional[List[Language]] = None,
) -> Dict[Language, MultilingualReport]:
    """生成多语言报告

    Args:
        analysis_data: 分析数据
        primary_language: 主要语言
        additional_languages: 附加语言列表

    Returns:
        语言到报告的映射
    """
    generator = MultilingualReportGenerator()

    languages = [primary_language]
    if additional_languages:
        languages.extend(additional_languages)

    return generator.generate_reports_for_all_languages(analysis_data, list(set(languages)))  # 去重
