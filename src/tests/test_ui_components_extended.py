"""UI组件模块扩展单元测试

覆盖esg.ui.components模块的各种使用场景和边界情况。
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestRenderHeader(unittest.TestCase):
    """页面头部渲染测试"""

    @patch("streamlit.title")
    @patch("streamlit.markdown")
    def test_render_header_with_subtitle(self, mock_markdown, mock_title):
        """测试带副标题的头部渲染"""
        from src.esg.ui import components

        components.render_header("测试标题", "测试副标题")

    @patch("streamlit.title")
    @patch("streamlit.markdown")
    def test_render_header_without_subtitle(self, mock_markdown, mock_title):
        """测试不带副标题的头部渲染"""
        from src.esg.ui import components

        components.render_header("测试标题")


class TestRenderSectionTitle(unittest.TestCase):
    """章节标题测试"""

    @patch("streamlit.markdown")
    def test_render_section_title(self, mock_markdown):
        """测试章节标题渲染"""
        from src.esg.ui import components

        components.render_section_title("测试章节", "📌")


class TestRenderInfoBox(unittest.TestCase):
    """信息框测试"""

    @patch("streamlit.info")
    def test_render_info_box_info(self, mock_info):
        """测试信息类型信息框"""
        from src.esg.ui import components

        components.render_info_box("测试消息", "info")

    @patch("streamlit.success")
    def test_render_info_box_success(self, mock_success):
        """测试成功类型信息框"""
        from src.esg.ui import components

        components.render_info_box("测试消息", "success")

    @patch("streamlit.warning")
    def test_render_info_box_warning(self, mock_warning):
        """测试警告类型信息框"""
        from src.esg.ui import components

        components.render_info_box("测试消息", "warning")

    @patch("streamlit.error")
    def test_render_info_box_error(self, mock_error):
        """测试错误类型信息框"""
        from src.esg.ui import components

        components.render_info_box("测试消息", "error")


class TestRenderProgressStep(unittest.TestCase):
    """进度步骤条测试"""

    @patch("streamlit.columns")
    @patch("streamlit.markdown")
    def test_render_progress_step(self, mock_markdown, mock_columns):
        """测试进度步骤条渲染"""
        mock_col = MagicMock()
        mock_columns.return_value = [mock_col]

        from src.esg.ui import components

        components.render_progress_step(["步骤1", "步骤2"], 0)


class TestScoreCardData(unittest.TestCase):
    """评分卡片数据测试"""

    def test_score_card_data_creation(self):
        """测试评分卡片数据创建"""
        from src.esg.ui.components import ScoreCardData

        data = ScoreCardData(title="测试", score=85.0)
        self.assertEqual(data.title, "测试")
        self.assertEqual(data.score, 85.0)
        self.assertEqual(data.max_score, 100.0)


class TestGapCardData(unittest.TestCase):
    """差距卡片数据测试"""

    def test_gap_card_data_creation(self):
        """测试差距卡片数据创建"""
        from src.esg.ui.components import GapCardData

        data = GapCardData(dimension="E", current=70.0, benchmark=80.0, gap=10.0, priority="高")
        self.assertEqual(data.dimension, "E")
        self.assertEqual(data.current, 70.0)


class TestStrategyCardData(unittest.TestCase):
    """策略卡片数据测试"""

    def test_strategy_card_data_creation(self):
        """测试策略卡片数据创建"""
        from src.esg.ui.components import StrategyCardData

        data = StrategyCardData(
            id="1",
            title="测试策略",
            description="测试描述",
            dimension="E",
            priority="高",
            confidence=0.85,
            actions=["行动1", "行动2"],
        )
        self.assertEqual(data.id, "1")
        self.assertEqual(data.actions, ["行动1", "行动2"])

    def test_strategy_card_data_defaults(self):
        """测试策略卡片数据默认值"""
        from src.esg.ui.components import StrategyCardData

        data = StrategyCardData(
            id="1",
            title="测试",
            description="描述",
            dimension="E",
            priority="高",
            confidence=0.8,
            actions=[],
        )
        self.assertEqual(data.target_audiences, [])
        self.assertEqual(data.recommended_channels, [])


class TestRenderScoreCard(unittest.TestCase):
    """评分卡片渲染测试"""

    @patch("streamlit.markdown")
    @patch("streamlit.container")
    @patch("streamlit.progress")
    def test_render_score_card(self, mock_progress, mock_container, mock_markdown):
        """测试评分卡片渲染"""
        from src.esg.ui.components import ScoreCardData, render_score_card

        data = ScoreCardData(title="测试", score=85.0)
        render_score_card(data)

    @patch("streamlit.markdown")
    @patch("streamlit.container")
    @patch("streamlit.progress")
    def test_render_score_card_no_progress(self, mock_progress, mock_container, mock_markdown):
        """测试不显示进度条"""
        from src.esg.ui.components import ScoreCardData, render_score_card

        data = ScoreCardData(title="测试", score=85.0)
        render_score_card(data, show_progress=False)


class TestRenderMetricCard(unittest.TestCase):
    """指标卡片渲染测试"""

    @patch("streamlit.markdown")
    @patch("streamlit.caption")
    def test_render_metric_card(self, mock_caption, mock_markdown):
        """测试指标卡片渲染"""
        from src.esg.ui.components import render_metric_card

        render_metric_card("碳排放", "1000", "吨")

    @patch("streamlit.markdown")
    @patch("streamlit.caption")
    def test_render_metric_card_with_delta(self, mock_caption, mock_markdown):
        """测试带变化值的指标卡片"""
        from src.esg.ui.components import render_metric_card

        render_metric_card("碳排放", "1000", "吨", delta=-5.0, delta_description="同比")


class TestRenderGapCard(unittest.TestCase):
    """差距卡片渲染测试"""

    @patch("streamlit.markdown")
    @patch("streamlit.columns")
    @patch("streamlit.metric")
    def test_render_gap_card(self, mock_metric, mock_columns, mock_markdown):
        """测试差距卡片渲染"""
        from src.esg.ui.components import GapCardData, render_gap_card

        data = GapCardData(dimension="E", current=70.0, benchmark=80.0, gap=10.0, priority="高")

        # 修复：st.columns 返回列表，不是元组，需要正确模拟
        mock_col1 = MagicMock()
        mock_col2 = MagicMock()
        mock_col3 = MagicMock()
        # 第一次调用 columns([3, 1]) 返回 2 列，第二次调用 columns(3) 返回 3 列
        mock_columns.side_effect = [
            [mock_col1, mock_col2],  # 用于标题行
            [MagicMock(), MagicMock(), MagicMock()],  # 用于数据对比行
        ]
        render_gap_card(data)


class TestRenderStrategyCard(unittest.TestCase):
    """策略卡片渲染测试"""

    @patch("streamlit.markdown")
    @patch("streamlit.columns")
    @patch("streamlit.expander")
    def test_render_strategy_card(self, mock_expander, mock_columns, mock_markdown):
        """测试策略卡片渲染"""
        from src.esg.ui.components import StrategyCardData, render_strategy_card

        mock_expander.return_value.__enter__ = MagicMock()
        mock_expander.return_value.__exit__ = MagicMock()

        mock_col = MagicMock()
        mock_columns.return_value = [mock_col] * 2

        data = StrategyCardData(
            id="1",
            title="测试策略",
            description="测试描述",
            dimension="E",
            priority="高",
            confidence=0.85,
            actions=["行动1"],
        )
        render_strategy_card(data)


class TestRenderRadarChart(unittest.TestCase):
    """雷达图渲染测试"""

    def test_render_radar_chart(self):
        """测试雷达图渲染"""
        from src.esg.ui.components import render_radar_chart

        scores = {"E": 80, "S": 70, "G": 90}
        fig = render_radar_chart(scores)
        self.assertIsNotNone(fig)

    def test_render_radar_chart_with_benchmark(self):
        """测试带标杆的雷达图"""
        from src.esg.ui.components import render_radar_chart

        scores = {"E": 80, "S": 70, "G": 90}
        benchmark = {"E": 85, "S": 75, "G": 88}
        fig = render_radar_chart(scores, benchmark_scores=benchmark)
        self.assertIsNotNone(fig)


class TestRenderBidirectionalBar(unittest.TestCase):
    """双向条形图渲染测试"""

    def test_render_bidirectional_bar(self):
        """测试双向条形图"""
        from src.esg.ui.components import render_bidirectional_bar

        data = {"E": (70.0, 80.0), "S": (75.0, 78.0), "G": (80.0, 85.0)}
        fig = render_bidirectional_bar(data)
        self.assertIsNotNone(fig)


class TestRenderDimensionComparison(unittest.TestCase):
    """维度对比图渲染测试"""

    def test_render_dimension_comparison(self):
        """测试维度对比图"""
        from src.esg.ui.components import render_dimension_comparison

        scores = {"E": 80, "S": 70, "G": 90}
        weights = {"E": 0.33, "S": 0.33, "G": 0.34}
        fig = render_dimension_comparison(scores, weights)
        self.assertIsNotNone(fig)


class TestRenderTopicWordcloud(unittest.TestCase):
    """议题词云图测试"""

    def test_render_topic_wordcloud(self):
        """测试议题词云图"""
        from src.esg.ui.components import render_topic_wordcloud

        topics = [
            {"name": "碳排放", "value": 80, "category": "E"},
            {"name": "水资源", "value": 60, "category": "E"},
        ]
        fig = render_topic_wordcloud(topics)
        self.assertIsNotNone(fig)

    def test_render_topic_wordcloud_empty(self):
        """测试空数据"""
        from src.esg.ui.components import render_topic_wordcloud

        fig = render_topic_wordcloud([])
        self.assertIsNotNone(fig)


class TestRenderGaugeChart(unittest.TestCase):
    """仪表盘图测试"""

    def test_render_gauge_chart(self):
        """测试仪表盘图"""
        from src.esg.ui.components import render_gauge_chart

        fig = render_gauge_chart(85.0)
        self.assertIsNotNone(fig)


class TestRenderGapTable(unittest.TestCase):
    """差距分析表格测试"""

    @patch("streamlit.dataframe")
    def test_render_gap_table(self, mock_dataframe):
        """测试差距表格"""
        from src.esg.ui.components import render_gap_table

        gap_data = {"dimensions": {"E": {"current": 70, "target": 80, "gap": 10, "priority": "高"}}}
        render_gap_table(gap_data)


class TestRenderBusinessUnitRiskMatrix(unittest.TestCase):
    """业务单元风险矩阵测试"""

    @patch("streamlit.info")
    @patch("streamlit.dataframe")
    def test_render_business_unit_risk_matrix(self, mock_dataframe, mock_info):
        """测试风险矩阵"""
        from src.esg.ui.components import render_business_unit_risk_matrix

        matrix_data = [
            {"business_unit": "业务单元A", "topics": {"topic1": {"name": "碳排放", "impact": "高"}}}
        ]
        render_business_unit_risk_matrix(matrix_data)

    @patch("streamlit.info")
    def test_render_business_unit_risk_matrix_empty(self, mock_info):
        """测试空数据"""
        from src.esg.ui.components import render_business_unit_risk_matrix

        render_business_unit_risk_matrix([])


class TestGetScoreColor(unittest.TestCase):
    """分数颜色测试"""

    def test_get_score_color_excellent(self):
        """测试优秀分数"""
        from src.esg.ui.components import get_score_color

        color = get_score_color(85)
        self.assertEqual(color, "#52c41a")

    def test_get_score_color_good(self):
        """测试良好分数"""
        from src.esg.ui.components import get_score_color

        color = get_score_color(65)
        self.assertEqual(color, "#1890ff")

    def test_get_score_color_moderate(self):
        """测试中等分数"""
        from src.esg.ui.components import get_score_color

        color = get_score_color(45)
        self.assertEqual(color, "#faad14")

    def test_get_score_color_poor(self):
        """测试较差分数"""
        from src.esg.ui.components import get_score_color

        color = get_score_color(25)
        self.assertEqual(color, "#ff4d4f")


class TestGetScoreEmoji(unittest.TestCase):
    """分数表情测试"""

    def test_get_score_emoji_excellent(self):
        """测试优秀分数表情"""
        from src.esg.ui.components import get_score_emoji

        emoji = get_score_emoji(85)
        self.assertEqual(emoji, "🌟")

    def test_get_score_emoji_good(self):
        """测试良好分数表情"""
        from src.esg.ui.components import get_score_emoji

        emoji = get_score_emoji(65)
        self.assertEqual(emoji, "👍")

    def test_get_score_emoji_moderate(self):
        """测试中等分数表情"""
        from src.esg.ui.components import get_score_emoji

        emoji = get_score_emoji(45)
        self.assertEqual(emoji, "📊")

    def test_get_score_emoji_poor(self):
        """测试较差分数表情"""
        from src.esg.ui.components import get_score_emoji

        emoji = get_score_emoji(25)
        self.assertEqual(emoji, "⚠️")


class TestGetConfidenceColor(unittest.TestCase):
    """置信度颜色测试"""

    def test_get_confidence_color_high(self):
        """测试高置信度"""
        from src.esg.ui.components import get_confidence_color

        color = get_confidence_color(0.9)
        self.assertEqual(color, "#52c41a")

    def test_get_confidence_color_medium(self):
        """测试中等置信度"""
        from src.esg.ui.components import get_confidence_color

        color = get_confidence_color(0.75)
        self.assertEqual(color, "#1890ff")

    def test_get_confidence_color_low(self):
        """测试低置信度"""
        from src.esg.ui.components import get_confidence_color

        color = get_confidence_color(0.5)
        # 0.5 < 0.55，所以返回红色 #ff4d4f
        self.assertEqual(color, "#ff4d4f")

    def test_get_confidence_color_very_low(self):
        """测试很低置信度"""
        from src.esg.ui.components import get_confidence_color

        color = get_confidence_color(0.3)
        self.assertEqual(color, "#ff4d4f")


class TestRenderEmptyState(unittest.TestCase):
    """空状态渲染测试"""

    @patch("streamlit.markdown")
    def test_render_empty_state(self, mock_markdown):
        """测试空状态渲染"""
        from src.esg.ui.components import render_empty_state

        render_empty_state()


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestRenderHeader))
    suite.addTests(loader.loadTestsFromTestCase(TestRenderSectionTitle))
    suite.addTests(loader.loadTestsFromTestCase(TestRenderInfoBox))
    suite.addTests(loader.loadTestsFromTestCase(TestRenderProgressStep))
    suite.addTests(loader.loadTestsFromTestCase(TestScoreCardData))
    suite.addTests(loader.loadTestsFromTestCase(TestGapCardData))
    suite.addTests(loader.loadTestsFromTestCase(TestStrategyCardData))
    suite.addTests(loader.loadTestsFromTestCase(TestRenderScoreCard))
    suite.addTests(loader.loadTestsFromTestCase(TestRenderMetricCard))
    suite.addTests(loader.loadTestsFromTestCase(TestRenderGapCard))
    suite.addTests(loader.loadTestsFromTestCase(TestRenderStrategyCard))
    suite.addTests(loader.loadTestsFromTestCase(TestRenderRadarChart))
    suite.addTests(loader.loadTestsFromTestCase(TestRenderBidirectionalBar))
    suite.addTests(loader.loadTestsFromTestCase(TestRenderDimensionComparison))
    suite.addTests(loader.loadTestsFromTestCase(TestRenderTopicWordcloud))
    suite.addTests(loader.loadTestsFromTestCase(TestRenderGaugeChart))
    suite.addTests(loader.loadTestsFromTestCase(TestRenderGapTable))
    suite.addTests(loader.loadTestsFromTestCase(TestRenderBusinessUnitRiskMatrix))
    suite.addTests(loader.loadTestsFromTestCase(TestGetScoreColor))
    suite.addTests(loader.loadTestsFromTestCase(TestGetScoreEmoji))
    suite.addTests(loader.loadTestsFromTestCase(TestGetConfidenceColor))
    suite.addTests(loader.loadTestsFromTestCase(TestRenderEmptyState))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
