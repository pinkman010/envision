"""测试策略生成器"""

import pytest
from analysis.strategy_generator import StrategyGenerator


class TestStrategyGenerator:
    """测试策略生成器"""
    
    def test_generate_diagnosis(self, mock_gap_analysis):
        """测试诊断生成"""
        gen = StrategyGenerator()
        diagnosis = gen.generate_diagnosis(mock_gap_analysis)
        
        assert len(diagnosis) > 0
        assert len(diagnosis) <= 3
        
        # 检查诊断结构
        for d in diagnosis:
            assert 'id' in d
            assert 'title' in d
            assert 'severity' in d
    
    def test_generate_strategies(self, mock_gap_analysis):
        """测试策略生成"""
        gen = StrategyGenerator()
        diagnosis = gen.generate_diagnosis(mock_gap_analysis)
        strategies = gen.generate_strategies(diagnosis)
        
        assert len(strategies) > 0
        
        # 检查策略结构
        for s in strategies:
            assert 'title' in s
            assert 'priority' in s
            assert 'actions' in s
            assert 'confidence' in s  # 确保有置信度信息
            
            # 置信度不应是随机的
            conf = s['confidence']
            assert 'score' in conf
            assert 'level' in conf
            assert 'needs_review' in conf
            assert 0 <= conf['score'] <= 1  # 分数应在0-1之间
    
    def test_calculate_confidence(self):
        """测试置信度计算"""
        gen = StrategyGenerator()
        
        # 完整数据应产生高置信度
        complete_item = {
            'gap': 20,
            'company_score': 70,
            'benchmark_score': 90,
            'description': '有详细描述'
        }
        conf1 = gen._calculate_confidence(complete_item)
        assert conf1['score'] > 0.7
        
        # 缺少数据应产生较低置信度
        incomplete_item = {
            'gap': 0,
            'company_score': 0,
            'benchmark_score': 0
        }
        conf2 = gen._calculate_confidence(incomplete_item)
        assert conf2['score'] < 0.7
        assert conf2['needs_review'] is True
    
    def test_detect_audience(self):
        """测试受众检测"""
        gen = StrategyGenerator()
        
        assert gen._detect_audience("适合投资者阅读") == "投资者"
        assert gen._detect_audience("请考虑监管要求") == "监管"
        assert gen._detect_audience("关注公众形象") == "公众"
        assert gen._detect_audience("提交董事会审议") == "董事会"
        assert gen._detect_audience("其他指令") == "投资者"  # 默认
    
    def test_refine_strategies(self, mock_gap_analysis):
        """测试策略微调"""
        gen = StrategyGenerator()
        diagnosis = gen.generate_diagnosis(mock_gap_analysis)
        strategies = gen.generate_strategies(diagnosis)
        
        refined = gen.refine_strategies(strategies, "适合投资者阅读")
        
        assert len(refined) == len(strategies)
        
        for s in refined:
            assert 'target_audience' in s
            assert s['target_audience'] == "投资者"
            assert 'refined_benefit' in s
    
    def test_generate_action_checklist(self, mock_gap_analysis):
        """测试行动清单生成"""
        gen = StrategyGenerator()
        diagnosis = gen.generate_diagnosis(mock_gap_analysis)
        strategies = gen.generate_strategies(diagnosis)
        
        if strategies:
            checklist = gen.generate_action_checklist(strategies[0])
            
            assert len(checklist) > 0
            for item in checklist:
                assert 'step' in item
                assert 'action' in item
                assert 'status' in item
                assert item['status'] == "待开始"
