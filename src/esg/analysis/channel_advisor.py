"""沟通渠道建议器

为ESG策略提供推荐的沟通渠道建议。
"""

from typing import Dict, List, Optional


class ChannelAdvisor:
    """ESG沟通渠道建议器
    
    根据策略类型和维度推荐合适的沟通渠道。
    
    Attributes:
        channel_mappings: 预设的渠道映射规则
    """
    
    # 渠道映射规则：策略类型 -> 推荐渠道列表
    CHANNEL_MAPPINGS = {
        # 治理类策略
        "board_independence": [
            {"channel_name": "年度ESG报告", "priority": "主渠道", "reason": "披露董事会构成和多元化政策详情"},
            {"channel_name": "股东大会", "priority": "主渠道", "reason": "向股东汇报治理结构和董事变更"},
            {"channel_name": "投资者路演", "priority": "辅助渠道", "reason": "阐述董事会ESG监督能力提升"},
            {"channel_name": "公司治理公告", "priority": "辅助渠道", "reason": "发布董事会委员会设立和调整"},
        ],
        "esg_disclosure": [
            {"channel_name": "年度ESG报告", "priority": "主渠道", "reason": "核心披露载体，包含完整ESG数据和分析"},
            {"channel_name": "官网ESG专栏", "priority": "主渠道", "reason": "实时更新ESG进展和下载中心"},
            {"channel_name": "ESG评级回复", "priority": "辅助渠道", "reason": "回应MSCI、Sustainalytics等评级问询"},
            {"channel_name": "投资者说明会", "priority": "辅助渠道", "reason": "解读ESG报告亮点和应对投资者问题"},
        ],
        "ethics_compliance": [
            {"channel_name": "员工培训", "priority": "主渠道", "reason": "全员伦理培训和商业行为准则宣导"},
            {"channel_name": "年度ESG报告", "priority": "主渠道", "reason": "披露合规管理体系和举报机制"},
            {"channel_name": "内部举报热线", "priority": "辅助渠道", "reason": "提供匿名举报渠道和保护机制"},
            {"channel_name": "官网合规专栏", "priority": "辅助渠道", "reason": "公开商业行为准则和合规承诺"},
        ],
        # 环境类策略
        "carbon_management": [
            {"channel_name": "年度ESG报告", "priority": "主渠道", "reason": "年报适合详细碳排放数据披露和减排目标进展汇报"},
            {"channel_name": "官网ESG专栏", "priority": "主渠道", "reason": "实时展示碳管理数据和可视化进展"},
            {"channel_name": "ESG评级回复", "priority": "辅助渠道", "reason": "回应评级机构对碳管理的专业问询"},
            {"channel_name": "投资者路演", "priority": "辅助渠道", "reason": "向投资者阐述碳中和战略和投资价值"},
        ],
        "renewable_energy": [
            {"channel_name": "官网ESG专栏", "priority": "主渠道", "reason": "展示可再生能源项目进展和实时数据"},
            {"channel_name": "社交媒体", "priority": "主渠道", "reason": "传播绿色能源成就，提升品牌形象"},
            {"channel_name": "年度ESG报告", "priority": "辅助渠道", "reason": "汇总披露可再生能源使用比例和目标"},
            {"channel_name": "新闻发布会", "priority": "辅助渠道", "reason": "重大项目签约或并网时对外发布"},
        ],
        "circular_economy": [
            {"channel_name": "社交媒体", "priority": "主渠道", "reason": "分享循环经济案例，增强公众参与感"},
            {"channel_name": "供应商大会", "priority": "主渠道", "reason": "推动供应链伙伴参与循环经济计划"},
            {"channel_name": "年度ESG报告", "priority": "辅助渠道", "reason": "披露废弃物管理和资源利用数据"},
            {"channel_name": "社区活动", "priority": "辅助渠道", "reason": "组织回收活动，提升社区参与度"},
        ],
        # 社会类策略
        "diversity_inclusion": [
            {"channel_name": "员工大会", "priority": "主渠道", "reason": "向全员宣导多元化政策和员工资源小组"},
            {"channel_name": "社交媒体", "priority": "主渠道", "reason": "分享多元文化故事，展示包容性文化"},
            {"channel_name": "年度ESG报告", "priority": "辅助渠道", "reason": "披露员工多样性数据和薪酬公平性"},
            {"channel_name": "招聘网站", "priority": "辅助渠道", "reason": "展示多元化承诺，吸引多样化人才"},
        ],
        "employee_development": [
            {"channel_name": "员工培训", "priority": "主渠道", "reason": "直接开展技能培训和ESG意识课程"},
            {"channel_name": "内部通讯", "priority": "主渠道", "reason": "发布培训机会和员工发展成功案例"},
            {"channel_name": "年度ESG报告", "priority": "辅助渠道", "reason": "披露培训投入和覆盖率数据"},
            {"channel_name": "员工内网", "priority": "辅助渠道", "reason": "提供在线学习资源和个人发展工具"},
        ],
        "supply_chain_human_rights": [
            {"channel_name": "供应商大会", "priority": "主渠道", "reason": "宣导供应商行为准则和审核要求"},
            {"channel_name": "年度ESG报告", "priority": "主渠道", "reason": "披露供应链人权尽职调查进展"},
            {"channel_name": "供应商培训", "priority": "辅助渠道", "reason": "帮助供应商理解和改善人权表现"},
            {"channel_name": "官网供应商门户", "priority": "辅助渠道", "reason": "发布行为准则和审核标准"},
        ],
    }
    
    # 维度默认渠道
    DIMENSION_DEFAULT_CHANNELS = {
        "E": [
            {"channel_name": "年度ESG报告", "priority": "主渠道", "reason": "环境议题适合详细数据披露和进展汇报"},
            {"channel_name": "官网ESG专栏", "priority": "主渠道", "reason": "实时展示环境管理数据和可视化进展"},
            {"channel_name": "ESG评级回复", "priority": "辅助渠道", "reason": "回应评级机构对环境议题的专业问询"},
        ],
        "S": [
            {"channel_name": "年度ESG报告", "priority": "主渠道", "reason": "披露社会议题数据和员工相关指标"},
            {"channel_name": "员工大会", "priority": "主渠道", "reason": "直接向员工传达社会相关政策和举措"},
            {"channel_name": "社交媒体", "priority": "辅助渠道", "reason": "分享社会责任故事和员工成就"},
        ],
        "G": [
            {"channel_name": "年度ESG报告", "priority": "主渠道", "reason": "披露治理结构和董事会信息"},
            {"channel_name": "股东大会", "priority": "主渠道", "reason": "向股东汇报治理变更和重要决策"},
            {"channel_name": "投资者路演", "priority": "辅助渠道", "reason": "阐述公司治理优势和投资者权益保护"},
        ],
    }
    
    # 渠道图标映射
    CHANNEL_ICONS = {
        "年度ESG报告": "📊",
        "官网ESG专栏": "🌐",
        "社交媒体": "📱",
        "投资者路演": "🎯",
        "员工培训": "🎓",
        "股东大会": "🏛️",
        "ESG评级回复": "📋",
        "新闻发布会": "📰",
        "供应商大会": "🤝",
        "社区活动": "🎉",
        "员工大会": "👥",
        "内部通讯": "📧",
        "员工内网": "💻",
        "招聘网站": "🔍",
        "内部举报热线": "📞",
        "官网合规专栏": "⚖️",
        "公司治理公告": "📢",
        "投资者说明会": "💼",
        "供应商培训": "📚",
        "官网供应商门户": "🏭",
    }
    
    def __init__(self):
        """初始化渠道建议器"""
        pass
    
    def get_channels(self, strategy_type: str) -> List[Dict[str, str]]:
        """获取策略类型对应的推荐渠道
        
        Args:
            strategy_type: 策略类型ID（如"carbon_management"）
            
        Returns:
            推荐渠道列表，每个渠道包含channel_name、priority、reason
        """
        return self.CHANNEL_MAPPINGS.get(strategy_type, [])
    
    def get_channels_for_dimension(self, dimension: str) -> List[Dict[str, str]]:
        """获取维度对应的默认推荐渠道
        
        Args:
            dimension: ESG维度（"E"/"S"/"G"）
            
        Returns:
            推荐渠道列表
        """
        return self.DIMENSION_DEFAULT_CHANNELS.get(dimension, [])
    
    def get_channel_icon(self, channel_name: str) -> str:
        """获取渠道对应的图标
        
        Args:
            channel_name: 渠道名称
            
        Returns:
            图标emoji
        """
        return self.CHANNEL_ICONS.get(channel_name, "📢")
    
    def filter_channels_by_priority(
        self, 
        channels: List[Dict[str, str]], 
        priority: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """按优先级筛选渠道
        
        Args:
            channels: 渠道列表
            priority: 优先级（"主渠道"/"辅助渠道"），None表示不过滤
            
        Returns:
            筛选后的渠道列表
        """
        if priority is None:
            return channels
        return [c for c in channels if c.get("priority") == priority]
    
    def get_primary_channels(self, strategy_type: str) -> List[Dict[str, str]]:
        """获取主渠道列表
        
        Args:
            strategy_type: 策略类型ID
            
        Returns:
            主渠道列表
        """
        channels = self.get_channels(strategy_type)
        return self.filter_channels_by_priority(channels, "主渠道")
    
    def get_supporting_channels(self, strategy_type: str) -> List[Dict[str, str]]:
        """获取辅助渠道列表
        
        Args:
            strategy_type: 策略类型ID
            
        Returns:
            辅助渠道列表
        """
        channels = self.get_channels(strategy_type)
        return self.filter_channels_by_priority(channels, "辅助渠道")
