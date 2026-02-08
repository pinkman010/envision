"""检查docstring覆盖率"""
import ast
import os

def check_file(filepath):
    """检查单个文件的docstring"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tree = ast.parse(content)
    
    total = 0
    with_doc = 0
    missing = []
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            # 跳过私有方法（单下划线开头但非双下划线）
            if node.name.startswith('_') and not node.name.startswith('__'):
                continue
            
            total += 1
            if ast.get_docstring(node):
                with_doc += 1
            else:
                missing.append(f"  {node.name} (line {node.lineno})")
    
    return total, with_doc, missing

# 检查src目录
total_all = 0
with_doc_all = 0
missing_all = []

for root, dirs, files in os.walk('src'):
    if '__pycache__' in root or 'egg-info' in root:
        continue
    for file in files:
        if file.endswith('.py') and file != '__init__.py':
            filepath = os.path.join(root, file)
            try:
                t, w, m = check_file(filepath)
                total_all += t
                with_doc_all += w
                if m:
                    missing_all.append((filepath, m))
            except Exception as e:
                print(f"Error parsing {filepath}: {e}")

print("=" * 60)
print("Docstring覆盖率报告")
print("=" * 60)
print(f"总函数/类数量: {total_all}")
print(f"有docstring的数量: {with_doc_all}")
if total_all > 0:
    coverage = (with_doc_all / total_all) * 100
    print(f"覆盖率: {coverage:.1f}%")
print()

if missing_all:
    print(f"缺少docstring的项 ({total_all - with_doc_all}个):")
    for filepath, items in missing_all[:10]:  # 只显示前10个文件
        print(f"\n{filepath}:")
        for item in items[:5]:  # 每个文件最多显示5个
            print(item)
        if len(items) > 5:
            print(f"  ... 还有 {len(items) - 5} 个")
    if len(missing_all) > 10:
        print(f"\n... 还有 {len(missing_all) - 10} 个文件")
else:
    print("✅ 所有函数/类都有docstring！")
