#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目代码统计工具
统计指定目录下所有 .py 文件的数量和代码行数
"""

import os
import sys
import argparse
from pathlib import Path
from collections import defaultdict


class CodeStats:
    def __init__(self):
        self.total_files = 0
        self.total_lines = 0
        self.code_lines = 0      # 实际代码行
        self.blank_lines = 0     # 空行
        self.comment_lines = 0   # 注释行
        self.file_details = []   # 单个文件详情
        
    def add_file(self, filepath, lines, code, blank, comment):
        self.total_files += 1
        self.total_lines += lines
        self.code_lines += code
        self.blank_lines += blank
        self.comment_lines += comment
        self.file_details.append({
            'path': filepath,
            'total': lines,
            'code': code,
            'blank': blank,
            'comment': comment
        })


def analyze_file(filepath):
    """分析单个 Python 文件的行数统计"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"警告: 无法读取文件 {filepath}: {e}")
        return None
    
    total_lines = len(lines)
    code_lines = 0
    blank_lines = 0
    comment_lines = 0
    in_multiline_string = False
    
    for line in lines:
        stripped = line.strip()
        
        # 空行检测
        if not stripped:
            blank_lines += 1
            continue
            
        # 多行字符串检测 (""" 或 ''')
        if '"""' in stripped or "'''" in stripped:
            # 简单处理：切换多行字符串状态
            # 注意：这不会处理所有边界情况，但足够日常使用
            quote_count = stripped.count('"""') + stripped.count("'''")
            if quote_count % 2 == 1:
                in_multiline_string = not in_multiline_string
                
        if in_multiline_string:
            comment_lines += 1
            continue
            
        # 单行注释检测
        if stripped.startswith('#'):
            comment_lines += 1
        else:
            code_lines += 1
            
    return {
        'total': total_lines,
        'code': code_lines,
        'blank': blank_lines,
        'comment': comment_lines
    }


def scan_directory(directory, exclude_dirs=None, exclude_files=None):
    """
    递归扫描目录统计 Python 文件
    
    Args:
        directory: 目标目录路径
        exclude_dirs: 要排除的目录名列表 (如 ['.git', '__pycache__', 'venv'])
        exclude_files: 要排除的文件模式列表
    """
    if exclude_dirs is None:
        exclude_dirs = {'.git', '__pycache__', '.pytest_cache', '.mypy_cache', 
                       'venv', '.venv', 'env', 'node_modules', '.idea', '.vscode'}
    if exclude_files is None:
        exclude_files = set()
        
    stats = CodeStats()
    directory = Path(directory).resolve()
    
    if not directory.exists():
        print(f"错误: 目录不存在 {directory}")
        return None
        
    # 按目录分组的统计
    dir_stats = defaultdict(lambda: {'files': 0, 'lines': 0})
    
    for root, dirs, files in os.walk(directory):
        # 排除指定目录
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        current_dir = Path(root)
        relative_dir = current_dir.relative_to(directory)
        
        for filename in files:
            if filename.endswith('.py') and filename not in exclude_files:
                filepath = current_dir / filename
                relative_path = filepath.relative_to(directory)
                
                result = analyze_file(filepath)
                if result:
                    stats.add_file(
                        str(relative_path),
                        result['total'],
                        result['code'],
                        result['blank'],
                        result['comment']
                    )
                    
                    dir_stats[str(relative_dir)]['files'] += 1
                    dir_stats[str(relative_dir)]['lines'] += result['total']
    
    return stats, dir_stats


