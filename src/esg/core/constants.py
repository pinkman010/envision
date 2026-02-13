"""ESG评分基准常量

定义ESG评分所使用的各种基准值和阈值常量。
"""

# ============ 默认值 ============
DEFAULT_SCORE: float = 50.0  # 默认评分
DEFAULT_TARGET_SCORE: float = 80.0  # 默认目标评分

# ============ 差距阈值 ============
GAP_THRESHOLD_HIGH: float = 15.0  # 高差距阈值
GAP_THRESHOLD_MEDIUM: float = 8.0  # 中差距阈值

# ============ 碳强度评分基准（吨CO2e/万元营收）==========
# 低于此值为优秀，高于此值为差
CARBON_INTENSITY_BENCHMARK_LOW = 0.5  # 优秀阈值
CARBON_INTENSITY_BENCHMARK_HIGH = 2.0  # 较差阈值

# ============ 水资源强度基准（立方米/万元营收）==========
WATER_INTENSITY_BENCHMARK_LOW = 10.0  # 优秀阈值
WATER_INTENSITY_BENCHMARK_HIGH = 50.0  # 较差阈值

# ============ 新能源特色指标基准 ===========
TURBINE_AVAILABILITY_BENCHMARK = 97.0  # 风机可利用率基准
BATTERY_CYCLE_LIFE_BENCHMARK = 6000  # 电池循环寿命基准
BATTERY_RECYCLING_RATE_BENCHMARK = 95.0  # 电池回收率基准
ELECTROLYSIS_EFFICIENCY_BENCHMARK = 70.0  # 电解效率基准

# ============ 行业指标基准 ===========
BIODIVERSITY_IMPACT_BENCHMARK = 80.0  # 生物多样性影响基准
ENERGY_STORAGE_SAFETY_BENCHMARK = 90.0  # 储能安全评分基准

# ============ 社会指标基准 ===========
TRAINING_HOURS_MAX = 40.0  # 培训时长参考值
COMMUNITY_INVESTMENT_MAX = 50000000.0  # 社区投资参考值

# ============ 评分上限 ============
SCORE_MAX = 100.0  # 最大评分
SCORE_MIN = 0.0  # 最小评分
