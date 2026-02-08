"""ESG维度/指标配置

ESG维度定义、评分阈值、AHP配置、业务单元等。
"""

from typing import Any, Dict, List

# ========== ESG 维度配置 ==========
ESG_DIMENSIONS: Dict[str, Dict[str, str]] = {
    "E": {"name": "环境", "color": "#52c41a", "icon": "🌱"},
    "S": {"name": "社会", "color": "#1890ff", "icon": "👥"},
    "G": {"name": "治理", "color": "#faad14", "icon": "⚖️"},
}

ESG_DIMENSION_NAMES = {k: v["name"] for k, v in ESG_DIMENSIONS.items()}
ESG_COLORS = {k: v["color"] for k, v in ESG_DIMENSIONS.items()}
ESG_ICONS = {k: v["icon"] for k, v in ESG_DIMENSIONS.items()}

# ========== 评分阈值 ==========
DEFAULT_SCORE = 50.0
GAP_THRESHOLD_HIGH = 15.0
GAP_THRESHOLD_MEDIUM = 8.0
AHP_CONSISTENCY_THRESHOLD = 0.1
CONFIDENCE_THRESHOLD_HIGH = 0.8
CONFIDENCE_THRESHOLD_MEDIUM = 0.6

# ========== AHP 配置 ==========
AHP_RI_TABLE: Dict[int, float] = {
    1: 0.0,
    2: 0.0,
    3: 0.58,
    4: 0.90,
    5: 1.12,
    6: 1.24,
    7: 1.32,
    8: 1.41,
    9: 1.45,
    10: 1.49,
}

AHP_SCALE_LABELS: Dict[int, str] = {
    1: "同等重要",
    3: "稍微重要",
    5: "明显重要",
    7: "强烈重要",
    9: "极端重要",
}

# ========== 数据质量阈值 ==========
DATA_QUALITY_THRESHOLDS = {
    "min_carbon_emissions": 1000,
    "min_employees": 100,
    "min_carbon_per_employee": 50000,
    "max_female_ratio": 1.0,
    "max_board_independence": 1.0,
}

# ========== 实质性议题评分配置 ==========
# 基于新能源行业特性的10个核心议题初始评分
# financial: 财务重要性 (0-10), impact: 影响重要性 (0-10)
DEFAULT_MATERIALITY_SCORES: Dict[str, Dict[str, Dict[str, Any]]] = {
    "carbon_emission": {
        "financial": 9,
        "impact": 9,
        "name": "碳排放管理",
        "dimension": "E",
        "description": "温室气体排放核算与管理",
    },
    "renewable_energy": {
        "financial": 8,
        "impact": 8,
        "name": "可再生能源使用",
        "dimension": "E",
        "description": "清洁能源转型与能源结构优化",
    },
    "supply_chain_carbon": {
        "financial": 7,
        "impact": 8,
        "name": "供应链碳管理",
        "dimension": "E",
        "description": "范围3排放与供应链环境管理",
    },
    "employee_safety": {
        "financial": 7,
        "impact": 9,
        "name": "员工职业健康与安全",
        "dimension": "S",
        "description": "工作场所安全与员工健康保护",
    },
    "employee_training": {
        "financial": 5,
        "impact": 6,
        "name": "员工培训与发展",
        "dimension": "S",
        "description": "技能培训与职业发展机会",
    },
    "community_investment": {
        "financial": 4,
        "impact": 7,
        "name": "社区投资",
        "dimension": "S",
        "description": "社区关系建设与公益投资",
    },
    "board_diversity": {
        "financial": 6,
        "impact": 7,
        "name": "董事会多元化",
        "dimension": "G",
        "description": "董事会构成多元化与独立性",
    },
    "esg_disclosure": {
        "financial": 7,
        "impact": 6,
        "name": "ESG信息披露",
        "dimension": "G",
        "description": "ESG报告质量与透明度",
    },
    "business_ethics": {
        "financial": 6,
        "impact": 8,
        "name": "商业道德与合规",
        "dimension": "G",
        "description": "反腐败、举报机制与合规管理",
    },
    "circular_economy": {
        "financial": 5,
        "impact": 7,
        "name": "循环经济实践",
        "dimension": "E",
        "description": "废弃物管理与资源循环利用",
    },
}

# ========== 业务单元配置 ==========
# 新能源行业业务单元列表
BUSINESS_UNITS: List[str] = ["智能风电", "智慧储能", "绿氢解决方案", "电池制造", "供应链管理"]

