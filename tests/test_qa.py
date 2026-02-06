# -*- coding: utf-8 -*-
"""
问答功能测试脚本
测试知识库检索和回答生成

运行方法: python test_qa.py
"""
import sys
import os
import time

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("🧪 问答功能测试")
print("=" * 60)


# ========== 初始化 ==========
print("\n【初始化】")
print("-" * 40)

try:
    from scripts.rag_system import init_system
    
    print("加载问答系统...")
    start = time.time()
    qa_system, doc_count = init_system(warmup=True)
    print(f"✅ 加载成功 ({time.time()-start:.1f}秒)")
    print(f"   知识库: {doc_count} 个文档块")
    
except Exception as e:
    print(f"❌ 加载失败: {e}")
    print("\n请先检查:")
    print("  1. ollama serve")
    print("  2. ollama pull deepseek-r1:1.5b")
    print("  3. python scripts/create_vector_db.py")
    sys.exit(1)


# ========== 自动测试 ==========
print("\n【自动测试】")
print("-" * 40)

test_questions = [
    "什么是ESG？",
    "碳排放有什么要求？",
]

for i, q in enumerate(test_questions, 1):
    print(f"\n问题{i}: {q}")
    
    start = time.time()
    answer = ""
    sources = []
    
    # 流式获取回答
    for msg_type, content in qa_system.ask_stream(q):
        if msg_type == "answer":
            answer += content
        elif msg_type == "done":
            sources = content.get("source_documents", [])
            if not answer:
                answer = content.get("answer", "")
    
    # 清理回答
    if "</think>" in answer:
        answer = answer.split("</think>")[-1].strip()
    
    elapsed = time.time() - start
    
    # 显示结果
    print(f"回答: {answer[:200]}..." if len(answer) > 200 else f"回答: {answer}")
    print(f"耗时: {elapsed:.1f}秒 | 参考: {len(sources)}个文档")


# ========== 交互测试 ==========
print("\n" + "=" * 60)
print("【交互测试】输入问题，输入 q 退出")
print("=" * 60)

while True:
    try:
        q = input("\n❓ 问题: ").strip()
        
        if q.lower() in ['q', 'quit', 'exit', '退出']:
            print("👋 测试结束")
            break
        
        if not q:
            continue
        
        print("\n🤔 思考中...\n")
        start = time.time()
        
        # 流式输出
        for msg_type, content in qa_system.ask_stream(q):
            if msg_type == "think":
                print(f"💭 {content}", end="", flush=True)
            elif msg_type == "think_end":
                print("\n")
            elif msg_type == "answer":
                print(content, end="", flush=True)
        
        print(f"\n\n⏱️ 耗时: {time.time()-start:.1f}秒")
        
    except KeyboardInterrupt:
        print("\n\n👋 测试结束")
        break