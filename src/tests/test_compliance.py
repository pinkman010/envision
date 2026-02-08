"""测试合规检查功能"""

import logging

from src.esg.core.models import ESGMetrics
from src.esg.core.compliance_checker import ComplianceChecker
from src.config import DISCLOSURE_STANDARDS

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_config_loading():
    """测试配置加载"""
    logger.info("=== 配置加载测试 ===")
    logger.info(f"标准数量: {len(DISCLOSURE_STANDARDS)}")
    for key, std in DISCLOSURE_STANDARDS.items():
        logger.info(f"  {key}: {std['name']} - {len(std['clauses'])}条")


def test_compliance_checker():
    """测试合规检查器"""
    logger.info("\n=== 合规检查器测试 ===")
    
    # 创建测试指标（完整数据）
    metrics = ESGMetrics(
        company_name="测试公司",
        year="2024",
        carbon_emissions=10000,
        renewable_energy_ratio=35.5,
        energy_efficiency=82.0,
        water_consumption=50000,
        waste_recycling_rate=78.0,
        employee_count=5000,
        female_ratio=0.42,
        training_hours=25.0,
        safety_incidents=2,
        community_investment=500000,
        board_independence_ratio=0.67,
        ethics_training_coverage=95.0,
        esg_report_quality=85.0
    )
    
    checker = ComplianceChecker()
    
    # 测试检查合规性
    results = checker.check_compliance(metrics)
    logger.info(f"检查条款总数: {len(results)}")
    
    # 显示部分结果
    logger.info("\n部分检查结果（前5条）:")
    for i, (std_id, result) in enumerate(list(results.items())[:5]):
        logger.info(f"  {std_id}: {result['status']} (得分: {result['score']}, 类型: {result['requirement_type']})")
    
    # 测试合规率
    rate = checker.get_compliance_rate(metrics)
    logger.info(f"\n强制条款合规率: {rate:.1%}")
    
    # 测试汇总
    summary = checker.get_compliance_summary(metrics)
    logger.info(f"已合规: {summary['compliant_count']}, 部分合规: {summary['partial_count']}, 未合规: {summary['non_compliant_count']}")
    
    # 测试缺失项
    non_compliant = checker.get_non_compliant_items(metrics)
    logger.info(f"\n未合规条款数量: {len(non_compliant)}")


def test_report_generator():
    """测试报告生成器"""
    logger.info("\n=== 报告生成器测试 ===")
    
    from src.esg.completion.report_generator import ReportGenerator
    from src.esg.core.models import AnalysisResult
    
    metrics = ESGMetrics(
        company_name="测试公司",
        year="2024",
        carbon_emissions=10000,
        renewable_energy_ratio=35.5,
        employee_count=5000,
        board_independence_ratio=0.67,
    )
    
    result = AnalysisResult(
        metrics=metrics,
        overall_score=72.5,
        strategies=[
            {"dimension": "E", "title": "提高可再生能源比例", "priority": "高", "actions": ["安装太阳能板"]},
            {"dimension": "G", "title": "完善治理架构", "priority": "中", "actions": ["增加独立董事"]},
        ]
    )
    
    generator = ReportGenerator(include_compliance=True)
    report = generator.generate(result)
    
    # 检查是否包含合规部分
    if "国际标准合规检查清单" in report:
        logger.info("报告包含合规检查部分: ✓")
    else:
        logger.info("报告包含合规检查部分: ✗")
    
    if "合规率进度" in report:
        logger.info("报告包含合规率进度条: ✓")
    else:
        logger.info("报告包含合规率进度条: ✗")
    
    # 保存报告样例
    with open("test_report_sample.md", "w", encoding="utf-8") as f:
        f.write(report)
    logger.info("\n测试报告已保存到: test_report_sample.md")


if __name__ == "__main__":
    test_config_loading()
    test_compliance_checker()
    test_report_generator()
    logger.info("\n=== 所有测试完成 ===")
