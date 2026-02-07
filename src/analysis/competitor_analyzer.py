"""竞争对手分析器

基于行业最佳实践数据，生成深度对标分析和竞争情报。
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from src.core.models import ESGMetrics
from src.config import ESG_DIMENSION_NAMES


@dataclass
class CompetitorStrategy:
    """竞争对手策略数据类"""
    company_name: str
    dimension: str
    strategy_area: str
    best_practice_description: str
    key_results: str
    implementation_timeline: str
    investment: str
    innovation_highlights: str


class CompetitorAnalyzer:
    """竞争对手分析器
    
    加载行业最佳实践数据，生成深度对标分析。
    
    Attributes:
        data_file: 竞争情报数据文件路径
        competitors: 竞争对手数据字典
        industry_benchmarks: 行业基准数据
    """
    
    # 数据文件路径
    DATA_FILE = Path(__file__).parent.parent.parent / "data" / "mock_competitor_intelligence.json"
    
    # 差距阈值（超过此值触发分析）
    GAP_THRESHOLD = 10.0
    
    # 分析模板
    ANALYSIS_TEMPLATE = (
        "经对比，贵司在{维度名}方面落后{标杆名}{差距值}分"
        "（当前{当前分}分 vs 标杆{标杆分}分）。"
        "{标杆名}通过'{最佳实践描述}'实现了{关键成果}。"
        "建议贵司参考其经验，在{实施周期}内启动类似举措。"
    )
    
    def __init__(self):
        """初始化分析器"""
        self.data_file = self.DATA_FILE
        self.competitors: Dict[str, Any] = {}
        self.industry_benchmarks: Dict[str, Any] = {}
        self._load_data()
    
    def _load_data(self) -> None:
        """加载竞争情报数据"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.competitors = data.get("competitors", {})
            self.industry_benchmarks = data.get("industry_benchmarks", {})
        except FileNotFoundError:
            self.competitors = {}
            self.industry_benchmarks = {}
        except json.JSONDecodeError:
            self.competitors = {}
            self.industry_benchmarks = {}
    
    def get_competitor_data(self, company_name: str) -> Optional[Dict[str, Any]]:
        """获取指定竞争对手数据
        
        Args:
            company_name: 竞争对手名称
            
        Returns:
            竞争对手数据字典或None
        """
        return self.competitors.get(company_name)
    
    def get_strategy_by_dimension(
        self, 
        company_name: str, 
        dimension: str
    ) -> Optional[CompetitorStrategy]:
        """获取指定维度的策略数据
        
        Args:
            company_name: 竞争对手名称
            dimension: ESG维度（E/S/G）
            
        Returns:
            策略数据对象或None
        """
        company_data = self.get_competitor_data(company_name)
        if not company_data:
            return None
        
        strategies = company_data.get("strategies", {})
        dim_strategy = strategies.get(dimension)
        
        if not dim_strategy:
            return None
        
        return CompetitorStrategy(
            company_name=company_name,
            dimension=dimension,
            strategy_area=dim_strategy.get("strategy_area", ""),
            best_practice_description=dim_strategy.get("best_practice_description", ""),
            key_results=dim_strategy.get("key_results", ""),
            implementation_timeline=dim_strategy.get("implementation_timeline", ""),
            investment=dim_strategy.get("investment", ""),
            innovation_highlights=dim_strategy.get("innovation_highlights", "")
        )
    
    def generate_analysis(
        self,
        current_metrics: ESGMetrics,
        benchmark_company: str,
        gap_data: Dict[str, Any]
    ) -> str:
        """生成深度对标分析报告
        
        基于差距数据和最佳实践，生成文字分析。
        规则：如果gap_data中某维度差距>10分且Mock库中有该维度数据，则拼接字符串生成分析报告。
        
        Args:
            current_metrics: 当前企业ESG指标
            benchmark_company: 标杆企业名称
            gap_data: 差距数据，格式: {"E": {"current": 65, "target": 85, "gap": 20}, ...}
            
        Returns:
            分析报告文本
        """
        analysis_parts = []
        
        dimension_map = {
            "E": "环境",
            "S": "社会", 
            "G": "治理"
        }
        
        for dim, dim_name in dimension_map.items():
            # 获取差距 - 支持两种数据格式
            if dim in gap_data:
                gap_info = gap_data[dim]
                if isinstance(gap_info, dict):
                    gap_value = gap_info.get("gap", 0)
                    current_score = gap_info.get("current", 0)
                    benchmark_score = gap_info.get("target", 0)
                else:
                    # 如果gap_data直接是数值
                    gap_value = float(gap_info)
                    current_score = 0
                    benchmark_score = 0
            else:
                continue
            
            # 只有差距超过阈值(10分)才生成分析
            if gap_value > self.GAP_THRESHOLD:
                # 获取标杆最佳实践
                strategy = self.get_strategy_by_dimension(benchmark_company, dim)
                
                if strategy:
                    # 使用模板生成分析
                    analysis = self.ANALYSIS_TEMPLATE.format(
                        维度名=dim_name,
                        标杆名=benchmark_company,
                        差距值=round(gap_value, 1),
                        当前分=round(current_score, 1),
                        标杆分=round(benchmark_score, 1),
                        最佳实践描述=strategy.best_practice_description[:100] + "..." if len(strategy.best_practice_description) > 100 else strategy.best_practice_description,
                        关键成果=strategy.key_results.split("。")[0] if "。" in strategy.key_results else strategy.key_results.split("，")[0],
                        实施周期=strategy.implementation_timeline
                    )
                    
                    analysis_parts.append({
                        "dimension": dim,
                        "dimension_name": dim_name,
                        "gap": gap_value,
                        "analysis": analysis,
                        "strategy": strategy
                    })
        
        # 如果没有显著差距，返回通用分析
        if not analysis_parts:
            return "贵司各维度表现与标杆企业差距较小，建议持续优化现有举措。参考行业最佳实践：" + \
                   self._get_general_recommendations()
        
        # 按差距大小排序
        analysis_parts.sort(key=lambda x: -x["gap"])
        
        # 合并分析
        full_analysis = "\n\n".join([p["analysis"] for p in analysis_parts])
        
        # 添加总结建议
        summary = self._generate_summary(analysis_parts, benchmark_company)
        
        return full_analysis + "\n\n" + summary
    
    def _get_general_recommendations(self) -> str:
        """获取通用建议"""
        return (
            "维斯塔斯在环境领域领先（碳中和承诺）、西门子歌美飒在治理方面创新（透明平台）。"
            "建议关注行业共享资源，参与ESG评级互认机制。"
        )
    
    def _generate_summary(
        self, 
        analysis_parts: List[Dict[str, Any]], 
        benchmark_company: str
    ) -> str:
        """生成总结建议
        
        Args:
            analysis_parts: 分析部分列表
            benchmark_company: 标杆企业
            
        Returns:
            总结文本
        """
        priority_dim = analysis_parts[0]["dimension_name"]
        
        return (
            f"【优先行动建议】建议优先关注{priority_dim}维度改进，"
            f"参考{benchmark_company}的{analysis_parts[0]['strategy'].implementation_timeline}实施路径，"
            f"预计投入{analysis_parts[0]['strategy'].investment}可实现显著提升。"
        )
    
    def generate_comparison_table(
        self,
        current_metrics: ESGMetrics,
        benchmark_company: str,
        gap_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成对比表格数据
        
        Args:
            current_metrics: 当前企业ESG指标
            benchmark_company: 标杆企业名称
            gap_data: 差距数据
            
        Returns:
            对比表格数据列表
        """
        table_data = []
        
        dimensions = ["E", "S", "G"]
        
        for dim in dimensions:
            dim_name = ESG_DIMENSION_NAMES.get(dim, dim)
            
            # 我司现状
            current_score = gap_data.get(dim, {}).get("current", 0)
            
            # 标杆做法
            strategy = self.get_strategy_by_dimension(benchmark_company, dim)
            benchmark_practice = strategy.best_practice_description[:80] + "..." if strategy else "暂无数据"
            
            # 差距与机会
            gap_value = gap_data.get(dim, {}).get("gap", 0)
            
            if gap_value > 15:
                opportunity = "高优先级改进机会"
                priority = "🔴 高"
            elif gap_value > 8:
                opportunity = "中等改进机会"
                priority = "🟡 中"
            elif gap_value > 0:
                opportunity = "持续优化"
                priority = "🟢 低"
            else:
                opportunity = "已领先或持平"
                priority = "✅ 达标"
            
            table_data.append({
                "维度": dim_name,
                "我司现状": f"{current_score:.1f}分",
                "标杆做法": benchmark_practice,
                "差距": f"{gap_value:+.1f}分",
                "改进机会": opportunity,
                "优先级": priority
            })
        
        return table_data
    
    def get_competitor_list(self) -> List[str]:
        """获取竞争对手列表"""
        return list(self.competitors.keys())
    
    def get_overall_comparison(
        self,
        current_metrics: ESGMetrics
    ) -> Dict[str, Any]:
        """获取整体对比数据
        
        Args:
            current_metrics: 当前企业ESG指标
            
        Returns:
            整体对比数据
        """
        current_overall = sum(
            current_metrics.get_dimension_score(d) 
            for d in ["E", "S", "G"]
        ) / 3
        
        comparison = {
            "current_company": {
                "name": current_metrics.company_name,
                "overall_score": round(current_overall, 1),
                "e_score": round(current_metrics.get_dimension_score("E"), 1),
                "s_score": round(current_metrics.get_dimension_score("S"), 1),
                "g_score": round(current_metrics.get_dimension_score("G"), 1),
            },
            "competitors": []
        }
        
        for company_name, data in self.competitors.items():
            comparison["competitors"].append({
                "name": company_name,
                "overall_score": data.get("overall_esg_score", 0),
                "country": data.get("country", ""),
                "industry": data.get("industry", ""),
            })
        
        # 计算排名
        all_scores = [(comparison["current_company"]["name"], comparison["current_company"]["overall_score"])]
        for comp in comparison["competitors"]:
            all_scores.append((comp["name"], comp["overall_score"]))
        
        all_scores.sort(key=lambda x: x[1], reverse=True)
        rank = next(i for i, (name, _) in enumerate(all_scores, 1) 
                   if name == current_metrics.company_name)
        
        comparison["current_company"]["rank"] = rank
        comparison["current_company"]["total_companies"] = len(all_scores)
        
        return comparison
    
    def get_innovation_highlights(self, company_name: str) -> List[str]:
        """获取创新亮点
        
        Args:
            company_name: 竞争对手名称
            
        Returns:
            创新亮点列表
        """
        company_data = self.get_competitor_data(company_name)
        if not company_data:
            return []
        
        highlights = []
        strategies = company_data.get("strategies", {})
        
        for dim, strategy in strategies.items():
            innovation = strategy.get("innovation_highlights", "")
            if innovation:
                highlights.append(f"【{ESG_DIMENSION_NAMES.get(dim, dim)}】{innovation}")
        
        return highlights
