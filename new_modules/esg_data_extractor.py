# -*- coding: utf-8 -*-
"""
ESG数据提取器
从真实ESG报告PDF中提取结构化数据
支持：关键指标提取、主题分析、差距识别
"""
import os
import re
import json
import PyPDF2
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import jieba
import jieba.analyse
import numpy as np

# 尝试导入pdfplumber，如果失败则使用PyPDF2作为备选
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False
    print("⚠️ 警告: pdfplumber未安装，将使用PyPDF2作为PDF提取引擎")
    print("💡 建议安装pdfplumber以获得更好的提取效果: pip install pdfplumber")


@dataclass
class ESGMetrics:
    """ESG指标数据结构"""
    company_name: str
    year: str
    
    # 环境指标 (E)
    carbon_emissions: Optional[float] = None  # 碳排放量 (吨CO2e)
    carbon_intensity: Optional[float] = None  # 碳排放强度
    renewable_energy_ratio: Optional[float] = None  # 可再生能源占比 (%)
    energy_efficiency: Optional[float] = None  # 能源效率
    water_consumption: Optional[float] = None  # 用水量
    waste_recycling_rate: Optional[float] = None  # 废弃物回收率 (%)
    scope1_emissions: Optional[float] = None  # Scope 1 排放
    scope2_emissions: Optional[float] = None  # Scope 2 排放
    scope3_emissions: Optional[float] = None  # Scope 3 排放
    
    # 社会指标 (S)
    employee_count: Optional[int] = None  # 员工总数
    female_ratio: Optional[float] = None  # 女性员工比例 (%)
    training_hours: Optional[float] = None  # 人均培训时长
    safety_incidents: Optional[int] = None  # 安全事故数
    community_investment: Optional[float] = None  # 社区投资金额
    supplier_audit_rate: Optional[float] = None  # 供应商审核覆盖率 (%)
    
    # 治理指标 (G)
    board_independence_ratio: Optional[float] = None  # 独立董事比例 (%)
    ethics_training_coverage: Optional[float] = None  # 伦理培训覆盖率 (%)
    esg_report_quality: Optional[float] = None  # ESG报告质量评分
    stakeholder_engagement: Optional[float] = None  # 利益相关方参与度
    
    # 披露评分 (用于差距分析)
    disclosure_scores: Dict[str, float] = None
    
    def __post_init__(self):
        if self.disclosure_scores is None:
            self.disclosure_scores = {}


