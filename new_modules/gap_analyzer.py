# -*- coding: utf-8 -*-
"""
模块三：披露差距诊断与对标
技术：向量相似度计算
"""
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class BenchmarkData:
    """标杆企业数据"""
    company_name: str
    esg_score: float
    indicators: Dict[str, float]  # 各指标得分


class GapAnalyzer:
    """ESG披露差距分析器 - 支持真实数据和模拟数据"""
    
    def __init__(self, use_real_data: bool = True, extractor=None):
        """
        初始化差距分析器
        
        Args:
            use_real_data: 是否使用真实ESG报告数据
            extractor: ESGDataExtractor实例
        """
        self.use_real_data = use_real_data
        
        if use_real_data:
            self._init_real_data(extractor)
        else:
            self._init_mock_data()
    
    def _init_real_data(self, extractor):
        """从真实数据初始化"""
        if extractor is None:
            try:
                from new_modules.esg_data_extractor import load_extracted_data
                extractor = load_extracted_data()
                # 检查是否有数据
                if not extractor.extracted_data:
                    raise ValueError("没有提取到任何ESG报告数据")
            except Exception as e:
                print(f"⚠️ 无法加载真实数据: {e}，回退到模拟数据")
                self._init_mock_data()
                return
        
        # 从提取器获取标杆数据
        benchmarks_data = extractor.generate_benchmark_data()
        
        # 检查是否有数据
        if not benchmarks_data:
            print(f"⚠️ 真实数据为空，回退到模拟数据")
            self._init_mock_data()
            return
        
        # 转换为BenchmarkData对象
        self.benchmarks = {}
        for company_name, data in benchmarks_data.items():
            self.benchmarks[company_name] = BenchmarkData(
                company_name=data['company_name'],
                esg_score=data['esg_score'],
                indicators=data['indicators']
            )
        
        # 设置远景能源为默认分析对象
        if '远景能源' in self.benchmarks:
            self.yuanjing_data = self.benchmarks['远景能源']
        else:
            # 如果没有远景能源，使用第一个可用公司
            first_company = list(self.benchmarks.keys())[0]
            self.yuanjing_data = self.benchmarks[first_company]
        
        # 如果没有行业平均，创建一个
        if '行业平均' not in self.benchmarks and len(self.benchmarks) > 1:
            self._calculate_industry_average_from_real_data()
    
    def _calculate_industry_average_from_real_data(self):
        """从真实数据计算行业平均"""
        all_indicators = {}
        
        for company, data in self.benchmarks.items():
            for indicator, value in data.indicators.items():
                if indicator not in all_indicators:
                    all_indicators[indicator] = []
                all_indicators[indicator].append(value)
        
        avg_indicators = {
            indicator: np.mean(values)
            for indicator, values in all_indicators.items()
        }
        
        avg_score = np.mean(list(avg_indicators.values()))
        
        self.benchmarks['行业平均'] = BenchmarkData(
            company_name="行业平均",
            esg_score=round(avg_score, 1),
            indicators=avg_indicators
        )
    
    def _init_mock_data(self):
        """初始化模拟数据"""
        # 远景能源模拟数据（当前表现）
        self.yuanjing_data = BenchmarkData(
            company_name="远景能源",
            esg_score=78.5,
            indicators={
                '碳排放披露': 85,
                'Scope 3数据': 45,  # 短板
                '可再生能源占比': 92,
                '能源效率': 88,
                '水资源管理': 75,
                '废弃物管理': 80,
                '员工多样性': 70,
                '职业健康与安全': 82,
                '供应链审核': 65,  # 短板
                '社区投资': 78,
                '董事会独立性': 85,
                '反腐败政策': 88,
                'ESG报告质量': 72,
                '利益相关方沟通': 68  # 短板
            }
        )
        
        # 行业标杆数据（维斯塔斯等）
        self.benchmarks = {
            '维斯塔斯': BenchmarkData(
                company_name="维斯塔斯",
                esg_score=88.2,
                indicators={
                    '碳排放披露': 95,
                    'Scope 3数据': 90,
                    '可再生能源占比': 98,
                    '能源效率': 92,
                    '水资源管理': 85,
                    '废弃物管理': 88,
                    '员工多样性': 88,
                    '职业健康与安全': 90,
                    '供应链审核': 85,
                    '社区投资': 85,
                    '董事会独立性': 90,
                    '反腐败政策': 92,
                    'ESG报告质量': 88,
                    '利益相关方沟通': 85
                }
            ),
            '西门子歌美飒': BenchmarkData(
                company_name="西门子歌美飒",
                esg_score=85.6,
                indicators={
                    '碳排放披露': 90,
                    'Scope 3数据': 82,
                    '可再生能源占比': 95,
                    '能源效率': 90,
                    '水资源管理': 82,
                    '废弃物管理': 85,
                    '员工多样性': 85,
                    '职业健康与安全': 88,
                    '供应链审核': 80,
                    '社区投资': 82,
                    '董事会独立性': 88,
                    '反腐败政策': 90,
                    'ESG报告质量': 85,
                    '利益相关方沟通': 82
                }
            ),
            '行业平均': BenchmarkData(
                company_name="新能源行业平均",
                esg_score=82.0,
                indicators={
                    '碳排放披露': 82,
                    'Scope 3数据': 68,
                    '可再生能源占比': 85,
                    '能源效率': 82,
                    '水资源管理': 78,
                    '废弃物管理': 80,
                    '员工多样性': 75,
                    '职业健康与安全': 80,
                    '供应链审核': 72,
                    '社区投资': 75,
                    '董事会独立性': 82,
                    '反腐败政策': 85,
                    'ESG报告质量': 78,
                    '利益相关方沟通': 75
                }
            )
        }
    
    def calculate_gap(self, benchmark_name: str = '行业平均') -> Dict:
        """
        计算与标杆的差距
        
        Returns:
            {
                'overall_gap': 综合差距,
                'indicator_gaps': {指标: 差距值},
                'strengths': [优势指标],
                'weaknesses': [短板指标],
                'priority_actions': [优先改进项]
            }
        """
        if benchmark_name not in self.benchmarks:
            benchmark_name = '行业平均'
        
        benchmark = self.benchmarks[benchmark_name]
        
        gaps = {}
        strengths = []
        weaknesses = []
        
        for indicator, yuanjing_score in self.yuanjing_data.indicators.items():
            benchmark_score = benchmark.indicators.get(indicator, 0)
            gap = benchmark_score - yuanjing_score
            
            gaps[indicator] = {
                'yuanjing': yuanjing_score,
                'benchmark': benchmark_score,
                'gap': gap,
                'gap_pct': (gap / benchmark_score * 100) if benchmark_score > 0 else 0
            }
            
            if gap > 10:
                weaknesses.append((indicator, gap))
            elif gap < -5:
                strengths.append((indicator, -gap))
        
        # 排序
        weaknesses.sort(key=lambda x: x[1], reverse=True)
        strengths.sort(key=lambda x: x[1], reverse=True)
        
        # 优先改进行动（差距最大的前3个）
        priority_actions = [
            {
                'indicator': ind,
                'gap': gap,
                'urgency': '高' if gap > 20 else '中'
            }
            for ind, gap in weaknesses[:3]
        ]
        
        overall_gap = benchmark.esg_score - self.yuanjing_data.esg_score
        
        return {
            'yuanjing_score': self.yuanjing_data.esg_score,
            'benchmark_score': benchmark.esg_score,
            'benchmark_company': benchmark.company_name,
            'overall_gap': overall_gap,
            'indicator_gaps': gaps,
            'strengths': strengths[:3],  # 前3优势
            'weaknesses': weaknesses[:5],  # 前5短板
            'priority_actions': priority_actions
        }
    
    def get_disclosure_depth_score(self) -> Dict:
        """
        计算披露深度评分
        """
        indicators = self.yuanjing_data.indicators
        
        # 环境披露深度
        e_indicators = ['碳排放披露', 'Scope 3数据', '可再生能源占比', '能源效率', 
                       '水资源管理', '废弃物管理']
        e_score = np.mean([indicators.get(i, 0) for i in e_indicators])
        
        # 社会披露深度
        s_indicators = ['员工多样性', '职业健康与安全', '供应链审核', '社区投资']
        s_score = np.mean([indicators.get(i, 0) for i in s_indicators])
        
        # 治理披露深度
        g_indicators = ['董事会独立性', '反腐败政策', 'ESG报告质量', '利益相关方沟通']
        g_score = np.mean([indicators.get(i, 0) for i in g_indicators])
        
        return {
            'E环境披露': round(e_score, 1),
            'S社会披露': round(s_score, 1),
            'G治理披露': round(g_score, 1),
            '总体披露': round((e_score + s_score + g_score) / 3, 1)
        }
    
    def get_trend_simulation(self, indicator: str) -> List[float]:
        """
        模拟某指标的改进趋势（用于建议效果展示）
        """
        current = self.yuanjing_data.indicators.get(indicator, 50)
        benchmark = 90
        
        # 模拟6个季度的改进轨迹
        improvement = np.linspace(current, min(current + 20, benchmark), 6)
        noise = np.random.normal(0, 2, 6)
        trend = np.clip(improvement + noise, current, 100)
        
        return trend.tolist()
    
    def generate_radar_data(self, benchmark_name: str = '行业平均') -> Dict:
        """
        生成雷达图数据
        """
        benchmark = self.benchmarks.get(benchmark_name, self.benchmarks['行业平均'])
        
        # 聚合到ESG三大维度
        categories = {
            'E环境': ['碳排放披露', 'Scope 3数据', '可再生能源占比', '能源效率', 
                     '水资源管理', '废弃物管理'],
            'S社会': ['员工多样性', '职业健康与安全', '供应链审核', '社区投资'],
            'G治理': ['董事会独立性', '反腐败政策', 'ESG报告质量', '利益相关方沟通']
        }
        
        radar_data = {
            'categories': list(categories.keys()),
            'yuanjing': [],
            'benchmark': []
        }
        
        for cat, indicators in categories.items():
            y_score = np.mean([self.yuanjing_data.indicators.get(i, 0) for i in indicators])
            b_score = np.mean([benchmark.indicators.get(i, 0) for i in indicators])
            radar_data['yuanjing'].append(round(y_score, 1))
            radar_data['benchmark'].append(round(b_score, 1))
        
        return radar_data
    
    def compare_with_multiple(self) -> Dict:
        """
        与多个标杆同时对比
        """
        result = {
            'indicators': list(self.yuanjing_data.indicators.keys()),
            'yuanjing': list(self.yuanjing_data.indicators.values()),
            'companies': {}
        }
        
        for name, data in self.benchmarks.items():
            result['companies'][name] = [
                data.indicators.get(ind, 0) for ind in result['indicators']
            ]
        
        return result