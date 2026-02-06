"""报告生成器"""

from pathlib import Path
from datetime import datetime

from src.models.esg import AnalysisResult


class ReportGenerator:
    """ESG报告生成器"""
    
    def generate(self, result: AnalysisResult) -> str:
        """生成Markdown报告"""
        metrics = result.metrics
        
        md = f"""# {metrics.company_name} ESG分析报告

**分析时间**: {datetime.now().strftime("%Y-%m-%d %H:%M")}  
**数据年份**: {metrics.year}

## 总体评分

**ESG总分**: {result.overall_score}/100

### 各维度得分
| 维度 | 权重 | 得分 |
|------|------|------|
| 环境(E) | {result.weights.get('E', 0):.0%} | {metrics.get_dimension_score('E'):.1f} |
| 社会(S) | {result.weights.get('S', 0):.0%} | {metrics.get_dimension_score('S'):.1f} |
| 治理(G) | {result.weights.get('G', 0):.0%} | {metrics.get_dimension_score('G'):.1f} |

## 改进建议

"""
        
        for strategy in result.strategies:
            md += f"\n### {strategy.get('title', '')}\n\n"
            md += f"**优先级**: {strategy.get('priority', '中')}\n\n"
            md += "**行动项**:\n"
            for action in strategy.get('actions', []):
                md += f"- {action}\n"
            md += "\n"
        
        if result.data_quality_warnings:
            md += "## 数据质量警告\n\n"
            for warning in result.data_quality_warnings:
                md += f"- ⚠️ {warning}\n"
        
        return md
    
    def save(self, result: AnalysisResult, output_dir: str = "reports") -> str:
        """保存报告到文件"""
        Path(output_dir).mkdir(exist_ok=True)
        
        filename = f"{result.metrics.company_name}_ESG报告_{datetime.now().strftime('%Y%m%d')}.md"
        filepath = Path(output_dir) / filename
        
        content = self.generate(result)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        return str(filepath)