class ESGDataExtractor:
    """ESG数据提取器"""
    
    # ESG关键词词典
    ESG_KEYWORDS = {
        'E环境': [
            '碳排放', '碳中和', '碳足迹', '温室气体', 'Scope 1', 'Scope 2', 'Scope 3',
            '可再生能源', '清洁能源', '风能', '太阳能', '能源效率',
            '水资源管理', '废水处理', '循环水', '节水技术',
            '废弃物管理', '循环经济', '回收利用', '固废处理',
            '生物多样性', '生态保护', '土地利用', '生态修复',
            '气候变化', '气候风险', 'TCFD', '情景分析',
            '绿色金融', '绿色债券', 'ESG投资', '可持续金融'
        ],
        'S社会': [
            '员工权益', '劳工标准', '职业健康', '安全生产', '员工培训',
            '多元化', '包容性', '性别平等', '少数族裔', '董事会多样性',
            '社区关系', '社区投资', '公益慈善', '乡村振兴',
            '供应链责任', '供应商审核', '供应链透明度', '冲突矿产',
            '产品质量', '产品安全', '客户隐私', '数据保护', '网络安全',
            '人权', '原住民权益', '童工', '强迫劳动'
        ],
        'G治理': [
            '公司治理', '董事会结构', '独立董事', '董事会效率',
            '商业道德', '反腐败', '反贿赂', '举报机制', '合规管理',
            '风险管理', '内部控制', '审计质量', '内审外审',
            '信息披露', '透明度', 'ESG报告', '报告质量',
            '股东权益', '中小股东保护', '分红政策', '股权结构',
            '利益相关方沟通', '投资者关系', '分析师会议'
        ]
    }
    
    # 指标提取规则 (正则表达式模式)
    METRIC_PATTERNS = {
        'carbon_emissions': [
            r'碳排放[量]?[：:]?\s*([\d,\.]+)\s*[吨t]',
            r'温室气体排放[量]?[：:]?\s*([\d,\.]+)\s*[吨t]',
            r'CO2排放[：:]?\s*([\d,\.]+)\s*[吨t]'
        ],
        'renewable_energy_ratio': [
            r'可再生能源[占比]?[：:]?\s*([\d\.]+)\s*%',
            r'清洁能源[占比]?[：:]?\s*([\d\.]+)\s*%'
        ],
        'employee_count': [
            r'员工[总]?数[：:]?\s*([\d,]+)\s*人',
            r'从业人员[：:]?\s*([\d,]+)\s*人'
        ],
        'female_ratio': [
            r'女性[员工]?[占比]?[：:]?\s*([\d\.]+)\s*%',
            r'女员工[占比]?[：:]?\s*([\d\.]+)\s*%'
        ],
        'board_independence_ratio': [
            r'独立董事[占比]?[：:]?\s*([\d\.]+)\s*%',
            r'独董[占比]?[：:]?\s*([\d\.]+)\s*%'
        ]
    }
    
    def __init__(self, data_path: str = "data"):
        self.data_path = data_path
        self.extracted_data: Dict[str, ESGMetrics] = {}
        
        # 加载自定义词典
        self._load_custom_dict()
    
    def _load_custom_dict(self):
        """加载ESG领域自定义词典"""
        # 添加ESG关键词到jieba词典
        for category, keywords in self.ESG_KEYWORDS.items():
            for keyword in keywords:
                jieba.add_word(keyword, freq=1000)
    
    def extract_from_pdf(self, pdf_path: str) -> ESGMetrics:
        """
        从PDF文件中提取ESG数据
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            ESGMetrics对象
        """
        company_name = self._extract_company_name(pdf_path)
        year = self._extract_year(pdf_path)
        
        # 提取文本内容
        text = self._extract_text_from_pdf(pdf_path)
        
        # 提取各项指标
        metrics = ESGMetrics(
            company_name=company_name,
            year=year
        )
        
        # 使用正则表达式提取数值指标
        for metric_name, patterns in self.METRIC_PATTERNS.items():
            value = self._extract_metric_by_patterns(text, patterns)
            if value is not None:
                setattr(metrics, metric_name, value)
        
        # 提取关键词和主题
        keywords = self._extract_keywords(text)
        metrics.disclosure_scores = self._calculate_disclosure_scores(text, keywords)
        
        return metrics
    
    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """从PDF中提取文本"""
        text = ""
        
        # 优先使用pdfplumber（如果可用）
        if HAS_PDFPLUMBER:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                return text
            except Exception as e:
                print(f"pdfplumber提取失败，尝试PyPDF2: {e}")
        
        # 使用PyPDF2作为备选
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"PyPDF2提取也失败: {e}")
            
        return text
    
    def _extract_company_name(self, pdf_path: str) -> str:
        """从文件名或内容提取公司名称"""
        filename = os.path.basename(pdf_path)
        
        # 常见公司名称映射
        company_mapping = {
            'Xiaomi': '小米集团',
            '远景': '远景能源',
            'envision': '远景能源'
        }
        
        for key, name in company_mapping.items():
            if key.lower() in filename.lower():
                return name
        
        return "Unknown Company"
    
    def _extract_year(self, pdf_path: str) -> str:
        """从文件名提取年份"""
        filename = os.path.basename(pdf_path)
        
        # 匹配4位年份
        year_match = re.search(r'20\d{2}', filename)
        if year_match:
            return year_match.group()
        
        return "2023"
    
    def _extract_metric_by_patterns(self, text: str, patterns: List[str]) -> Optional[float]:
        """使用正则表达式模式提取指标"""
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                # 取第一个匹配值，处理逗号分隔的数字
                value_str = matches[0].replace(',', '')
                try:
                    return float(value_str)
                except ValueError:
                    continue
        return None
    
    def _extract_keywords(self, text: str, top_k: int = 50) -> List[Tuple[str, float]]:
        """提取ESG关键词"""
        # 使用jieba进行关键词提取
        keywords = jieba.analyse.extract_tags(
            text,
            topK=top_k,
            withWeight=True,
            allowPOS=('n', 'ns', 'vn', 'v', 'nz', 'an')
        )
        return keywords
    
    def _calculate_disclosure_scores(self, text: str, keywords: List[Tuple[str, float]]) -> Dict[str, float]:
        """
        计算各维度的披露质量得分
        
        基于关键词覆盖率、文本丰富度等指标
        """
        scores = {}
        text_lower = text.lower()
        
        for category, keyword_list in self.ESG_KEYWORDS.items():
            # 计算关键词覆盖率
            matched_keywords = sum(1 for kw in keyword_list if kw in text)
            coverage = matched_keywords / len(keyword_list)
            
            # 计算文本丰富度 (相关段落长度)
            relevant_text_length = sum(len(kw) * weight for kw, weight in keywords if kw in keyword_list)
            
            # 综合得分 (0-100)
            score = min(100, coverage * 50 + min(50, relevant_text_length / 100))
            scores[category] = round(score, 1)
        
        return scores
    
    def extract_all_reports(self) -> Dict[str, ESGMetrics]:
        """提取所有ESG报告数据"""
        pdf_files = [f for f in os.listdir(self.data_path) 
                    if f.endswith('.pdf')]
        
        print(f"发现 {len(pdf_files)} 个PDF文件:")
        for pdf_file in pdf_files:
            print(f"  - {pdf_file}")
        
        for pdf_file in pdf_files:
            pdf_path = os.path.join(self.data_path, pdf_file)
            try:
                print(f"\n正在处理: {pdf_file}...")
                metrics = self.extract_from_pdf(pdf_path)
                key = f"{metrics.company_name}_{metrics.year}"
                self.extracted_data[key] = metrics
                print(f"  ✅ 成功提取: {key}")
            except Exception as e:
                print(f"  ❌ 处理失败: {e}")
        
        return self.extracted_data
    
    def get_topic_trends_from_reports(self) -> Dict[str, List[Dict]]:
        """
        从报告中分析主题趋势
        
        Returns:
            {
                'hot_topics': [{'topic': str, 'weight': float, 'category': str}, ...],
                'growing_topics': [{'topic': str, 'growth_rate': float}, ...],
                'quarterly_data': {...}
            }
        """
        all_keywords = defaultdict(lambda: defaultdict(float))
        
        for report_key, metrics in self.extracted_data.items():
            # 这里简化处理，实际应该按时间序列分析
            year = metrics.year
            
            # 从报告路径重新提取关键词 (优化：应该缓存)
            pdf_path = os.path.join(self.data_path, f"{report_key.split('_')[0]}_{year} ESG Report.pdf")
            if os.path.exists(pdf_path):
                text = self._extract_text_from_pdf(pdf_path)
                keywords = self._extract_keywords(text, top_k=30)
                
                for keyword, weight in keywords:
                    all_keywords[keyword][year] = max(all_keywords[keyword][year], weight)
        
        # 计算趋势
        hot_topics = []
        growing_topics = []
        
        for keyword, year_data in all_keywords.items():
            if len(year_data) >= 2:
                years = sorted(year_data.keys())
                values = [year_data[y] for y in years]
                
                # 计算增长率
                if len(values) >= 2:
                    growth_rate = (values[-1] - values[0]) / values[0] * 100 if values[0] > 0 else 0
                    
                    # 确定类别
                    category = self._classify_topic(keyword)
                    
                    hot_topics.append({
                        'topic': keyword,
                        'weight': values[-1],
                        'category': category
                    })
                    
                    if growth_rate > 10:  # 增长率超过10%
                        growing_topics.append({
                            'topic': keyword,
                            'growth_rate': growth_rate,
                            'current': values[-1]
                        })
        
        # 排序
        hot_topics.sort(key=lambda x: x['weight'], reverse=True)
        growing_topics.sort(key=lambda x: x['growth_rate'], reverse=True)
        
        return {
            'hot_topics': hot_topics[:30],
            'growing_topics': growing_topics[:10]
        }
    
    def _classify_topic(self, topic: str) -> str:
        """将主题分类到E/S/G"""
        for category, keywords in self.ESG_KEYWORDS.items():
            if topic in keywords:
                return category
        
        # 模糊匹配
        for category, keywords in self.ESG_KEYWORDS.items():
            for keyword in keywords:
                if keyword in topic or topic in keyword:
                    return category
        
        return '其他'
    
    def generate_benchmark_data(self) -> Dict[str, Dict]:
        """
        生成标杆企业数据用于差距分析
        
        Returns:
            {
                '远景能源': {'indicators': {...}, 'esg_score': float},
                '行业标杆': {...},
                '行业平均': {...}
            }
        """
        benchmarks = {}
        
        # 处理远景能源数据
        yuanjing_data = [m for k, m in self.extracted_data.items() if '远景' in k]
        if yuanjing_data:
            latest = max(yuanjing_data, key=lambda x: x.year)
            benchmarks['远景能源'] = self._metrics_to_benchmark(latest)
        
        # 处理小米数据作为对比
        xiaomi_data = [m for k, m in self.extracted_data.items() if '小米' in k]
        if xiaomi_data:
            latest = max(xiaomi_data, key=lambda x: x.year)
            benchmarks['小米集团'] = self._metrics_to_benchmark(latest)
        
        # 计算行业平均 (基于所有可用数据)
        all_metrics = list(self.extracted_data.values())
        if len(all_metrics) > 1:
            benchmarks['行业平均'] = self._calculate_industry_average(all_metrics)
        
        return benchmarks
    
    def _metrics_to_benchmark(self, metrics: ESGMetrics) -> Dict:
        """将ESGMetrics转换为标杆数据格式"""
        indicators = {}
        
        # 环境指标
        if metrics.carbon_emissions is not None:
            indicators['碳排放披露'] = min(100, 50 + metrics.carbon_emissions / 1000)
        if metrics.scope3_emissions is not None:
            indicators['Scope 3数据'] = min(100, metrics.scope3_emissions / 100)
        if metrics.renewable_energy_ratio is not None:
            indicators['可再生能源占比'] = metrics.renewable_energy_ratio
        
        # 社会指标
        if metrics.female_ratio is not None:
            indicators['员工多样性'] = metrics.female_ratio
        if metrics.supplier_audit_rate is not None:
            indicators['供应链审核'] = metrics.supplier_audit_rate
        if metrics.community_investment is not None:
            indicators['社区投资'] = min(100, metrics.community_investment / 10000)
        
        # 治理指标
        if metrics.board_independence_ratio is not None:
            indicators['董事会独立性'] = metrics.board_independence_ratio
        if metrics.esg_report_quality is not None:
            indicators['ESG报告质量'] = metrics.esg_report_quality
        
        # 添加披露得分
        for category, score in metrics.disclosure_scores.items():
            indicators[f'{category}披露'] = score
        
        # 计算综合得分
        esg_score = np.mean(list(indicators.values())) if indicators else 75
        
        return {
            'company_name': metrics.company_name,
            'esg_score': round(esg_score, 1),
            'indicators': indicators,
            'year': metrics.year
        }
    
    def _calculate_industry_average(self, metrics_list: List[ESGMetrics]) -> Dict:
        """计算行业平均数据"""
        all_indicators = defaultdict(list)
        
        for metrics in metrics_list:
            benchmark = self._metrics_to_benchmark(metrics)
            for indicator, value in benchmark['indicators'].items():
                all_indicators[indicator].append(value)
        
        avg_indicators = {
            indicator: round(np.mean(values), 1)
            for indicator, values in all_indicators.items()
        }
        
        avg_score = np.mean(list(avg_indicators.values())) if avg_indicators else 80
        
        return {
            'company_name': '行业平均',
            'esg_score': round(avg_score, 1),
            'indicators': avg_indicators
        }
    
    def save_to_json(self, output_path: str = "data/extracted_esg_data.json"):
        """保存提取的数据到JSON"""
        data = {
            key: asdict(metrics)
            for key, metrics in self.extracted_data.items()
        }
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n数据已保存到: {output_path}")
    
    def load_from_json(self, input_path: str = "data/extracted_esg_data.json"):
        """从JSON加载提取的数据"""
        if not os.path.exists(input_path):
            print(f"文件不存在: {input_path}")
            return {}
        
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.extracted_data = {
            key: ESGMetrics(**metrics)
            for key, metrics in data.items()
        }
        
        print(f"已从 {input_path} 加载 {len(self.extracted_data)} 条记录")
        return self.extracted_data


