"""测试RAG功能"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试导入"""
    print("测试导入...")
    try:
        from vector_db.chroma_store import ChromaDBStore, get_db_store
        from core.rag_engine import RAGEngine, get_rag_engine
        print("✓ 所有导入成功")
        return True
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        return False

def test_chromadb():
    """测试ChromaDB"""
    print("\n测试ChromaDB...")
    try:
        import chromadb
        print(f"✓ ChromaDB版本: {chromadb.__version__}")
        return True
    except ImportError:
        print("✗ ChromaDB未安装，请运行: pip install chromadb")
        return False

def test_ollama_connection():
    """测试Ollama连接"""
    print("\n测试Ollama连接...")
    try:
        from utils.ollama_utils import check_ollama_running
        if check_ollama_running():
            print("✓ Ollama服务运行中")
            return True
        else:
            print("✗ Ollama未运行，请运行: ollama serve")
            return False
    except Exception as e:
        print(f"✗ 检查Ollama时出错: {e}")
        return False

def test_vector_db():
    """测试向量数据库"""
    print("\n测试向量数据库...")
    try:
        from vector_db.chroma_store import get_db_store
        
        db = get_db_store()
        stats = db.get_stats()
        print(f"✓ 向量数据库初始化成功")
        print(f"  - 集合名称: {stats['collection_name']}")
        print(f"  - 文档数量: {stats['total_documents']}")
        print(f"  - 持久化目录: {stats['persist_dir']}")
        return True
    except Exception as e:
        print(f"✗ 向量数据库初始化失败: {e}")
        return False

def test_indexing():
    """测试文档索引"""
    print("\n测试文档索引...")
    try:
        from vector_db.chroma_store import get_db_store, load_and_index_documents
        
        db = get_db_store()
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        
        if db.collection.count() == 0 and os.path.exists(data_dir):
            print("正在索引文档...")
            count = load_and_index_documents(data_dir, db)
            print(f"✓ 索引了 {count} 个文档片段")
        else:
            print(f"✓ 数据库已有 {db.collection.count()} 个文档")
        
        return True
    except Exception as e:
        print(f"✗ 文档索引失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rag_query():
    """测试RAG查询"""
    print("\n测试RAG查询...")
    try:
        from core.rag_engine import get_rag_engine
        
        engine = get_rag_engine()
        
        # 测试查询
        test_question = "什么是ESG？"
        print(f"测试问题: {test_question}")
        
        response = engine.query(test_question, top_k=3)
        
        print(f"✓ 查询成功")
        print(f"  - 答案长度: {len(response.answer)} 字符")
        print(f"  - 思维过程长度: {len(response.reasoning)} 字符")
        print(f"  - 参考来源: {len(response.sources)} 个")
        print(f"  - 置信度: {response.confidence:.2%}")
        
        return True
    except Exception as e:
        print(f"✗ RAG查询失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("RAG功能测试")
    print("=" * 50)
    
    results = []
    
    # 运行测试
    results.append(("导入测试", test_imports()))
    results.append(("ChromaDB测试", test_chromadb()))
    results.append(("Ollama连接测试", test_ollama_connection()))
    results.append(("向量数据库测试", test_vector_db()))
    results.append(("文档索引测试", test_indexing()))
    results.append(("RAG查询测试", test_rag_query()))
    
    # 打印结果
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    
    for name, result in results:
        status = "通过" if result else "失败"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {name}: {status}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\n总计: {passed}/{total} 通过")

if __name__ == "__main__":
    main()
