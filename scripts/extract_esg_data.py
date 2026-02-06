# -*- coding: utf-8 -*-
"""
ESG数据提取脚本
从data目录中的PDF报告提取结构化数据并保存
"""
import os
import sys

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from new_modules.esg_data_extractor import extract_and_save_all_data


def main():
    print("=" * 60)
    print("🔍 ESG数据提取工具")
    print("=" * 60)
    
    # 检查数据目录
    data_path = os.path.join(project_root, "data")
    if not os.path.exists(data_path):
        print(f"❌ 数据目录不存在: {data_path}")
        return
    
    # 列出可用的PDF文件
    pdf_files = [f for f in os.listdir(data_path) if f.endswith('.pdf')]
    
    if not pdf_files:
        print(f"❌ 未找到PDF文件，请确保ESG报告已放入 {data_path} 目录")
        return
    
    print(f"\n📁 发现 {len(pdf_files)} 个PDF文件:")
    for pdf in pdf_files:
        print(f"   • {pdf}")
    
    print("\n⏳ 开始提取数据...")
    print("-" * 60)
    
    try:
        # 执行数据提取
        extractor = extract_and_save_all_data()
        
        print("\n" + "=" * 60)
        print("✅ 数据提取完成!")
        print("=" * 60)
        
        # 显示提取结果摘要
        if extractor.extracted_data:
            print(f"\n📊 成功提取 {len(extractor.extracted_data)} 份报告数据:")
            for key, metrics in extractor.extracted_data.items():
                print(f"   • {metrics.company_name} ({metrics.year})")
                # 显示关键指标
                key_metrics = []
                if metrics.carbon_emissions:
                    key_metrics.append(f"碳排放: {metrics.carbon_emissions:.0f}吨")
                if metrics.renewable_energy_ratio:
                    key_metrics.append(f"可再生能源: {metrics.renewable_energy_ratio:.1f}%")
                if metrics.employee_count:
                    key_metrics.append(f"员工数: {metrics.employee_count}")
                if key_metrics:
                    print(f"     关键指标: {', '.join(key_metrics)}")
        
        # 显示数据文件位置
        output_file = os.path.join(data_path, "extracted_esg_data.json")
        print(f"\n💾 数据已保存到: {output_file}")
        
        # 提示下一步操作
        print("\n📋 下一步操作建议:")
        print("   1. 运行应用: python app.py")
        print("   2. 系统将自动使用提取的真实数据进行分析")
        
    except Exception as e:
        print(f"\n❌ 数据提取失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())