"""范围3排放核算模块

基于GHG Protocol Corporate Value Chain (Scope 3) Accounting and Reporting Standard
实现完整的15个排放类别核算、数据质量评估和CDP对标。

Reference: https://ghgprotocol.org/standards/scope-3-standard
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class Scope3Category(Enum):
    """范围3排放类别（GHG Protocol标准）"""

    # 上游排放（Upstream）
    PURCHASED_GOODS_SERVICES = 1  # 外购商品和服务
    CAPITAL_GOODS = 2  # 资本商品
    FUEL_ENERGY_ACTIVITIES = 3  # 燃料和能源相关活动
    UPSTREAM_TRANSPORTATION = 4  # 上游运输和配送
    WASTE_GENERATED = 5  # 运营中产生的废物
    BUSINESS_TRAVEL = 6  # 商务旅行
    EMPLOYEE_COMMUTING = 7  # 员工通勤
    UPSTREAM_LEASED_ASSETS = 8  # 上游租赁资产

    # 下游排放（Downstream）
    DOWNSTREAM_TRANSPORTATION = 9  # 下游运输和配送
    PROCESSING_OF_SOLD_PRODUCTS = 10  # 售出产品的加工
    USE_OF_SOLD_PRODUCTS = 11  # 售出产品的使用
    END_OF_LIFE_TREATMENT = 12  # 售出产品的报废处理
    DOWNSTREAM_LEASED_ASSETS = 13  # 下游租赁资产
    FRANCHISES = 14  # 特许经营权
    INVESTMENTS = 15  # 投资


# 类别名称和描述
SCOPE3_CATEGORY_INFO = {
    Scope3Category.PURCHASED_GOODS_SERVICES: {
        "name": "外购商品和服务",
        "name_en": "Purchased Goods and Services",
        "description": "上游供应链中外购商品和服务的生产相关排放",
        "type": "upstream",
        "relevance": "high",  # 对新能源企业的重要性
    },
    Scope3Category.CAPITAL_GOODS: {
        "name": "资本商品",
        "name_en": "Capital Goods",
        "description": "资本设备的生产相关排放（寿命>1年）",
        "type": "upstream",
        "relevance": "high",
    },
    Scope3Category.FUEL_ENERGY_ACTIVITIES: {
        "name": "燃料和能源相关活动",
        "name_en": "Fuel and Energy-Related Activities",
        "description": "未纳入范围1和2的燃料和能源相关排放",
        "type": "upstream",
        "relevance": "medium",
    },
    Scope3Category.UPSTREAM_TRANSPORTATION: {
        "name": "上游运输和配送",
        "name_en": "Upstream Transportation and Distribution",
        "description": "原材料和组件的运输排放",
        "type": "upstream",
        "relevance": "high",
    },
    Scope3Category.WASTE_GENERATED: {
        "name": "运营中产生的废物",
        "name_en": "Waste Generated in Operations",
        "description": "运营过程中产生废物的处理和处置排放",
        "type": "upstream",
        "relevance": "medium",
    },
    Scope3Category.BUSINESS_TRAVEL: {
        "name": "商务旅行",
        "name_en": "Business Travel",
        "description": "员工商务旅行产生的排放",
        "type": "upstream",
        "relevance": "low",
    },
    Scope3Category.EMPLOYEE_COMMUTING: {
        "name": "员工通勤",
        "name_en": "Employee Commuting",
        "description": "员工通勤产生的排放",
        "type": "upstream",
        "relevance": "low",
    },
    Scope3Category.UPSTREAM_LEASED_ASSETS: {
        "name": "上游租赁资产",
        "name_en": "Upstream Leased Assets",
        "description": "承租方运营的租赁资产产生的排放",
        "type": "upstream",
        "relevance": "low",
    },
    Scope3Category.DOWNSTREAM_TRANSPORTATION: {
        "name": "下游运输和配送",
        "name_en": "Downstream Transportation and Distribution",
        "description": "产品交付给客户的运输排放",
        "type": "downstream",
        "relevance": "high",
    },
    Scope3Category.PROCESSING_OF_SOLD_PRODUCTS: {
        "name": "售出产品的加工",
        "name_en": "Processing of Sold Products",
        "description": "售出产品由第三方进一步加工产生的排放",
        "type": "downstream",
        "relevance": "medium",
    },
    Scope3Category.USE_OF_SOLD_PRODUCTS: {
        "name": "售出产品的使用",
        "name_en": "Use of Sold Products",
        "description": "售出产品在客户使用过程中产生的排放",
        "type": "downstream",
        "relevance": "high",
    },
    Scope3Category.END_OF_LIFE_TREATMENT: {
        "name": "售出产品的报废处理",
        "name_en": "End-of-Life Treatment of Sold Products",
        "description": "售出产品报废处理产生的排放",
        "type": "downstream",
        "relevance": "high",
    },
    Scope3Category.DOWNSTREAM_LEASED_ASSETS: {
        "name": "下游租赁资产",
        "name_en": "Downstream Leased Assets",
        "description": "出租方拥有的租赁资产产生的排放",
        "type": "downstream",
        "relevance": "low",
    },
    Scope3Category.FRANCHISES: {
        "name": "特许经营权",
        "name_en": "Franchises",
        "description": "特许经营业务产生的排放",
        "type": "downstream",
        "relevance": "low",
    },
    Scope3Category.INVESTMENTS: {
        "name": "投资",
        "name_en": "Investments",
        "description": "投资业务产生的排放（金融机构重点关注）",
        "type": "downstream",
        "relevance": "low",
    },
}


# 新能源行业各排放类别的重要性权重
NEW_ENERGY_SECTOR_RELEVANCE = {
    "wind_power": {
        Scope3Category.PURCHASED_GOODS_SERVICES: 0.20,
        Scope3Category.CAPITAL_GOODS: 0.15,
        Scope3Category.UPSTREAM_TRANSPORTATION: 0.10,
        Scope3Category.DOWNSTREAM_TRANSPORTATION: 0.08,
        Scope3Category.USE_OF_SOLD_PRODUCTS: 0.25,  # 风电场运营
        Scope3Category.END_OF_LIFE_TREATMENT: 0.12,  # 风机叶片回收
        Scope3Category.PROCESSING_OF_SOLD_PRODUCTS: 0.05,
        Scope3Category.FUEL_ENERGY_ACTIVITIES: 0.03,
        Scope3Category.WASTE_GENERATED: 0.02,
    },
    "solar_pv": {
        Scope3Category.PURCHASED_GOODS_SERVICES: 0.25,  # 硅料、组件
        Scope3Category.CAPITAL_GOODS: 0.10,
        Scope3Category.UPSTREAM_TRANSPORTATION: 0.08,
        Scope3Category.DOWNSTREAM_TRANSPORTATION: 0.07,
        Scope3Category.USE_OF_SOLD_PRODUCTS: 0.20,  # 光伏电站运营
        Scope3Category.END_OF_LIFE_TREATMENT: 0.15,  # 组件回收
        Scope3Category.PROCESSING_OF_SOLD_PRODUCTS: 0.08,
        Scope3Category.FUEL_ENERGY_ACTIVITIES: 0.04,
        Scope3Category.WASTE_GENERATED: 0.03,
    },
    "energy_storage": {
        Scope3Category.PURCHASED_GOODS_SERVICES: 0.30,  # 电池材料（锂、钴、镍）
        Scope3Category.CAPITAL_GOODS: 0.08,
        Scope3Category.UPSTREAM_TRANSPORTATION: 0.08,
        Scope3Category.DOWNSTREAM_TRANSPORTATION: 0.07,
        Scope3Category.USE_OF_SOLD_PRODUCTS: 0.15,
        Scope3Category.END_OF_LIFE_TREATMENT: 0.18,  # 电池回收
        Scope3Category.PROCESSING_OF_SOLD_PRODUCTS: 0.07,
        Scope3Category.FUEL_ENERGY_ACTIVITIES: 0.04,
        Scope3Category.WASTE_GENERATED: 0.03,
    },
    "green_hydrogen": {
        Scope3Category.PURCHASED_GOODS_SERVICES: 0.20,  # 电解槽材料
        Scope3Category.CAPITAL_GOODS: 0.15,
        Scope3Category.UPSTREAM_TRANSPORTATION: 0.10,
        Scope3Category.DOWNSTREAM_TRANSPORTATION: 0.08,
        Scope3Category.USE_OF_SOLD_PRODUCTS: 0.25,  # 氢能使用
        Scope3Category.END_OF_LIFE_TREATMENT: 0.08,
        Scope3Category.PROCESSING_OF_SOLD_PRODUCTS: 0.07,
        Scope3Category.FUEL_ENERGY_ACTIVITIES: 0.05,
        Scope3Category.WASTE_GENERATED: 0.02,
    },
}


class DataQuality(Enum):
    """数据质量等级"""

    HIGH = "high"  # 供应商特定数据/实测数据
    MEDIUM = "medium"  # 混合数据（部分特定+部分行业平均）
    LOW = "low"  # 行业平均数据
    EXTRAPOLATED = "extrapolated"  # 外推/估算数据


@dataclass
class Scope3CategoryData:
    """单个范围3类别的排放数据

    Attributes:
        category: 排放类别
        emissions: 排放量（吨CO2e）
        calculation_method: 计算方法说明
        data_sources: 数据来源列表
        data_quality: 数据质量等级
        uncertainty_range: 不确定性范围（如±15%）
        activity_data: 活动数据（如物料重量、运输吨公里等）
        emission_factor: 排放因子
        coverage_percentage: 数据覆盖率（%）
        exclusions: 排除项说明
    """

    category: Scope3Category
    emissions: Optional[float] = None
    calculation_method: str = ""
    data_sources: List[str] = field(default_factory=list)
    data_quality: DataQuality = DataQuality.LOW
    uncertainty_range: Optional[float] = None  # 如 0.15 表示 ±15%
    activity_data: Optional[float] = None  # 活动数据值
    activity_unit: str = ""  # 活动数据单位
    emission_factor: Optional[float] = None  # 排放因子
    emission_factor_source: str = ""  # 排放因子来源
    coverage_percentage: float = 0.0  # 数据覆盖率
    exclusions: List[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "category_id": self.category.value,
            "category_name": SCOPE3_CATEGORY_INFO[self.category]["name"],
            "category_name_en": SCOPE3_CATEGORY_INFO[self.category]["name_en"],
            "emissions_tco2e": self.emissions,
            "calculation_method": self.calculation_method,
            "data_quality": self.data_quality.value,
            "uncertainty_range": self.uncertainty_range,
            "activity_data": self.activity_data,
            "activity_unit": self.activity_unit,
            "emission_factor": self.emission_factor,
            "coverage_percentage": self.coverage_percentage,
            "exclusions": self.exclusions,
            "notes": self.notes,
        }


@dataclass
class Scope3Inventory:
    """范围3排放清单

    存储企业完整的范围3排放数据，支持15个类别的核算。

    Attributes:
        reporting_year: 报告年份
        company_name: 公司名称
        sector: 行业分类（wind_power/solar_pv/energy_storage/green_hydrogen）
        categories: 各排放类别数据
        total_scope3: 范围3排放总量
        scope1_2_total: 范围1+2排放总量（用于计算占比）
        verification_status: 第三方核证状态
        verification_provider: 核证机构
    """

    reporting_year: str
    company_name: str
    sector: str = "new_energy_composite"
    categories: Dict[Scope3Category, Scope3CategoryData] = field(default_factory=dict)
    scope1_2_total: Optional[float] = None
    verification_status: str = "unverified"  # unverified/limited/reasonable
    verification_provider: str = ""
    prepared_by: str = ""
    preparation_date: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self):
        """初始化后确保所有类别都存在"""
        for cat in Scope3Category:
            if cat not in self.categories:
                self.categories[cat] = Scope3CategoryData(category=cat)

    def get_category(self, category: Scope3Category) -> Scope3CategoryData:
        """获取指定类别的数据"""
        return self.categories.get(category, Scope3CategoryData(category=category))

    def set_category(self, data: Scope3CategoryData) -> None:
        """设置类别的数据"""
        self.categories[data.category] = data

    def get_total_emissions(self) -> Optional[float]:
        """计算范围3排放总量

        Returns:
            总排放量（吨CO2e）或None（如果数据不完整）
        """
        total = 0.0
        has_data = False

        for cat_data in self.categories.values():
            if cat_data.emissions is not None:
                total += cat_data.emissions
                has_data = True

        return total if has_data else None

    def get_upstream_emissions(self) -> Optional[float]:
        """计算上游排放总量（类别1-8）"""
        upstream_cats = [c for c in Scope3Category if SCOPE3_CATEGORY_INFO[c]["type"] == "upstream"]
        total = 0.0
        has_data = False

        for cat in upstream_cats:
            cat_data = self.categories.get(cat)
            if cat_data and cat_data.emissions is not None:
                total += cat_data.emissions
                has_data = True

        return total if has_data else None

    def get_downstream_emissions(self) -> Optional[float]:
        """计算下游排放总量（类别9-15）"""
        downstream_cats = [
            c for c in Scope3Category if SCOPE3_CATEGORY_INFO[c]["type"] == "downstream"
        ]
        total = 0.0
        has_data = False

        for cat in downstream_cats:
            cat_data = self.categories.get(cat)
            if cat_data and cat_data.emissions is not None:
                total += cat_data.emissions
                has_data = True

        return total if has_data else None

    def get_scope3_intensity(self, revenue_millions: float) -> Optional[float]:
        """计算范围3排放强度

        Args:
            revenue_millions: 营收（百万元）

        Returns:
            排放强度（吨CO2e/百万元营收）
        """
        total = self.get_total_emissions()
        if total is None or revenue_millions <= 0:
            return None
        return total / revenue_millions

    def get_coverage_percentage(self) -> float:
        """计算整体数据覆盖率"""
        total = self.get_total_emissions()
        if total is None or total == 0:
            return 0.0

        covered = 0.0
        for cat_data in self.categories.values():
            if cat_data.emissions is not None and cat_data.coverage_percentage > 0:
                covered += cat_data.emissions * (cat_data.coverage_percentage / 100)

        return (covered / total) * 100

    def get_data_quality_score(self) -> float:
        """计算数据质量评分（0-100）"""
        quality_scores = {
            DataQuality.HIGH: 100,
            DataQuality.MEDIUM: 70,
            DataQuality.LOW: 40,
            DataQuality.EXTRAPOLATED: 20,
        }

        total = self.get_total_emissions()
        if total is None or total == 0:
            return 0.0

        weighted_score = 0.0
        for cat_data in self.categories.values():
            if cat_data.emissions is not None and cat_data.emissions > 0:
                weight = cat_data.emissions / total
                score = quality_scores.get(cat_data.data_quality, 0)
                weighted_score += weight * score

        return weighted_score

    def get_significant_categories(self, threshold: float = 0.05) -> List[Scope3Category]:
        """获取重要排放类别（占比>阈值）

        Args:
            threshold: 占比阈值（如0.05表示5%）

        Returns:
            重要类别列表
        """
        total = self.get_total_emissions()
        if total is None or total == 0:
            return []

        significant = []
        for cat, cat_data in self.categories.items():
            if cat_data.emissions is not None and cat_data.emissions / total >= threshold:
                significant.append(cat)

        # 按排放量排序
        significant.sort(key=lambda c: self.categories[c].emissions or 0, reverse=True)
        return significant

    def calculate_completeness_score(self) -> float:
        """计算核算完整性评分（基于行业相关性）"""
        relevance_map = NEW_ENERGY_SECTOR_RELEVANCE.get(
            self.sector, NEW_ENERGY_SECTOR_RELEVANCE.get("wind_power")
        )

        total_relevance = sum(relevance_map.values())
        covered_relevance = 0.0

        for cat, relevance in relevance_map.items():
            cat_data = self.categories.get(cat)
            if cat_data and cat_data.emissions is not None:
                covered_relevance += relevance

        return (covered_relevance / total_relevance) * 100 if total_relevance > 0 else 0

    def get_cdp_alignment_score(self) -> Dict[str, Any]:
        """计算CDP范围3披露对齐评分

        CDP评分标准：
        - 披露所有相关类别（30分）
        - 数据质量（25分）
        - 覆盖重要类别（25分）
        - 有减排目标（20分）

        Returns:
            CDP对齐评分详情
        """
        score = 0
        details = []

        # 1. 披露完整性（30分）
        relevance_map = NEW_ENERGY_SECTOR_RELEVANCE.get(
            self.sector, NEW_ENERGY_SECTOR_RELEVANCE.get("wind_power")
        )
        disclosed_high = sum(
            1
            for cat in relevance_map.keys()
            if self.categories.get(cat) and self.categories[cat].emissions is not None
        )
        total_high = len(relevance_map)

        disclosure_ratio = disclosed_high / total_high if total_high > 0 else 0
        disclosure_score = min(30, disclosure_ratio * 30)
        score += disclosure_score
        details.append(
            f"披露完整性: {disclosed_high}/{total_high} 重要类别 ({disclosure_score:.0f}分)"
        )

        # 2. 数据质量（25分）
        quality_score = self.get_data_quality_score() / 4  # 转换为25分制
        score += quality_score
        details.append(f"数据质量: {quality_score:.0f}分")

        # 3. 数据覆盖率（25分）
        coverage = self.get_coverage_percentage()
        coverage_score = min(25, coverage / 4)
        score += coverage_score
        details.append(f"数据覆盖率: {coverage:.0f}% ({coverage_score:.0f}分)")

        # 4. 第三方核证（20分）
        if self.verification_status == "reasonable":
            score += 20
            details.append("第三方核证: 合理保证 (20分)")
        elif self.verification_status == "limited":
            score += 12
            details.append("第三方核证: 有限保证 (12分)")
        else:
            details.append("第三方核证: 无 (0分)")

        # 确定CDP等级
        if score >= 80:
            level = "A"
        elif score >= 65:
            level = "B"
        elif score >= 50:
            level = "C"
        else:
            level = "D"

        return {
            "total_score": score,
            "cdp_level": level,
            "details": details,
            "completeness": self.calculate_completeness_score(),
            "data_quality": self.get_data_quality_score(),
            "coverage": self.get_coverage_percentage(),
        }

    def to_dict(self) -> Dict[str, Any]:
        """转换为完整字典"""
        return {
            "company_name": self.company_name,
            "reporting_year": self.reporting_year,
            "sector": self.sector,
            "total_scope3_tco2e": self.get_total_emissions(),
            "upstream_emissions_tco2e": self.get_upstream_emissions(),
            "downstream_emissions_tco2e": self.get_downstream_emissions(),
            "scope1_2_total_tco2e": self.scope1_2_total,
            "scope3_to_scope12_ratio": (
                self.get_total_emissions() / self.scope1_2_total
                if self.scope1_2_total and self.scope1_2_total > 0
                else None
            ),
            "data_quality_score": self.get_data_quality_score(),
            "coverage_percentage": self.get_coverage_percentage(),
            "completeness_score": self.calculate_completeness_score(),
            "verification_status": self.verification_status,
            "verification_provider": self.verification_provider,
            "categories": {cat.value: data.to_dict() for cat, data in self.categories.items()},
            "significant_categories": [
                {
                    "category_id": cat.value,
                    "name": SCOPE3_CATEGORY_INFO[cat]["name"],
                    "emissions": self.categories[cat].emissions,
                }
                for cat in self.get_significant_categories()
            ],
        }


class Scope3Calculator:
    """范围3排放计算器

    提供各种范围3排放类别的计算方法。
    """

    @staticmethod
    def calculate_category1_purchased_goods(
        material_quantities: Dict[str, float],  # 物料重量(kg)
        emission_factors: Dict[str, float],  # 排放因子(kgCO2e/kg)
    ) -> Tuple[float, Dict[str, Any]]:
        """计算类别1：外购商品和服务

        Args:
            material_quantities: 物料数量，如{"钢材": 1000, "铜": 500}
            emission_factors: 排放因子，如{"钢材": 2.3, "铜": 3.5}

        Returns:
            (总排放量, 详细数据)
        """
        total = 0.0
        breakdown = {}

        for material, quantity in material_quantities.items():
            ef = emission_factors.get(material, 0)
            emissions = quantity * ef
            total += emissions
            breakdown[material] = {
                "quantity_kg": quantity,
                "emission_factor_kgco2e_per_kg": ef,
                "emissions_kgco2e": emissions,
            }

        return total / 1000, {  # 转换为吨CO2e
            "method": "供应商特定排放因子法",
            "breakdown": breakdown,
            "total_tco2e": total / 1000,
        }

    @staticmethod
    def calculate_category4_upstream_transport(
        transport_data: List[Dict[str, Any]],  # 运输数据列表
    ) -> Tuple[float, Dict[str, Any]]:
        """计算类别4：上游运输

        Args:
            transport_data: 运输数据列表，每项包含：
                - mode: 运输方式（road/rail/sea/air）
                - distance_km: 距离（公里）
                - weight_tonnes: 重量（吨）

        Returns:
            (总排放量, 详细数据)
        """
        # 运输排放因子（kgCO2e/吨公里）
        transport_efs = {
            "road": 0.062,
            "rail": 0.022,
            "sea": 0.008,
            "air": 0.602,
        }

        total = 0.0
        breakdown = []

        for item in transport_data:
            mode = item.get("mode", "road")
            distance = item.get("distance_km", 0)
            weight = item.get("weight_tonnes", 0)

            ef = transport_efs.get(mode, transport_efs["road"])
            emissions = distance * weight * ef
            total += emissions

            breakdown.append(
                {
                    "mode": mode,
                    "distance_km": distance,
                    "weight_tonnes": weight,
                    "ton_km": distance * weight,
                    "emissions_kgco2e": emissions,
                }
            )

        return total / 1000, {
            "method": "基于吨公里的运输排放计算",
            "breakdown": breakdown,
            "total_tco2e": total / 1000,
        }

    @staticmethod
    def calculate_category11_use_of_sold_products(
        products: List[Dict[str, Any]],
        lifetime_years: float,
    ) -> Tuple[float, Dict[str, Any]]:
        """计算类别11：售出产品的使用

        适用于风电/光伏设备制造商（设备运营期排放）

        Args:
            products: 产品销售数据，每项包含：
                - product_type: 产品类型（wind_turbine/solar_panel/battery等）
                - capacity_mw: 容量（MW）
                - annual_generation_mwh: 年发电量（MWh）
                - grid_carbon_intensity: 电网碳排放因子（kgCO2e/kWh）
            lifetime_years: 产品寿命（年）
        """
        total = 0.0
        breakdown = []

        for product in products:
            product_type = product.get("product_type", "")
            capacity = product.get("capacity_mw", 0)
            generation = product.get("annual_generation_mwh", 0)
            grid_ef = product.get("grid_carbon_intensity", 0.0005)  # 默认0.5kgCO2e/kWh

            # 计算避免/产生的排放
            # 风电/光伏设备：产生清洁电力，避免电网排放
            if product_type in ("wind_turbine", "solar_panel"):
                # 避免排放 = 发电量 × 电网因子 × 寿命
                avoided_emissions = generation * 1000 * grid_ef * lifetime_years
                actual_emissions = 0  # 运营期几乎零排放
                net_emissions = actual_emissions - avoided_emissions  # 负值表示净减排
            else:
                # 其他设备可能有运营排放
                net_emissions = 0

            total += net_emissions
            breakdown.append(
                {
                    "product_type": product_type,
                    "capacity_mw": capacity,
                    "lifetime_years": lifetime_years,
                    "annual_generation_mwh": generation,
                    "avoided_emissions_tco2e": (
                        avoided_emissions / 1000
                        if product_type in ("wind_turbine", "solar_panel")
                        else 0
                    ),
                }
            )

        return total / 1000, {
            "method": "产品使用期排放/避免排放计算",
            "breakdown": breakdown,
            "total_tco2e": total / 1000,
            "note": "负值表示净减排贡献",
        }

    @staticmethod
    def calculate_category12_end_of_life(
        products: List[Dict[str, Any]],
        recycling_rates: Dict[str, float],
    ) -> Tuple[float, Dict[str, Any]]:
        """计算类别12：产品报废处理

        Args:
            products: 产品报废数据，每项包含：
                - product_type: 产品类型
                - weight_tonnes: 产品重量（吨）
                - material_composition: 材料组成比例
            recycling_rates: 各材料回收率
        """
        # 报废处理排放因子（简化示例）
        eol_efs = {
            "steel": 0.5,  # 吨CO2e/吨材料
            "aluminum": 2.0,
            "copper": 1.5,
            "glass": 0.3,
            "silicon": 5.0,
            "lithium": 10.0,
            "blade_composite": 3.0,  # 风机叶片复合材料
            "battery": 8.0,
        }

        total = 0.0
        breakdown = []

        for product in products:
            product_type = product.get("product_type", "")
            weight = product.get("weight_tonnes", 0)
            composition = product.get("material_composition", {})

            product_emissions = 0.0
            material_breakdown = {}

            for material, ratio in composition.items():
                material_weight = weight * ratio
                ef = eol_efs.get(material, 1.0)
                recycling_rate = recycling_rates.get(material, 0.5)

                # 考虑回收率（回收减少排放）
                effective_ef = ef * (1 - recycling_rate * 0.7)  # 回收可减少70%排放
                emissions = material_weight * effective_ef
                product_emissions += emissions

                material_breakdown[material] = {
                    "weight_tonnes": material_weight,
                    "recycling_rate": recycling_rate,
                    "emissions_tco2e": emissions,
                }

            total += product_emissions
            breakdown.append(
                {
                    "product_type": product_type,
                    "total_weight_tonnes": weight,
                    "emissions_tco2e": product_emissions,
                    "materials": material_breakdown,
                }
            )

        return total, {
            "method": "基于材料组成的报废处理排放计算",
            "breakdown": breakdown,
            "total_tco2e": total,
        }


def create_empty_inventory(company_name: str, year: str, sector: str) -> Scope3Inventory:
    """创建空的范围3排放清单

    Args:
        company_name: 公司名称
        year: 报告年份
        sector: 行业分类

    Returns:
        空的Scope3Inventory对象
    """
    return Scope3Inventory(
        reporting_year=year,
        company_name=company_name,
        sector=sector,
    )


# 便捷函数
def quick_calculate_scope3_summary(inventory: Scope3Inventory) -> Dict[str, Any]:
    """快速计算范围3排放汇总"""
    return {
        "total_scope3": inventory.get_total_emissions(),
        "upstream": inventory.get_upstream_emissions(),
        "downstream": inventory.get_downstream_emissions(),
        "data_quality": inventory.get_data_quality_score(),
        "coverage": inventory.get_coverage_percentage(),
        "completeness": inventory.calculate_completeness_score(),
    }