# ==================== 便捷函数 ====================

def extract_and_save_all_data():
    """提取所有数据并保存"""
    extractor = ESGDataExtractor()
    extractor.extract_all_reports()
    extractor.save_to_json()
    return extractor


def load_extracted_data() -> ESGDataExtractor:
    """加载已提取的数据"""
    extractor = ESGDataExtractor()
    extractor.load_from_json()
    return extractor


# ==================== 测试代码 ====================
if __name__ == "__main__":
    print("=" * 50)
    print("ESG数据提取器测试")
    print("=" * 50)
    
    # 测试数据提取
    extractor = extract_and_save_all_data()
    
    # 测试主题趋势分析
    print("\n" + "=" * 50)
    print("主题趋势分析")
    print("=" * 50)
    trends = extractor.get_topic_trends_from_reports()
    print(f"\n热门主题 (Top 10):")
    for topic in trends['hot_topics'][:10]:
        print(f"  - {topic['topic']} ({topic['category']}): {topic['weight']:.3f}")
    
    # 测试标杆数据生成
    print("\n" + "=" * 50)
    print("标杆数据生成")
    print("=" * 50)
    benchmarks = extractor.generate_benchmark_data()
    for company, data in benchmarks.items():
        print(f"\n{company}:")
        print(f"  ESG得分: {data['esg_score']}")
        print(f"  关键指标: {list(data['indicators'].keys())[:5]}")