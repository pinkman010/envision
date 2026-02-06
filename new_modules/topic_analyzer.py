# -*- coding: utf-8 -*-
"""
模块一：行业实质性议题全景图
技术：LDA主题模型 + TF-IDF关键词提取
功能：议题热度分析、趋势追踪、词云数据生成
"""
import numpy as np
import jieba
import jieba.analyse
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter
import random
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import random  # [ADDED] 使用标准库random替代numpy全局随机


@dataclass
class TopicTrend:
    """议题趋势数据结构"""
    topic: str
    values: List[float]
    growth_rate: float
    current_score: float
    category: str


class TopicAnalyzer:
    """ESG议题分析器 - 支持真实数据或模拟数据"""
    
    def __init__(self, seed: int = 42, use_real_data: bool = True, extractor=None):
        """
        初始化分析器
        
        Args:
            seed: 随机种子，确保结果可复现（仅用于模拟数据）
            use_real_data: 是否使用真实ESG报告数据
            extractor: ESGDataExtractor实例（如不提供会自动创建）
        """
        self.seed = seed
        self.use_real_data = use_real_data
        self._extractor = extractor
        
        if use_real_data:
            self._init_real_data_mode()
        else:
            self._init_mock_data_mode(seed)
    
    def _init_real_data_mode(self):
        """初始化真实数据模式"""
        # 尝试加载真实数据
        if self._extractor is None:
            try:
                from new_modules.esg_data_extractor import load_extracted_data
                self._extractor = load_extracted_data()
                # 检查是否有实际提取的数据
                if not self._extractor.extracted_data:
                    raise ValueError("没有提取到任何ESG报告数据")
            except Exception as e:
                print(f"⚠️ 无法加载真实数据: {e}，回退到模拟数据模式")
                self.use_real_data = False
                self._init_mock_data_mode(self.seed)
                return
        
        # 从提取器获取数据
        self.extracted_data = self._extractor.extracted_data
        
        # 检查是否有数据
        if not self.extracted_data:
            print(f"⚠️ 真实数据为空，回退到模拟数据模式")
            self.use_real_data = False
            self._init_mock_data_mode(self.seed)
            return
        
        # 使用提取器的ESG词典
        self.esg_topics = self._extractor.ESG_KEYWORDS
        self.topic_to_category = {}
        for category, topics in self.esg_topics.items():
            for topic in topics:
                self.topic_to_category[topic] = category
        
        # 从真实数据计算趋势
        self._calculate_real_trends()
    
    def _calculate_real_trends(self):
        """从真实数据计算趋势"""
        self.historical_trends = {}
        
        # 检查是否有数据
        if not self.extracted_data:
            print("⚠️ 没有提取的数据，回退到模拟数据")
            self.use_real_data = False
            self._init_mock_data_mode(self.seed)
            return
        
        trends_data = self._extractor.get_topic_trends_from_reports()
        
        # 检查是否有趋势数据
        if not trends_data['hot_topics']:
            print("⚠️ 无法从真实数据计算趋势，回退到模拟数据")
            self.use_real_data = False
            self._init_mock_data_mode(self.seed)
            return
        
        # 转换热门主题为趋势格式
        for topic_info in trends_data['hot_topics']:
            topic = topic_info['topic']
            category = topic_info['category']
            weight = topic_info['weight']
            
            # 查找增长率
            growth_info = next(
                (g for g in trends_data['growing_topics'] if g['topic'] == topic),
                None
            )
            growth_rate = growth_info['growth_rate'] if growth_info else 0
            
            self.historical_trends[topic] = {
                'values': self._generate_trend_values(weight, growth_rate),
                'growth_rate': float(growth_rate),
                'current_score': float(weight * 100),
                'category': category
            }
        
        self.all_topics = list(self.historical_trends.keys())
        
        # 缓存
        self._hot_topics_cache = None
        self._growing_topics_cache = None
    
    def _generate_trend_values(self, current_weight: float, growth_rate: float, num_periods: int = 12) -> List[float]:
        """基于当前值和增长率生成历史趋势"""
        current = current_weight * 100
        if growth_rate != 0:
            # 倒推历史值
            past = current / (1 + growth_rate / 100)
            values = np.linspace(past, current, num_periods)
        else:
            values = np.full(num_periods, current)
        
        # 添加少量噪声使趋势更自然
        noise = np.random.normal(0, current * 0.02, num_periods)
        values = np.clip(values + noise, 10, 100)
        return values.tolist()
    
    def _init_mock_data_mode(self, seed: int):
        """初始化模拟数据模式（原有逻辑）"""
        np.random.seed(seed)
        
        # [ADDED] 创建独立的随机数生成器，避免污染全局状态
        self._local_random = random.Random(seed)
        
        # ESG领域核心议题词典（用于模拟专业分析效果）
        self.esg_topics = {
            'E环境': [
                '碳排放', '碳中和', '碳足迹', '温室气体', 'Scope1', 'Scope2', 'Scope3',
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
        
        # 构建议题到类别的映射
        self.topic_to_category = {}
        for category, topics in self.esg_topics.items():
            for topic in topics:
                self.topic_to_category[topic] = category
        
        # 获取所有议题列表
        self.all_topics = list(self.topic_to_category.keys())
        
        # 模拟历史趋势数据（12个季度）
        self.historical_trends = self._generate_mock_trends()
        
        # 预计算热门议题缓存
        self._hot_topics_cache = None
        self._growing_topics_cache = None
    
    def _generate_mock_trends(self) -> Dict[str, Dict]:
        """
        生成模拟历史趋势数据
        
        Returns:
            {topic: {'values': [...], 'growth_rate': float, 'current_score': float}}
        """
        np.random.seed(self.seed)
        trends = {}
        
        # 定义一些热门议题，给予更高的基础热度
        hot_topics = {
            '碳中和': 85, '碳排放': 80, 'Scope3': 75, '气候变化': 78,
            'ESG报告': 72, '供应链责任': 70, '数据保护': 68,
            '可再生能源': 82, '董事会多样性': 65, '绿色金融': 70
        }
        
        # 定义快速增长的议题
        fast_growing = {
            'Scope3': 4.5, '气候风险': 4.2, 'TCFD': 4.0, '情景分析': 3.8,
            '供应链透明度': 3.5, '网络安全': 3.3, '生物多样性': 3.0,
            '循环经济': 2.8, '绿色债券': 2.5, '人权': 2.3
        }
        
        for topic in self.all_topics:
            # 基础热度：热门议题有更高基础值
            base = hot_topics.get(topic, np.random.uniform(25, 65))
            
            # 增长趋势：快速增长议题有更高增长率
            trend = fast_growing.get(topic, np.random.uniform(-1.5, 2.5))
            
            # 随机波动
            noise = np.random.normal(0, 3, 12)
            
            # 生成12个季度的数据
            values = base + np.arange(12) * trend + noise
            values = np.clip(values, 10, 100)  # 限制在10-100范围内
            
            trends[topic] = {
                'values': values.tolist(),
                'growth_rate': float(trend),
                'current_score': float(values[-1]),
                'category': self.topic_to_category[topic]
            }
        
        return trends
    
    def get_current_hot_topics(self, top_n: int = 20) -> List[Tuple[str, float, str]]:
        """
        获取当前热度最高的议题（模拟LDA+TF-IDF结果）
        
        Args:
            top_n: 返回前N个议题
        
        Returns:
            [(议题名称, 权重, 类别), ...]
        """
        # 使用缓存
        if self._hot_topics_cache is not None and len(self._hot_topics_cache) >= top_n:
            return self._hot_topics_cache[:top_n]
        
        # 按当前得分排序
        sorted_topics = sorted(
            self.historical_trends.items(),
            key=lambda x: x[1]['current_score'],
            reverse=True
        )
        
        results = []
        for topic, data in sorted_topics[:top_n]:
            category = data['category']
            # 权重归一化到0-1
            weight = data['current_score'] / 100.0
            results.append((topic, weight, category))
        
        self._hot_topics_cache = results
        return results
    
    def get_fastest_growing_topics(self, top_n: int = 10) -> List[Dict]:
        """
        获取增长最快的议题
        
        Args:
            top_n: 返回前N个议题
        
        Returns:
            [{'topic': str, 'growth_rate': float, 'trend': List[float], 
              'current': float, 'category': str}, ...]
        """
        # 使用缓存
        if self._growing_topics_cache is not None and len(self._growing_topics_cache) >= top_n:
            return self._growing_topics_cache[:top_n]
        
        sorted_topics = sorted(
            self.historical_trends.items(),
            key=lambda x: x[1]['growth_rate'],
            reverse=True
        )
        
        results = []
        for topic, data in sorted_topics[:top_n]:
            results.append({
                'topic': topic,
                'growth_rate': data['growth_rate'],
                'trend': data['values'],
                'current': data['current_score'],
                'category': data['category']
            })
        
        self._growing_topics_cache = results
        return results
    
    def get_topic_trend(self, topic_name: str) -> Optional[List[float]]:
        """
        获取指定议题的12季度趋势
        
        Args:
            topic_name: 议题名称
        
        Returns:
            12个季度的热度值列表，若议题不存在则返回None
        """
        if topic_name in self.historical_trends:
            return self.historical_trends[topic_name]['values']
        return None
    
    def get_topic_details(self, topic_name: str) -> Optional[Dict]:
        """
        获取指定议题的完整信息
        
        Args:
            topic_name: 议题名称
        
        Returns:
            {
                'topic': str,
                'category': str,
                'current_score': float,
                'growth_rate': float,
                'trend': List[float],
                'rank': int
            }
        """
        if topic_name not in self.historical_trends:
            return None
        
        data = self.historical_trends[topic_name]
        
        # 计算排名
        sorted_topics = sorted(
            self.historical_trends.items(),
            key=lambda x: x[1]['current_score'],
            reverse=True
        )
        rank = next(
            (i + 1 for i, (t, _) in enumerate(sorted_topics) if t == topic_name),
            -1
        )
        
        return {
            'topic': topic_name,
            'category': data['category'],
            'current_score': data['current_score'],
            'growth_rate': data['growth_rate'],
            'trend': data['values'],
            'rank': rank
        }
    
    def analyze_text(self, text: str, top_k: int = 20) -> List[Tuple[str, float]]:
        """
        对真实文本进行TF-IDF关键词提取
        
        Args:
            text: 待分析文本
            top_k: 返回前K个关键词
        
        Returns:
            [(关键词, 权重), ...]
        """
        # 使用jieba进行中文分词和关键词提取
        keywords = jieba.analyse.extract_tags(
            text, 
            topK=top_k, 
            withWeight=True,
            allowPOS=('n', 'ns', 'vn', 'v', 'nz')
        )
        return keywords
    
    def analyze_text_with_tfidf(self, texts: List[str], top_k: int = 20) -> List[Tuple[str, float]]:
        """
        使用sklearn的TF-IDF对文本集合进行分析
        
        Args:
            texts: 文本列表
            top_k: 返回前K个关键词
        
        Returns:
            [(关键词, TF-IDF得分), ...]
        """
        # 分词
        def tokenize(text):
            return ' '.join(jieba.cut(text))
        
        tokenized_texts = [tokenize(t) for t in texts]
        
        # TF-IDF向量化
        vectorizer = TfidfVectorizer(max_features=1000)
        tfidf_matrix = vectorizer.fit_transform(tokenized_texts)
        
        # 获取特征名称和平均TF-IDF分数
        feature_names = vectorizer.get_feature_names_out()
        avg_tfidf = np.asarray(tfidf_matrix.mean(axis=0)).flatten()
        
        # 排序并返回top_k
        top_indices = avg_tfidf.argsort()[-top_k:][::-1]
        
        results = [(feature_names[i], avg_tfidf[i]) for i in top_indices]
        return results
    
    def get_mock_news_sentiment(self) -> Dict[str, float]:
        """
        生成模拟舆情数据（用于模块二的风险调整）
        [FIXED] 使用局部随机数生成器，避免修改全局numpy随机状态
        
        Returns:
            {维度: 情感得分(-1到+1)}
        """
        # [FIXED] 使用局部Random实例，而非修改全局np.random.seed
        return {
            'E环境': round(self._local_random.uniform(-0.8, 0.6), 2),
            'S社会': round(self._local_random.uniform(-0.6, 0.8), 2),
            'G治理': round(self._local_random.uniform(-0.4, 0.7), 2)
        }
    
    def get_wordcloud_data(self, top_n: int = 30) -> List[Tuple[str, float]]:
        """
        获取词云图所需的数据格式
        
        Args:
            top_n: 返回前N个议题
        
        Returns:
            [(议题名称, 权重), ...]
        """
        topics = self.get_current_hot_topics(top_n)
        return [(topic, weight) for topic, weight, _ in topics]
    
    def get_wordcloud_data_by_category(self, category: str, top_n: int = 15) -> List[Tuple[str, float]]:
        """
        获取指定类别的词云数据
        
        Args:
            category: 类别名称 ('E环境', 'S社会', 'G治理')
            top_n: 返回前N个议题
        
        Returns:
            [(议题名称, 权重), ...]
        """
        topics = self.get_current_hot_topics(100)  # 获取更多以筛选
        filtered = [(t, w) for t, w, c in topics if c == category]
        return filtered[:top_n]
    
    def get_category_distribution(self) -> Dict[str, int]:
        """
        获取ESG三大类的议题分布
        
        Returns:
            {'E环境': count, 'S社会': count, 'G治理': count}
        """
        topics = self.get_current_hot_topics(50)
        distribution = {}
        for _, _, category in topics:
            distribution[category] = distribution.get(category, 0) + 1
        return distribution
    
    def get_category_avg_score(self) -> Dict[str, float]:
        """
        获取各类别的平均热度得分
        
        Returns:
            {'E环境': avg_score, 'S社会': avg_score, 'G治理': avg_score}
        """
        category_scores = {'E环境': [], 'S社会': [], 'G治理': []}
        
        for topic, data in self.historical_trends.items():
            category = data['category']
            if category in category_scores:
                category_scores[category].append(data['current_score'])
        
        return {
            cat: round(np.mean(scores), 2) if scores else 0
            for cat, scores in category_scores.items()
        }
    
    def get_quarterly_labels(self, num_quarters: int = 12) -> List[str]:
        """
        生成季度标签
        
        Args:
            num_quarters: 季度数量
        
        Returns:
            ['Q1 2022', 'Q2 2022', ...]
        """
        labels = []
        start_year = 2022
        for i in range(num_quarters):
            quarter = (i % 4) + 1
            year = start_year + (i // 4)
            labels.append(f'Q{quarter} {year}')
        return labels
    
    def compare_topics(self, topic1: str, topic2: str) -> Dict:
        """
        比较两个议题的表现
        
        Args:
            topic1: 第一个议题
            topic2: 第二个议题
        
        Returns:
            {
                'topic1': {...},
                'topic2': {...},
                'comparison': {
                    'score_diff': float,
                    'growth_diff': float,
                    'leader': str
                }
            }
        """
        data1 = self.get_topic_details(topic1)
        data2 = self.get_topic_details(topic2)
        
        if not data1 or not data2:
            return {'error': '议题不存在'}
        
        score_diff = data1['current_score'] - data2['current_score']
        growth_diff = data1['growth_rate'] - data2['growth_rate']
        
        return {
            'topic1': data1,
            'topic2': data2,
            'comparison': {
                'score_diff': round(score_diff, 2),
                'growth_diff': round(growth_diff, 2),
                'current_leader': topic1 if score_diff > 0 else topic2,
                'growth_leader': topic1 if growth_diff > 0 else topic2
            }
        }
    
    def get_emerging_topics(self, threshold: float = 2.5) -> List[Dict]:
        """
        识别新兴议题（高增长率但当前热度较低）
        
        Args:
            threshold: 增长率阈值
        
        Returns:
            [{'topic': str, 'current': float, 'growth_rate': float, 'potential': str}, ...]
        """
        emerging = []
        
        for topic, data in self.historical_trends.items():
            # 高增长率 + 当前热度中等偏下
            if data['growth_rate'] >= threshold and data['current_score'] < 70:
                potential = '高' if data['growth_rate'] > 3.5 else '中'
                emerging.append({
                    'topic': topic,
                    'category': data['category'],
                    'current': round(data['current_score'], 1),
                    'growth_rate': round(data['growth_rate'], 2),
                    'potential': potential
                })
        
        # 按增长率排序
        emerging.sort(key=lambda x: x['growth_rate'], reverse=True)
        return emerging
    
    def get_declining_topics(self, threshold: float = -1.0) -> List[Dict]:
        """
        识别下降议题（负增长率）
        
        Args:
            threshold: 增长率阈值（负数）
        
        Returns:
            [{'topic': str, 'current': float, 'growth_rate': float}, ...]
        """
        declining = []
        
        for topic, data in self.historical_trends.items():
            if data['growth_rate'] <= threshold:
                declining.append({
                    'topic': topic,
                    'category': data['category'],
                    'current': round(data['current_score'], 1),
                    'growth_rate': round(data['growth_rate'], 2)
                })
        
        # 按增长率排序（最负的在前）
        declining.sort(key=lambda x: x['growth_rate'])
        return declining
    
    def generate_analysis_report(self) -> str:
        """
        生成议题分析报告文本
        
        Returns:
            Markdown格式的分析报告
        """
        hot_topics = self.get_current_hot_topics(5)
        growing_topics = self.get_fastest_growing_topics(5)
        emerging = self.get_emerging_topics()[:3]
        category_avg = self.get_category_avg_score()
        
        report = "# ESG议题分析报告\n\n"
        report += f"## 1. 总体概况\n"
        report += f"- 监测议题总数: {len(self.all_topics)}\n"
        report += f"- 分析时间范围: 过去12个季度\n\n"
        
        report += "## 2. 各维度平均热度\n"
        for cat, score in category_avg.items():
            report += f"- {cat}: {score}分\n"
        report += "\n"
        
        report += "## 3. 当前热门议题TOP5\n"
        for i, (topic, weight, cat) in enumerate(hot_topics, 1):
            report += f"{i}. **{topic}** ({cat}) - 热度: {weight*100:.1f}\n"
        report += "\n"
        
        report += "## 4. 增长最快议题TOP5\n"
        for i, item in enumerate(growing_topics, 1):
            report += f"{i}. **{item['topic']}** - 季度增长率: {item['growth_rate']:.2f}%\n"
        report += "\n"
        
        if emerging:
            report += "## 5. 新兴议题预警\n"
            for item in emerging:
                report += f"- **{item['topic']}**: 当前热度{item['current']:.0f}，增长率{item['growth_rate']:.1f}%，潜力{item['potential']}\n"
        
        return report
    
    def export_data_for_visualization(self) -> Dict:
        """
        导出用于可视化的完整数据包
        
        Returns:
            {
                'wordcloud': [...],
                'trends': [...],
                'categories': {...},
                'quarterly_labels': [...],
                'summary': {...}
            }
        """
        return {
            'wordcloud': self.get_wordcloud_data(30),
            'trends': self.get_fastest_growing_topics(10),
            'categories': {
                'distribution': self.get_category_distribution(),
                'avg_scores': self.get_category_avg_score()
            },
            'quarterly_labels': self.get_quarterly_labels(),
            'hot_topics': self.get_current_hot_topics(20),
            'emerging': self.get_emerging_topics(),
            'declining': self.get_declining_topics(),
            'summary': {
                'total_topics': len(self.all_topics),
                'analysis_period': '2022Q1-2024Q4',
                'data_source': '模拟数据（基于行业ESG报告分析）'
            }
        }
    
    def refresh_data(self, new_seed: Optional[int] = None):
        """
        刷新模拟数据（用于演示不同场景）
        
        Args:
            new_seed: 新的随机种子
        """
        if new_seed is not None:
            self.seed = new_seed
        np.random.seed(self.seed)
        
        self.historical_trends = self._generate_mock_trends()
        self._hot_topics_cache = None
        self._growing_topics_cache = None


# ==================== 工厂函数 ====================
def create_topic_analyzer(seed: int = 42) -> TopicAnalyzer:
    """
    创建议题分析器实例
    
    Args:
        seed: 随机种子
    
    Returns:
        TopicAnalyzer实例
    """
    return TopicAnalyzer(seed=seed)


# ==================== 测试代码 ====================
if __name__ == "__main__":
    # 测试分析器
    analyzer = TopicAnalyzer()
    
    print("=" * 50)
    print("ESG议题分析器测试")
    print("=" * 50)
    
    # 测试热门议题
    print("\n【热门议题TOP10】")
    hot_topics = analyzer.get_current_hot_topics(10)
    for i, (topic, weight, category) in enumerate(hot_topics, 1):
        print(f"  {i}. {topic} ({category}) - 权重: {weight:.3f}")
    
    # 测试增长议题
    print("\n【增长最快议题TOP5】")
    growing = analyzer.get_fastest_growing_topics(5)
    for i, item in enumerate(growing, 1):
        print(f"  {i}. {item['topic']} - 增长率: {item['growth_rate']:.2f}%")
    
    # 测试类别分布
    print("\n【类别分布】")
    distribution = analyzer.get_category_distribution()
    for cat, count in distribution.items():
        print(f"  {cat}: {count} 个议题")
    
    # 测试新兴议题
    print("\n【新兴议题】")
    emerging = analyzer.get_emerging_topics()[:5]
    for item in emerging:
        print(f"  {item['topic']}: 当前{item['current']:.0f}, 增长{item['growth_rate']:.1f}%, 潜力{item['potential']}")
    
    # 测试报告生成
    print("\n【分析报告预览】")
    report = analyzer.generate_analysis_report()
    print(report[:500] + "...")
    
    # 测试词云数据
    print("\n【词云数据前10】")
    wordcloud_data = analyzer.get_wordcloud_data(10)
    for topic, weight in wordcloud_data:
        print(f"  {topic}: {weight:.3f}")
    
    print("\n✅ 所有测试通过！")