"""ESG评分基准常量

定义ESG评分所使用的各种基准值和阈值常量。
"""

# ============ 默认值 ============
DEFAULT_SCORE: float = 50.0  # 默认评分
DEFAULT_TARGET_SCORE: float = 80.0  # 默认目标评分

# ============ 差距阈值 ============
GAP_THRESHOLD_HIGH: float = 15.0  # 高差距阈值
GAP_THRESHOLD_MEDIUM: float = 8.0  # 中差距阈值

# ============ E维度评分权重配置 ============
# 将范围3排放纳入环境(E)维度评分体系
E_DIMENSION_WEIGHTS = {
    # 一级指标 - 排放相关（45%）
    "carbon_intensity_scope12": 0.15,  # 范围1+2碳强度
    "scope3_coverage": 0.10,  # 范围3覆盖率（新增）
    "scope3_ratio": 0.05,  # 范围3/1+2比例（新增）
    "sbti_target": 0.15,  # SBTi目标
    # 二级指标 - 运营效率（30%）
    "renewable_energy_ratio": 0.075,
    "energy_efficiency": 0.075,
    "waste_recycling_rate": 0.075,
    "water_intensity": 0.075,
    # 三级指标 - 新能源特色（25%）
    "turbine_availability": 0.05,
    "curtailment_rate": 0.05,
    "battery_cycle_life": 0.05,
    "battery_recycling_rate": 0.025,
    "electrolysis_efficiency": 0.025,
    "energy_storage_safety": 0.05,
}

# 范围3比例评分参考值
SCOPE3_RATIO_IDEAL_MIN = 5.0  # 理想区间最小值
SCOPE3_RATIO_IDEAL_MAX = 20.0  # 理想区间最大值
SCOPE3_RATIO_ACCEPTABLE_MAX = 50.0  # 可接受区间最大值

# ============ 新能源子行业碳强度评分基准（吨CO2e/百万元营收）==========
# MSCI/CDP标准：基于新能源行业实际排放水平设定
# 优秀阈值 = 行业前25%分位，较差阈值 = 行业后25%分位
CARBON_INTENSITY_BENCHMARKS = {
    "wind_power": {  # 风电整机/运营商
        "excellent": 0.15,  # <0.15 优秀（吨CO2e/百万元）
        "good": 0.25,  # 0.15-0.25 良好
        "poor": 0.50,  # >0.50 较差
    },
    "solar_pv": {  # 光伏组件/电站
        "excellent": 0.20,
        "good": 0.35,
        "poor": 0.70,
    },
    "energy_storage": {  # 储能系统/电池
        "excellent": 0.40,
        "good": 0.65,
        "poor": 1.20,
    },
    "green_hydrogen": {  # 电解槽/氢能设备
        "excellent": 0.30,
        "good": 0.50,
        "poor": 0.90,
    },
    "new_energy_composite": {  # 综合新能源企业
        "excellent": 0.25,
        "good": 0.45,
        "poor": 0.85,
    },
}

# 默认使用综合新能源企业基准
CARBON_INTENSITY_BENCHMARK_LOW = 0.25  # 优秀阈值（吨CO2e/百万元营收）
CARBON_INTENSITY_BENCHMARK_HIGH = 0.85  # 较差阈值

# ============ SBTi目标追踪配置 ===========
SBTI_STATUS_SCORES = {
    "committed": 20,  # 已承诺，待提交目标
    "target_set": 60,  # 已设定目标，待验证
    "validated": 80,  # 目标已通过SBTi验证
    "validated_1.5c": 100,  # 1.5°C路径目标（最高级别）
    "validated_wb2c": 90,  # Well-below 2°C目标
    "validated_2c": 80,  # 2°C目标
    "not_committed": 0,  # 未承诺
    "removed": 0,  # 已被移出名录
}

# 减排进度评分基准（相对于基准年的减排率）
EMISSION_REDUCTION_BENCHMARKS = {
    "2025": {  # 2025年目标进度
        "excellent": 0.30,  # 减排30%+
        "good": 0.20,  # 减排20%+
        "poor": 0.10,  # 减排<10%
    },
    "2030": {  # 2030年目标进度
        "excellent": 0.50,  # 减排50%+（1.5°C路径）
        "good": 0.42,  # 减排42%+（WB2C路径）
        "poor": 0.25,  # 减排<25%
    },
    "2050": {  # 2050年净零目标
        "excellent": 1.00,  # 已实现净零
        "good": 0.90,  # 减排90%+
        "poor": 0.70,  # 减排<70%
    },
}

# ============ 水资源强度基准（立方米/百万元营收）==========
# CDP Water Security 标准
WATER_INTENSITY_BENCHMARKS = {
    "wind_power": {
        "excellent": 5.0,  # 极低水耗
        "good": 15.0,
        "poor": 40.0,
    },
    "solar_pv": {
        "excellent": 8.0,
        "good": 20.0,
        "poor": 50.0,
    },
    "energy_storage": {
        "excellent": 20.0,
        "good": 50.0,
        "poor": 120.0,
    },
    "green_hydrogen": {
        "excellent": 500.0,  # 绿氢生产水耗较高但可接受
        "good": 800.0,
        "poor": 1500.0,
    },
    "new_energy_composite": {
        "excellent": 15.0,
        "good": 40.0,
        "poor": 100.0,
    },
}

WATER_INTENSITY_BENCHMARK_LOW = 15.0  # 优秀阈值
WATER_INTENSITY_BENCHMARK_HIGH = 100.0  # 较差阈值

