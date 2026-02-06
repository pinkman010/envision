# -*- coding: utf-8 -*-
"""
新闻抓取与情感分析模块
技术：网络爬虫 + NLP情感分析
"""
import requests
from datetime import datetime, timedelta
import random
from typing import List, Dict
import re


class NewsCrawler:
    """ESG新闻爬虫与情感分析器"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # 模拟新闻数据库（真实场景应调用新闻API）
        self.mock_news_db = self._generate_mock_news()
    
    def _generate_mock_news(self) -> List[Dict]:
        """生成模拟新闻数据"""
        news_templates = [
            # 环境类新闻
            {
                'category': 'E环境',
                'title': '远景能源发布2025年碳中和路线图，承诺2030年实现运营碳中和',
                'content': '远景能源今日发布最新碳中和战略，计划在2030年前实现Scope 1和Scope 2排放归零...',
                'sentiment': 0.8,
                'source': '财新网',
                'keywords': ['碳中和', '碳排放', '气候变化']
            },
            {
                'category': 'E环境',
                'title': '环保组织质疑远景能源Scope 3数据披露不足',
                'content': '某环保NGO发布报告指出，远景能源在供应链碳排放数据披露方面存在不足...',
                'sentiment': -0.7,
                'source': '绿色和平',
                'keywords': ['Scope 3', '供应链', '披露']
            },
            {
                'category': 'E环境',
                'title': '远景能源获得CDP气候变化A-评级',
                'content': '国际环保组织CDP公布2025年评级结果，远景能源获得A-评级，较去年提升一个等级...',
                'sentiment': 0.6,
                'source': 'CDP官网',
                'keywords': ['CDP', '气候变化', '评级']
            },
            
            # 社会类新闻
            {
                'category': 'S社会',
                'title': '远景能源员工满意度调查结果公布，整体满意度达85%',
                'content': '远景能源发布年度员工满意度调查报告，员工整体满意度达到85%，高于行业平均水平...',
                'sentiment': 0.7,
                'source': '人力资源杂志',
                'keywords': ['员工满意度', '企业文化']
            },
            {
                'category': 'S社会',
                'title': '远景能源供应商被曝存在劳工问题，公司回应将展开调查',
                'content': '有媒体报道远景能源某二级供应商存在超时加班问题，公司表示高度重视，已启动审核程序...',
                'sentiment': -0.6,
                'source': '劳工观察',
                'keywords': ['供应链', '劳工权益', '审核']
            },
            {
                'category': 'S社会',
                'title': '远景能源捐赠1000万元支持乡村教育',
                'content': '远景能源宣布向中西部地区捐赠1000万元，用于改善乡村学校基础设施...',
                'sentiment': 0.8,
                'source': '公益时报',
                'keywords': ['公益', '社区投资', '教育']
            },
            
            # 治理类新闻
            {
                'category': 'G治理',
                'title': '远景能源完善董事会结构，新增两名独立董事',
                'content': '远景能源股东大会通过决议，新增两名独立董事，进一步提升董事会独立性...',
                'sentiment': 0.5,
                'source': '证券时报',
                'keywords': ['公司治理', '独立董事', '董事会']
            },
            {
                'category': 'G治理',
                'title': '远景能源发布首份ESG报告，获得专业机构认可',
                'content': '远景能源发布2024年度ESG报告，报告质量获得多家评级机构认可...',
                'sentiment': 0.6,
                'source': 'ESG中国',
                'keywords': ['ESG报告', '信息披露', '透明度']
            },
            {
                'category': 'G治理',
                'title': '投资者呼吁远景能源加强利益相关方沟通',
                'content': '部分机构投资者在分析师会议上建议远景能源建立更系统的利益相关方沟通机制...',
                'sentiment': -0.3,
                'source': '投资者关系',
                'keywords': ['利益相关方', '投资者关系', '沟通']
            }
        ]
        
        # 为每条新闻添加时间戳
        news_list = []
        for i, template in enumerate(news_templates):
            news = template.copy()
            news['id'] = f'NEWS-{i+1:03d}'
            news['publish_date'] = (datetime.now() - timedelta(days=random.randint(1, 90))).strftime('%Y-%m-%d')
            news['url'] = f'https://example.com/news/{news["id"]}'
            news_list.append(news)
        
        return news_list
    
    def fetch_recent_news(self, days: int = 30, company: str = '远景能源') -> List[Dict]:
        """
        抓取最近N天的新闻
        
        Args:
            days: 天数
            company: 公司名称
        
        Returns:
            新闻列表
        """
        # 真实场景：调用新闻API
        # 示例：百度新闻API、腾讯新闻API、或专业ESG新闻源
        
        # 模拟场景：返回模拟数据
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_news = [
            news for news in self.mock_news_db
            if datetime.strptime(news['publish_date'], '%Y-%m-%d') >= cutoff_date
        ]
        
        return recent_news
    
    def analyze_sentiment(self, text: str) -> float:
        """
        情感分析（简化版）
        
        真实场景应使用：
        - SnowNLP（中文情感分析）
        - 百度情感分析API
        - 或训练好的BERT模型
        
        Returns:
            情感得分 (-1到+1)
        """
        # 简化版：基于关键词匹配
        positive_keywords = ['获得', '提升', '优秀', '领先', '成功', '增长', '认可', '满意']
        negative_keywords = ['质疑', '不足', '问题', '下降', '批评', '风险', '违规', '投诉']
        
        pos_count = sum(1 for kw in positive_keywords if kw in text)
        neg_count = sum(1 for kw in negative_keywords if kw in text)
        
        if pos_count + neg_count == 0:
            return 0.0
        
        score = (pos_count - neg_count) / (pos_count + neg_count)
        return max(-1.0, min(1.0, score))
    
    def get_sentiment_by_category(self, days: int = 30) -> Dict[str, float]:
        """
        按ESG维度统计情感得分
        
        Returns:
            {'E环境': 0.3, 'S社会': -0.2, 'G治理': 0.5}
        """
        news_list = self.fetch_recent_news(days)
        
        category_sentiments = {'E环境': [], 'S社会': [], 'G治理': []}
        
        for news in news_list:
            category = news.get('category', '其他')
            sentiment = news.get('sentiment', 0)
            
            if category in category_sentiments:
                category_sentiments[category].append(sentiment)
        
        # 计算平均值
        result = {}
        for cat, scores in category_sentiments.items():
            if scores:
                result[cat] = round(sum(scores) / len(scores), 2)
            else:
                result[cat] = 0.0
        
        return result
    
    def get_risk_alerts(self, threshold: float = -0.5) -> List[Dict]:
        """
        识别风险预警
        
        Args:
            threshold: 负面情感阈值
        
        Returns:
            风险预警列表
        """
        news_list = self.fetch_recent_news(days=30)
        
        alerts = []
        for news in news_list:
            if news.get('sentiment', 0) < threshold:
                alerts.append({
                    'title': news['title'],
                    'category': news['category'],
                    'sentiment': news['sentiment'],
                    'date': news['publish_date'],
                    'severity': '高' if news['sentiment'] < -0.7 else '中',
                    'keywords': news.get('keywords', [])
                })
        
        # 按严重程度排序
        alerts.sort(key=lambda x: x['sentiment'])
        
        return alerts
    
    def get_trending_topics(self, days: int = 30) -> List[Dict]:
        """
        获取热门话题
        
        Returns:
            [{'topic': '碳中和', 'count': 5, 'avg_sentiment': 0.6}, ...]
        """
        news_list = self.fetch_recent_news(days)
        
        topic_stats = {}
        for news in news_list:
            for keyword in news.get('keywords', []):
                if keyword not in topic_stats:
                    topic_stats[keyword] = {'count': 0, 'sentiments': []}
                
                topic_stats[keyword]['count'] += 1
                topic_stats[keyword]['sentiments'].append(news.get('sentiment', 0))
        
        # 计算平均情感并排序
        trending = []
        for topic, stats in topic_stats.items():
            avg_sentiment = sum(stats['sentiments']) / len(stats['sentiments'])
            trending.append({
                'topic': topic,
                'count': stats['count'],
                'avg_sentiment': round(avg_sentiment, 2)
            })
        
        trending.sort(key=lambda x: x['count'], reverse=True)
        
        return trending[:10]
    
    def generate_news_summary(self, days: int = 7) -> str:
        """
        生成新闻摘要
        """
        news_list = self.fetch_recent_news(days)
        sentiment_scores = self.get_sentiment_by_category(days)
        
        summary = f"**过去{days}天ESG舆情概览**\n\n"
        summary += f"- 共监测到 {len(news_list)} 条相关新闻\n"
        summary += f"- 环境维度情感得分: {sentiment_scores.get('E环境', 0)}\n"
        summary += f"- 社会维度情感得分: {sentiment_scores.get('S社会', 0)}\n"
        summary += f"- 治理维度情感得分: {sentiment_scores.get('G治理', 0)}\n\n"
        
        alerts = self.get_risk_alerts()
        if alerts:
            summary += f"⚠️ 发现 {len(alerts)} 条风险预警，请重点关注。"
        else:
            summary += "✅ 未发现重大负面舆情。"
        
        return summary


# 真实新闻API集成示例（备用）
class RealNewsAPI:
    """真实新闻API接口（需要API密钥）"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.base_url = "https://api.example.com/news"  # 替换为真实API
    
    def search_news(self, keyword: str, days: int = 30) -> List[Dict]:
        """
        调用真实新闻API
        
        可选API：
        1. 百度新闻API
        2. 腾讯新闻API
        3. NewsAPI.org
        4. 专业ESG新闻源（如ESG Today）
        """
        # 示例代码（需要根据实际API调整）
        try:
            params = {
                'q': keyword,
                'from': (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d'),
                'apiKey': self.api_key
            }
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            return response.json().get('articles', [])
        except Exception as e:
            print(f"API调用失败: {e}")
            return []