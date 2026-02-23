"""
一键初始化演示数据工具
下载公开的ESG报告，预跑语料处理，生成演示数据库
"""

import sys
from pathlib import Path
import requests

ROOT_DIR = Path(__file__).parent.parent
DEMO_CORPUS_DIR = ROOT_DIR / "demo_data" / "demo_corpus"


def download_demo_corpus():
    """下载演示用的公开ESG报告（示例：金风科技2023年ESG报告）"""
    print("🚀 开始初始化演示数据")
    DEMO_CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 示例：下载金风科技2023年ESG报告（公开可下载）
    # 注意：实际使用时请替换为真实的公开下载链接
    demo_urls = [
        "https://www.envision-group.com/viewer/web/viewer.html?file=//aesccdn.creatby.com/materials/files/2024ESG/%E8%BF%9C%E6%99%AF%E8%83%BD%E6%BA%902024%E5%B9%B4ESG%E6%8A%A5%E5%91%8A.pdf"
    ]
    
    if not demo_urls:
        print("⚠️  未配置演示数据下载链接，请手动将公开ESG报告放入 demo_data/demo_corpus/ 目录")
        print("✅ 演示数据目录已创建")
        return
    
    for url in demo_urls:
        file_name = url.split("/")[-1]
        file_path = DEMO_CORPUS_DIR / file_name
        if file_path.exists():
            print(f"ℹ️  演示文件已存在，跳过下载: {file_name}")
            continue
        
        print(f"📥 正在下载演示文件: {file_name}")
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            with open(file_path, "wb") as f:
                f.write(response.content)
            print(f"✅ 下载完成: {file_name}")
        except Exception as e:
            print(f"❌ 下载失败: {file_name}, 错误: {str(e)}")
    
    print("✅ 演示数据初始化完成")


def main():
    download_demo_corpus()
    sys.exit(0)


if __name__ == "__main__":
    main()