def print_results(stats, dir_stats, top_n=10):
    """格式化输出统计结果"""
    if not stats or stats.total_files == 0:
        print("未找到 Python 文件")
        return
        
    print("\n" + "="*70)
    print(f"{'Python 项目代码统计报告':^70}")
    print("="*70)
    
    # 总体统计
    print(f"\n📊 总体统计:")
    print(f"   文件总数: {stats.total_files} 个")
    print(f"   总行数:   {stats.total_lines:,} 行")
    print(f"   代码行:   {stats.code_lines:,} 行 ({stats.code_lines/stats.total_lines*100:.1f}%)")
    print(f"   空行:     {stats.blank_lines:,} 行 ({stats.blank_lines/stats.total_lines*100:.1f}%)")
    print(f"   注释行:   {stats.comment_lines:,} 行 ({stats.comment_lines/stats.total_lines*100:.1f}%)")
    print(f"   平均每文件: {stats.total_lines/stats.total_files:.0f} 行")
    
    # 目录分布
    print(f"\n📁 目录分布 (Top {top_n}):")
    sorted_dirs = sorted(dir_stats.items(), key=lambda x: x[1]['lines'], reverse=True)
    for i, (dir_name, info) in enumerate(sorted_dirs[:top_n], 1):
        if dir_name == '.':
            dir_name = '[根目录]'
        print(f"   {i}. {dir_name}: {info['files']} 文件, {info['lines']:,} 行")
    
    # 最大文件 Top 5
    print(f"\n📝 最大文件 Top 5:")
    sorted_files = sorted(stats.file_details, key=lambda x: x['total'], reverse=True)
    for i, f in enumerate(sorted_files[:5], 1):
        print(f"   {i}. {f['path']}: {f['total']:,} 行 "
              f"(代码:{f['code']}, 注释:{f['comment']}, 空行:{f['blank']})")
    
    # 代码密度最高
    print(f"\n🎯 代码密度最高 Top 5 (按代码/总行数比例):")
    density_files = [f for f in stats.file_details if f['total'] > 20]  # 过滤小文件
    density_files.sort(key=lambda x: x['code']/x['total'], reverse=True)
    for i, f in enumerate(density_files[:5], 1):
        ratio = f['code']/f['total']*100
        print(f"   {i}. {f['path']}: {ratio:.1f}% 为实际代码")
    
    print("\n" + "="*70)


def export_to_markdown(stats, output_file='code_stats.md'):
    """导出统计结果为 Markdown 文件"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# 项目代码统计报告\n\n")
        f.write(f"**统计时间:** {os.popen('date').read().strip() if sys.platform != 'win32' else ''}\n\n")
        f.write("## 总体统计\n\n")
        f.write(f"- **文件总数:** {stats.total_files} 个\n")
        f.write(f"- **总行数:** {stats.total_lines:,} 行\n")
        f.write(f"- **代码行:** {stats.code_lines:,} 行\n")
        f.write(f"- **注释行:** {stats.comment_lines:,} 行\n")
        f.write(f"- **空行:** {stats.blank_lines:,} 行\n\n")
        
        f.write("## 文件清单\n\n")
        f.write("| 文件路径 | 总行数 | 代码行 | 注释行 | 空行 |\n")
        f.write("|----------|--------|--------|--------|------|\n")
        for file_info in sorted(stats.file_details, key=lambda x: x['path']):
            f.write(f"| {file_info['path']} | {file_info['total']} | "
                   f"{file_info['code']} | {file_info['comment']} | {file_info['blank']} |\n")
    
    print(f"\n✅ 已导出 Markdown 报告: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='统计 Python 项目代码行数',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                    # 统计当前目录
  %(prog)s /path/to/project   # 统计指定目录
  %(prog)s . --export stats.md # 导出 Markdown 报告
        """
    )
    parser.add_argument('path', nargs='?', default='.', help='目标目录路径 (默认: 当前目录)')
    parser.add_argument('--exclude', '-e', nargs='+', default=[], 
                       help='额外排除的目录名 (如: build dist)')
    parser.add_argument('--top', '-t', type=int, default=10, help='显示 Top N 目录 (默认: 10)')
    parser.add_argument('--export', '-o', metavar='FILE', help='导出 Markdown 格式报告')
    parser.add_argument('--quiet', '-q', action='store_true', help='静默模式，只输出数字')
    
    args = parser.parse_args()
    
    exclude_dirs = {'.git', '__pycache__', '.pytest_cache', '.mypy_cache', 
                   'venv', '.venv', 'env', 'node_modules', '.idea', '.vscode'}
    exclude_dirs.update(args.exclude)
    
    if args.quiet:
        stats, _ = scan_directory(args.path, exclude_dirs)
        if stats:
            print(f"{stats.total_files},{stats.total_lines},{stats.code_lines}")
        return
        
    print(f"🔍 正在扫描目录: {Path(args.path).resolve()}")
    print(f"🚫 排除目录: {', '.join(exclude_dirs)}")
    
    stats, dir_stats = scan_directory(args.path, exclude_dirs)
    
    if stats:
        print_results(stats, dir_stats, args.top)
        if args.export:
            export_to_markdown(stats, args.export)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()