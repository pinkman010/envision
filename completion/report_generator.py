"""报告生成器"""

import os
from datetime import datetime
from core.data_models import AnalysisResult


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, output_dir: str = "data/reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_markdown(self, result: AnalysisResult) -> str:
        """生成Markdown报告"""
        m = result.metrics
        g = result.gap_analysis
        
        report = f"""# {m.company_name} ESG分析报告

## 数据质量声明

**数据置信度**: {result.confidence_level}

"""
        # 警告
        if result.data_quality_warnings:
            report += "### 数据质量警告\n\n"
            for warning in result.data_quality_warnings:
                report += f"- ⚠️ {warning}\n"
            report += "\n"
        
        # 数据溯源
        report += "## 数据溯源\n\n"
        report += "| 指标 | 数值 | 置信度 | 来源 |\n"
        report += "|------|------|--------|------|\n"
        
        for field in ['carbon_emissions', 'employee_count', 'renewable_energy_ratio']:
            value = getattr(m, field)
            conf = m.confidence.get(field, 0)
            source = m.data_sources.get(field, '')[:30]
            report += f"| {field} | {value if value else 'N/A'} | {conf:.0%} | {source}... |\n"
        
        # 基本信息
        report += f"""
## 基本信息

- **公司**: {m.company_name}
- **年份**: {m.year}
- **总分**: {result.overall_score}/100

## 维度得分

- 环境(E): {m.get_dimension_score('E'):.1f}
- 社会(S): {m.get_dimension_score('S'):.1f}
- 治理(G): {m.get_dimension_score('G'):.1f}

## 差距分析

"""
        for dim, data in g.get('dimensions', {}).items():
            report += f"- {dim}: 当前{data['current']} vs 目标{data['target']} (差距{data['gap']:+.1f})\n"
        
        # 建议
        report += "\n## 改进建议\n\n"
        for i, strategy in enumerate(result.strategies, 1):
            report += f"{i}. **{strategy['title']}** ({strategy['priority']}优先级)\n"
            for action in strategy['actions']:
                report += f"   - {action}\n"
            report += "\n"
        
        report += f"""\n---

*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
*系统版本: ESG评价专家系统 v1.1*
"""
        return report
    
    def save_markdown(self, result: AnalysisResult, filename: str = None) -> str:
        """保存报告"""
        if filename is None:
            filename = f"{result.metrics.company_name}_ESG报告.md"
        
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.generate_markdown(result))
        return filepath