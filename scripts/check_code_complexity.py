"""
代码复杂度检查工具（使用radon库）
"""

import sys
from pathlib import Path
from radon.complexity import cc_visit, cc_rank
from radon.raw import analyze
from radon.metrics import mi_visit

ROOT_DIR = Path(__file__).parent.parent
SRC_DIR = ROOT_DIR / "src"


def check_cyclomatic_complexity():
    """检查圈复杂度"""
    print("=" * 80)
    print("检查圈复杂度 (Cyclomatic Complexity)")
    print("=" * 80)
    high_complexity = False

    for py_file in SRC_DIR.rglob("*.py"):
        if "test" in py_file.name or "__init__" in py_file.name:
            continue
        with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()
        blocks = cc_visit(content)
        for block in blocks:
            rank = cc_rank(block.complexity)
            if rank in ["D", "E", "F"]:
                high_complexity = True
                print(f"! 高复杂度: {py_file.relative_to(ROOT_DIR)}")
                print(
                    f"   函数/类: {block.name}, 复杂度: {block.complexity}, 等级: {rank}"
                )

    if not high_complexity:
        print("OK 所有代码圈复杂度正常")
    return high_complexity


def check_maintainability_index():
    """检查可维护性指数"""
    print("\n" + "=" * 80)
    print("检查可维护性指数 (Maintainability Index)")
    print("=" * 80)
    low_maintainability = False

    for py_file in SRC_DIR.rglob("*.py"):
        if "test" in py_file.name or "__init__" in py_file.name:
            continue
        with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()
        mi = mi_visit(content, multi=True)

        # radon 6.x 返回 float，之前的版本返回可迭代对象
        if isinstance(mi, list):
            for m in mi:
                if m.mi < 65:
                    low_maintainability = True
                    print(f"! 低可维护性: {py_file.relative_to(ROOT_DIR)}")
                    print(f"   可维护性指数: {m.mi:.2f}")
        else:
            # radon 6.x 直接返回 float
            if mi < 65:
                low_maintainability = True
                print(f"! 低可维护性: {py_file.relative_to(ROOT_DIR)}")
                print(f"   可维护性指数: {mi:.2f}")

    if not low_maintainability:
        print("✅ 所有代码可维护性指数正常")
    return low_maintainability


def main():
    print("=== 开始代码质量检查 ===")
    cc_high = check_cyclomatic_complexity()
    mi_low = check_maintainability_index()

    if cc_high or mi_low:
        print("\n=== 代码质量检查未通过，请修复上述问题 ===")
        sys.exit(1)
    else:
        print("\n=== 代码质量检查通过 ===")
        sys.exit(0)


if __name__ == "__main__":
    main()
