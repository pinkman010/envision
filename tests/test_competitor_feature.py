"""测试竞争对手深度分析功能"""

from src.analysis.competitor_analyzer import CompetitorAnalyzer
from src.core.models import ESGMetrics

def test_competitor_analyzer():
    print('=== 测试竞争对手深度分析功能 ===')
    print()

    # 1. 测试 CompetitorAnalyzer
    analyzer = CompetitorAnalyzer()
    print('1. CompetitorAnalyzer 初始化成功')
    print('   可用竞争对手:', analyzer.get_competitor_list())
    print()

    # 2. 创建测试数据
    metrics = ESGMetrics(
        company_name='远景能源',
        year='2024',
        renewable_energy_ratio=0.45,
        energy_efficiency=70,
        waste_recycling_rate=0.6,
        female_ratio=0.35,
        training_hours=30,
        community_investment=500000,
        board_independence_ratio=0.40,
        ethics_training_coverage=0.70,
        esg_report_quality=75
    )
    print('2. 测试数据创建成功: 远景能源')
    print()

    # 3. 测试差距分析生成
    gap_data = {
        'E': {'current': 65, 'target': 85, 'gap': 20},
        'S': {'current': 70, 'target': 80, 'gap': 10},
        'G': {'current': 75, 'target': 78, 'gap': 3}
    }

    analysis = analyzer.generate_analysis(metrics, '维斯塔斯', gap_data)
    print('3. 文字分析生成成功!')
    print('   分析内容长度:', len(analysis), '字符')
    print()
    print('   分析内容预览:')
    for i, para in enumerate(analysis.split('\n\n')[:3], 1):
        print(f'   段落{i}: {para[:100]}...')
    print()

    # 4. 测试对比表格
    table = analyzer.generate_comparison_table(metrics, '维斯塔斯', gap_data)
    print('4. 对比表格生成成功!')
    print('   表格行数:', len(table))
    for row in table:
        print(f"   - {row['维度']}: {row['我司现状']} vs 标杆, 差距{row['差距']}, {row['改进机会']}")
    print()

    # 5. 测试创新亮点
    highlights = analyzer.get_innovation_highlights('维斯塔斯')
    print('5. 创新亮点获取成功!')
    for i, h in enumerate(highlights[:3], 1):
        print(f"   {i}. {h}")
    print()

    # 6. 测试整体对比
    comparison = analyzer.get_overall_comparison(metrics)
    print('6. 整体对比数据生成成功!')
    print(f"   当前公司: {comparison['current_company']['name']}")
    print(f"   综合评分: {comparison['current_company']['overall_score']}")
    print(f"   排名: #{comparison['current_company']['rank']} / {comparison['current_company']['total_companies']}")
    print()

    print('=== 所有测试通过! ===')
    return True

if __name__ == '__main__':
    test_competitor_analyzer()
