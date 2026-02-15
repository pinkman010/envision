#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目代码统计工具 (增强版)
统计所有 .py 文件，并单独统计排除 __init__.py、tests 和 scripts 后的核心代码
"""

import os
import sys
import argparse
from pathlib import Path
from collections import defaultdict


class CodeStats:
    def __init__(self, name="全部文件"):
        self.name = name
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
    
    def avg_lines_per_file(self):
        return self.total_lines / self.total_files if self.total_files > 0 else 0


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


def is_filtered_file(filepath, root_path):
    """
    判断文件是否应该被过滤（排除 __init__.py、tests目录、scripts目录）
    返回 True 表示该文件需要被排除
    """
    # 转换为 Path 对象便于处理
    path = Path(filepath)
    relative_path = path.relative_to(root_path)
    
    # 排除 __init__.py 文件（包括多层目录下的）
    if path.name == '__init__.py':
        return True
    
    # 检查路径中是否包含 tests 或 scripts 目录
    parts = relative_path.parts
    if 'tests' in parts or 'test' in parts:
        return True
    if 'scripts' in parts or 'script' in parts:
        return True
        
    return False


def scan_directory(directory, exclude_dirs=None):
    """
    递归扫描目录，同时维护全部统计和过滤后统计
    """
    if exclude_dirs is None:
        exclude_dirs = {'.git', '__pycache__', '.pytest_cache', '.mypy_cache', 
                       'venv', '.venv', 'env', 'node_modules', '.idea', '.vscode',
                       'build', 'dist', 'egg-info'}
        
    all_stats = CodeStats("全部文件")
    filtered_stats = CodeStats("核心代码(排除__init__,tests,scripts)")
    
    directory = Path(directory).resolve()
    
    if not directory.exists():
        print(f"错误: 目录不存在 {directory}")
        return None, None
        
    # 按目录分组的统计
    all_dir_stats = defaultdict(lambda: {'files': 0, 'lines': 0})
    filtered_dir_stats = defaultdict(lambda: {'files': 0, 'lines': 0})
    
    for root, dirs, files in os.walk(directory):
        # 排除指定目录（注意：这里不排除 tests/scripts，因为我们要在文件层面判断）
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        current_dir = Path(root)
        relative_dir = current_dir.relative_to(directory)
        
        for filename in files:
            if filename.endswith('.py'):
                filepath = current_dir / filename
                relative_path = filepath.relative_to(directory)
                
                result = analyze_file(filepath)
                if not result:
                    continue
                
                # 始终加入全部统计
                all_stats.add_file(
                    str(relative_path),
                    result['total'],
                    result['code'],
                    result['blank'],
                    result['comment']
                )
                all_dir_stats[str(relative_dir)]['files'] += 1
                all_dir_stats[str(relative_dir)]['lines'] += result['total']
                
                # 判断是否加入过滤后统计
                if not is_filtered_file(filepath, directory):
                    filtered_stats.add_file(
                        str(relative_path),
                        result['total'],
                        result['code'],
                        result['blank'],
                        result['comment']
                    )
                    filtered_dir_stats[str(relative_dir)]['files'] += 1
                    filtered_dir_stats[str(relative_dir)]['lines'] += result['total']
    
    return (all_stats, all_dir_stats), (filtered_stats, filtered_dir_stats)


def print_comparison(all_stats, filtered_stats):
    """打印对比数据"""
    if all_stats.total_files == 0:
        return
        
    print(f"\n📊 统计对比:")
    print(f"   {'指标':<20} {'全部文件':>12} {'核心代码':>12} {'过滤比例':>10}")
    print(f"   {'-'*20} {'-'*12} {'-'*12} {'-'*10}")
    
    # 文件数对比
    f_count = all_stats.total_files - filtered_stats.total_files
    f_percent = f_count / all_stats.total_files * 100 if all_stats.total_files > 0 else 0
    print(f"   {'文件数量':<20} {all_stats.total_files:>12} {filtered_stats.total_files:>12} {f_percent:>9.1f}%")
    
    # 总行数对比
    f_lines = all_stats.total_lines - filtered_stats.total_lines
    f_lines_percent = f_lines / all_stats.total_lines * 100 if all_stats.total_lines > 0 else 0
    print(f"   {'总行数':<20} {all_stats.total_lines:>12,} {filtered_stats.total_lines:>12,} {f_lines_percent:>9.1f}%")
    
    # 代码行对比
    f_code = all_stats.code_lines - filtered_stats.code_lines
    f_code_percent = f_code / all_stats.code_lines * 100 if all_stats.code_lines > 0 else 0
    print(f"   {'实际代码行':<20} {all_stats.code_lines:>12,} {filtered_stats.code_lines:>12,} {f_code_percent:>9.1f}%")
    
    # 平均每文件行数对比
    print(f"   {'平均每文件行数':<20} {all_stats.avg_lines_per_file():>12.0f} {filtered_stats.avg_lines_per_file():>12.0f}")


def print_results(stats_pair, top_n=10):
    """格式化输出统计结果"""
    (all_stats, all_dir_stats), (filtered_stats, filtered_dir_stats) = stats_pair
    
    if all_stats.total_files == 0:
        print("未找到 Python 文件")
        return
        
    print("\n" + "="*80)
    print(f"{'Python 项目代码统计报告':^80}")
    print("="*80)
    
    # 1. 全部文件统计
    print(f"\n📁 【全部文件统计】")
    print(f"   文件总数: {all_stats.total_files} 个")
    print(f"   总行数:   {all_stats.total_lines:,} 行")
    print(f"   代码行:   {all_stats.code_lines:,} 行 ({all_stats.code_lines/all_stats.total_lines*100:.1f}%)")
    print(f"   空行:     {all_stats.blank_lines:,} 行 ({all_stats.blank_lines/all_stats.total_lines*100:.1f}%)")
    print(f"   注释行:   {all_stats.comment_lines:,} 行 ({all_stats.comment_lines/all_stats.total_lines*100:.1f}%)")
    
    # 2. 过滤后统计
    print(f"\n🎯 【核心代码统计】(__init__.py, tests/, scripts/ 已排除)")
    if filtered_stats.total_files > 0:
        print(f"   文件总数: {filtered_stats.total_files} 个")
        print(f"   总行数:   {filtered_stats.total_lines:,} 行")
        print(f"   代码行:   {filtered_stats.code_lines:,} 行 ({filtered_stats.code_lines/filtered_stats.total_lines*100:.1f}%)")
        print(f"   空行:     {filtered_stats.blank_lines:,} 行 ({filtered_stats.blank_lines/filtered_stats.total_lines*100:.1f}%)")
        print(f"   注释行:   {filtered_stats.comment_lines:,} 行 ({filtered_stats.comment_lines/filtered_stats.total_lines*100:.1f}%)")
    else:
        print("   无核心代码文件（可能全部被过滤）")
    
    # 3. 对比分析
    print_comparison(all_stats, filtered_stats)
    
    # 4. 被过滤掉的内容明细
    print(f"\n🚫 【被过滤内容明细】")
    excluded_files = all_stats.total_files - filtered_stats.total_files
    excluded_lines = all_stats.total_lines - filtered_stats.total_lines
    print(f"   排除了 {excluded_files} 个文件，共 {excluded_lines:,} 行代码")
    print(f"   包含: __init__.py 文件、tests/ 目录下文件、scripts/ 目录下文件")
    
    # 5. 核心代码目录分布 (Top N)
    if filtered_stats.total_files > 0:
        print(f"\n📂 【核心代码目录分布】 (Top {top_n}):")
        sorted_dirs = sorted(filtered_dir_stats.items(), key=lambda x: x[1]['lines'], reverse=True)
        for i, (dir_name, info) in enumerate(sorted_dirs[:top_n], 1):
            if dir_name == '.':
                dir_name = '[根目录]'
            print(f"   {i}. {dir_name}: {info['files']} 文件, {info['lines']:,} 行")
    
    # 6. 最大核心文件 Top 5
    if filtered_stats.file_details:
        print(f"\n📝 【最大核心文件 Top 5】:")
        sorted_files = sorted(filtered_stats.file_details, key=lambda x: x['total'], reverse=True)
        for i, f in enumerate(sorted_files[:5], 1):
            print(f"   {i}. {f['path']}: {f['total']:,} 行 "
                  f"(代码:{f['code']}, 注释:{f['comment']}, 空行:{f['blank']})")
    
    print("\n" + "="*80)


def export_to_markdown(stats_pair, output_file='code_stats.md'):
    """导出统计结果为 Markdown 文件"""
    (all_stats, _), (filtered_stats, _) = stats_pair
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# 项目代码统计报告\n\n")
        f.write("## 统计概览\n\n")
        f.write("### 全部文件\n\n")
        f.write(f"- **文件总数:** {all_stats.total_files} 个\n")
        f.write(f"- **总行数:** {all_stats.total_lines:,} 行\n")
        f.write(f"- **代码行:** {all_stats.code_lines:,} 行\n")
        f.write(f"- **注释行:** {all_stats.comment_lines:,} 行\n")
        f.write(f"- **空行:** {all_stats.blank_lines:,} 行\n\n")
        
        f.write("### 核心代码 (排除 __init__.py, tests/, scripts/)\n\n")
        f.write(f"- **文件总数:** {filtered_stats.total_files} 个\n")
        f.write(f"- **总行数:** {filtered_stats.total_lines:,} 行\n")
        f.write(f"- **代码行:** {filtered_stats.code_lines:,} 行\n")
        f.write(f"- **注释行:** {filtered_stats.comment_lines:,} 行\n")
        f.write(f"- **空行:** {filtered_stats.blank_lines:,} 行\n\n")
        
        f.write("## 核心代码文件清单\n\n")
        f.write("| 文件路径 | 总行数 | 代码行 | 注释行 | 空行 |\n")
        f.write("|----------|--------|--------|--------|------|\n")
        for file_info in sorted(filtered_stats.file_details, key=lambda x: x['path']):
            f.write(f"| {file_info['path']} | {file_info['total']} | "
                   f"{file_info['code']} | {file_info['comment']} | {file_info['blank']} |\n")
        
        f.write("\n## 排除的文件清单\n\n")
        excluded = [f for f in all_stats.file_details if f not in filtered_stats.file_details]
        if excluded:
            f.write("| 文件路径 | 总行数 | 排除原因 |\n")
            f.write("|----------|--------|----------|\n")
            for file_info in sorted(excluded, key=lambda x: x['path']):
                reason = "scripts目录" if '/scripts/' in file_info['path'] else \
                        "tests目录" if '/tests/' in file_info['path'] or '/test/' in file_info['path'] else \
                        "__init__.py" if file_info['path'].endswith('__init__.py') else "其他"
                f.write(f"| {file_info['path']} | {file_info['total']} | {reason} |\n")
        else:
            f.write("无排除文件\n")
    
    print(f"\n✅ 已导出 Markdown 报告: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='统计 Python 项目代码行数 (区分全部代码和核心代码)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                    # 统计当前目录
  %(prog)s /path/to/project   # 统计指定目录
  %(prog)s . --export         # 导出 Markdown 报告
        """
    )
    parser.add_argument('path', nargs='?', default='.', help='目标目录路径 (默认: 当前目录)')
    parser.add_argument('--exclude', '-e', nargs='+', default=[], 
                       help='额外排除的目录名 (如: build dist)')
    parser.add_argument('--top', '-t', type=int, default=10, help='显示 Top N 目录 (默认: 10)')
    parser.add_argument('--export', '-o', metavar='FILE', nargs='?', const='code_stats.md',
                       help='导出 Markdown 格式报告 (默认文件名: code_stats.md)')
    parser.add_argument('--quiet', '-q', action='store_true', 
                       help='静默模式，输出: 全部文件数,全部行数,核心文件数,核心行数')
    
    args = parser.parse_args()
    
    exclude_dirs = {'.git', '__pycache__', '.pytest_cache', '.mypy_cache', 
                   'venv', '.venv', 'env', 'node_modules', '.idea', '.vscode',
                   'build', 'dist', 'egg-info', '.tox'}
    exclude_dirs.update(args.exclude)
    
    if args.quiet:
        stats_pair = scan_directory(args.path, exclude_dirs)
        if stats_pair[0][0].total_files > 0:
            all_stats, filtered_stats = stats_pair[0][0], stats_pair[1][0]
            print(f"{all_stats.total_files},{all_stats.total_lines},"
                  f"{filtered_stats.total_files},{filtered_stats.total_lines}")
        return
        
    print(f"🔍 正在扫描目录: {Path(args.path).resolve()}")
    print(f"🚫 排除目录: {', '.join(sorted(exclude_dirs))}")
    print(f"🚫 过滤规则: __init__.py, tests/, scripts/")
    
    stats_pair = scan_directory(args.path, exclude_dirs)
    
    if stats_pair[0][0].total_files > 0:
        print_results(stats_pair, args.top)
        if args.export:
            export_to_markdown(stats_pair, args.export)
    else:
        print("未找到 Python 文件")
        sys.exit(1)


if __name__ == '__main__':
    main()