# 议题与业务单元映射关系
# impact等级：高/中/低
TOPIC_BUSINESS_MAP: Dict[str, Dict[str, Any]] = {
    "carbon_emission": {
        "units": ["智能风电", "电池制造", "绿氢解决方案"],
        "impact": {"智能风电": "高", "电池制造": "中", "绿氢解决方案": "高"},
    },
    "renewable_energy": {
        "units": ["智能风电", "智慧储能", "绿氢解决方案"],
        "impact": {"智能风电": "高", "智慧储能": "中", "绿氢解决方案": "高"},
    },
    "supply_chain_carbon": {
        "units": ["供应链管理", "电池制造", "智能风电"],
        "impact": {"供应链管理": "高", "电池制造": "中", "智能风电": "中"},
    },
    "employee_safety": {
        "units": ["电池制造", "智能风电", "智慧储能"],
        "impact": {"电池制造": "高", "智能风电": "中", "智慧储能": "中"},
    },
    "employee_training": {
        "units": ["电池制造", "绿氢解决方案", "智慧储能"],
        "impact": {"电池制造": "中", "绿氢解决方案": "中", "智慧储能": "低"},
    },
    "community_investment": {
        "units": ["智能风电", "绿氢解决方案"],
        "impact": {"智能风电": "中", "绿氢解决方案": "中"},
    },
    "board_diversity": {
        "units": ["供应链管理", "电池制造", "智慧储能"],
        "impact": {"供应链管理": "中", "电池制造": "中", "智慧储能": "低"},
    },
    "esg_disclosure": {
        "units": ["电池制造", "智能风电", "绿氢解决方案", "智慧储能", "供应链管理"],
        "impact": {
            "电池制造": "高",
            "智能风电": "中",
            "绿氢解决方案": "中",
            "智慧储能": "中",
            "供应链管理": "中",
        },
    },
    "business_ethics": {
        "units": ["供应链管理", "电池制造"],
        "impact": {"供应链管理": "高", "电池制造": "中"},
    },
    "circular_economy": {
        "units": ["电池制造", "智慧储能"],
        "impact": {"电池制造": "高", "智慧储能": "中"},
    },
}

# 业务单元描述
BUSINESS_UNIT_DESCRIPTIONS: Dict[str, str] = {
    "智能风电": "风力发电机组研发、制造与运维服务",
    "智慧储能": "储能系统集成与能源管理解决方案",
    "绿氢解决方案": "电解水制氢设备及氢能应用解决方案",
    "电池制造": "动力电池及储能电池研发生产",
    "供应链管理": "原材料采购、物流与供应商管理",
}

# ========== 新能源行业特色指标配置 ==========
NEW_ENERGY_SPECIFIC_METRICS = {
    "wind_power": {
        "name": "风电指标",
        "metrics": {
            "turbine_availability": {
                "name": "风机可利用率",
                "unit": "%",
                "benchmark": 97.0,
                "description": "风力发电机组可用时间与总时间的比率",
            },
            "capacity_factor": {
                "name": "容量因子",
                "unit": "%",
                "benchmark": 35.0,
                "description": "实际发电量与理论最大发电量的比率",
            },
            "power_generation_per_unit": {
                "name": "单位装机容量发电量",
                "unit": "MWh/MW/year",
                "benchmark": 3000,
                "description": "每兆瓦装机容量年发电量",
            },
        },
    },
    "energy_storage": {
        "name": "储能指标",
        "metrics": {
            "battery_cycle_life": {
                "name": "电池循环寿命",
                "unit": "次",
                "benchmark": 6000,
                "description": "电池在容量衰减至80%前的完整充放电循环次数",
            },
            "round_trip_efficiency": {
                "name": "储能系统往返效率",
                "unit": "%",
                "benchmark": 88.0,
                "description": "充放电过程中能量保持率",
            },
            "energy_density": {
                "name": "电池能量密度",
                "unit": "Wh/kg",
                "benchmark": 250,
                "description": "单位重量的电池储能容量",
            },
        },
    },
    "green_hydrogen": {
        "name": "绿氢指标",
        "metrics": {
            "electrolysis_efficiency": {
                "name": "电解水制氢效率",
                "unit": "%",
                "benchmark": 70.0,
                "description": "电能转化为氢能的效率",
            },
            "hydrogen_purity": {
                "name": "氢气纯度",
                "unit": "%",
                "benchmark": 99.9,
                "description": "产出的氢气纯度等级",
            },
            "water_consumption_per_kg_h2": {
                "name": "单位氢气水耗",
                "unit": "L/kg",
                "benchmark": 9.0,
                "description": "生产每公斤氢气消耗的水量",
            },
        },
    },
    "green_power_trading": {
        "name": "绿电交易指标",
        "metrics": {
            "green_power_ratio": {
                "name": "绿电交易占比",
                "unit": "%",
                "benchmark": 50.0,
                "description": "绿电交易量占总电力交易量的比例",
            },
            "carbon_reduction_by_green_power": {
                "name": "绿电减排量",
                "unit": "吨CO2e/MWh",
                "benchmark": 0.5,
                "description": "每兆瓦时绿电减少的碳排放量",
            },
            "green_power_certificates": {
                "name": "绿证持有量",
                "unit": "张",
                "benchmark": 10000,
                "description": "持有的绿色电力证书数量",
            },
        },
    },
    "circular_economy": {
        "name": "循环经济指标",
        "metrics": {
            "battery_recycling_rate": {
                "name": "电池回收利用率",
                "unit": "%",
                "benchmark": 95.0,
                "description": "退役电池回收再利用的比例",
            },
            "rare_earth_recovery_rate": {
                "name": "稀土材料回收率",
                "unit": "%",
                "benchmark": 90.0,
                "description": "电池中稀土材料回收效率",
            },
            "packaging_recycling_rate": {
                "name": "包装材料回收率",
                "unit": "%",
                "benchmark": 85.0,
                "description": "产品包装材料回收再利用比例",
            },
        },
    },
}