# ============ 新能源特色指标基准 ===========
TURBINE_AVAILABILITY_BENCHMARK = 97.0  # 风机可利用率基准
BATTERY_CYCLE_LIFE_BENCHMARK = 6000  # 电池循环寿命基准
BATTERY_RECYCLING_RATE_BENCHMARK = 95.0  # 电池回收率基准
ELECTROLYSIS_EFFICIENCY_BENCHMARK = 70.0  # 电解效率基准

# 新增新能源特色指标
CURTAILMENT_RATE_BENCHMARK = 5.0  # 弃风/弃光率基准（%）
SOLAR_DEGRADATION_RATE_BENCHMARK = 0.55  # 光伏组件年衰减率基准（%）
BATTERY_SECOND_LIFE_UTILIZATION_BENCHMARK = 80.0  # 电池梯次利用率基准
GREEN_HYDROGEN_RATIO_BENCHMARK = 90.0  # 绿氢占比基准

# ============ 行业指标基准 ===========
BIODIVERSITY_IMPACT_BENCHMARK = 80.0  # 生物多样性影响基准
ENERGY_STORAGE_SAFETY_BENCHMARK = 90.0  # 储能安全评分基准

# 范围3评分基准
SCOPE3_COVERAGE_BENCHMARK_HIGH = 0.80  # 高覆盖率基准（80%）
SCOPE3_COVERAGE_BENCHMARK_LOW = 0.40  # 低覆盖率基准（40%）

# ============ 社会指标基准 ===========
TRAINING_HOURS_MAX = 40.0  # 培训时长参考值
COMMUNITY_INVESTMENT_MAX = 50000000.0  # 社区投资参考值

# 新增社会指标基准
TRIR_BENCHMARK = 2.0  # 总可记录伤害率基准（每百万工时）
LOST_TIME_INJURY_RATE_BENCHMARK = 0.5  # 失时工伤率基准
FEMALE_EXECUTIVE_RATIO_BENCHMARK = 30.0  # 高管层女性比例基准（%）
LOCAL_EMPLOYMENT_RATIO_BENCHMARK = 70.0  # 本地雇佣比例基准（%）

# 安全指标评分基准（越低越好）
TRIR_BENCHMARKS = {
    "excellent": 1.0,  # <1.0 优秀
    "good": 2.0,  # 1.0-2.0 良好
    "poor": 3.0,  # >3.0 较差
}

LTIFR_BENCHMARKS = {
    "excellent": 0.2,  # <0.2 优秀
    "good": 0.5,  # 0.2-0.5 良好
    "poor": 1.0,  # >1.0 较差
}

# 安全投入占比评分基准（越高越好）
SAFETY_INVESTMENT_BENCHMARKS = {
    "excellent": 2.0,  # >2% 优秀
    "good": 1.0,  # 1%-2% 良好
    "poor": 0.5,  # <0.5% 较差
}

# ============ 评分上限 ============
SCORE_MAX = 100.0  # 最大评分
SCORE_MIN = 0.0  # 最小评分

# ============ MSCI/CDP 评级对标 ===========
MSCI_ESG_SCORE_MAPPING = {
    "AAA": (8.6, 10.0),  # 领先
    "AA": (7.1, 8.6),  # 领先
    "A": (5.7, 7.1),  # 平均
    "BBB": (4.3, 5.7),  # 平均
    "BB": (2.9, 4.3),  # 落后
    "B": (1.4, 2.9),  # 落后
    "CCC": (0.0, 1.4),  # 落后
}

CDP_SCORE_MAPPING = {
    "A": (90, 100),  # 领导力级别
    "A-": (80, 90),
    "B": (70, 80),  # 管理级别
    "B-": (60, 70),
    "C": (50, 60),  # 认知级别
    "C-": (40, 50),
    "D": (30, 40),  # 披露级别
    "D-": (20, 30),
    "F": (0, 20),  # 未披露/拒绝
}

# ============ G维度评分权重配置 ============
# 传统治理（40%）+ 气候治理（40%）+ 信息披露（20%）
G_DIMENSION_WEIGHTS = {
    # 传统治理（40%）
    "board_independence_ratio": 0.10,  # 董事会独立性
    "esg_committee_independence": 0.10,  # ESG委员会独立性
    "ethics_training_coverage": 0.10,  # 道德培训覆盖率
    "anti_corruption_training_coverage": 0.10,  # 反腐败培训覆盖率
    # 气候治理（40%）- 新增重点
    "climate_governance": 0.20,  # 气候治理架构
    "tcfd_disclosure": 0.20,  # TCFD披露完整度
    # 信息披露（20%）
    "esg_report_quality": 0.10,  # ESG报告质量
    "whistleblower_protection": 0.10,  # 举报人保护机制
}

# 气候治理架构评分权重
CLIMATE_GOVERNANCE_WEIGHTS = {
    "board_committee": 0.30,  # 董事会气候委员会设立
    "exec_comp": 0.30,  # 高管薪酬与气候目标挂钩
    "risk_process": 0.20,  # 气候风险识别流程
    "board_reporting": 0.20,  # 定期气候议题向董事会汇报
}

# TCFD四支柱权重
TCFD_PILLAR_WEIGHTS = {
    "governance": 0.25,  # 治理
    "strategy": 0.25,  # 战略
    "risk_management": 0.25,  # 风险管理
    "metrics_targets": 0.25,  # 指标与目标
}

# 气候信息披露质量评分权重
CLIMATE_DISCLOSURE_QUALITY_WEIGHTS = {
    "scope123_full_disclosure": 0.40,  # 范围1+2+3完整披露
    "third_party_verification": 0.30,  # 第三方核证
    "historical_data_comparability": 0.20,  # 历史数据可比性
    "forward_looking_targets": 0.10,  # 前瞻性目标披露
}
