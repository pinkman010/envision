"""ChromaDB向量存储扩展单元测试

覆盖esg.vector_store.chroma_store模块的各种使用场景和边界情况。
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, patch

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestChromaDBStoreInit(unittest.TestCase):
    """ChromaDBStore初始化测试"""

    @patch("esg.vector_store.chroma_store._check_chromadb")
    def test_chromadb_store_init(self, mock_check):
        """测试ChromaDB存储初始化"""
        mock_check.return_value = True

        with patch("esg.vector_store.chroma_store.OllamaClient"):
            from src.esg.vector_store.chroma_store import ChromaDBStore

            store = ChromaDBStore(collection="test")
            self.assertEqual(store.collection_name, "test")


class TestChromaDBStoreMethods(unittest.TestCase):
    """ChromaDBStore方法测试"""

    @patch("esg.vector_store.chroma_store._check_chromadb")
    def test_chromadb_store_methods(self, mock_check):
        """测试ChromaDB存储方法"""
        mock_check.return_value = True

        with patch("esg.vector_store.chroma_store.OllamaClient"):
            from src.esg.vector_store.chroma_store import ChromaDBStore

            store = ChromaDBStore()

            # 测试方法存在
            self.assertTrue(hasattr(store, "add_documents"))
            self.assertTrue(hasattr(store, "search"))
            self.assertTrue(hasattr(store, "count"))
            self.assertTrue(hasattr(store, "is_available"))


class TestChromaDBStoreGenerateId(unittest.TestCase):
    """文档ID生成测试"""

    @patch("esg.vector_store.chroma_store._check_chromadb")
    def test_generate_id(self, mock_check):
        """测试文档ID生成"""
        mock_check.return_value = True

        with patch("esg.vector_store.chroma_store.OllamaClient"):
            from src.esg.vector_store.chroma_store import ChromaDBStore

            store = ChromaDBStore()

            doc = {"text": "测试内容", "source": "test.pdf", "position": "1"}
            doc_id = store._generate_id(doc)

            self.assertIsInstance(doc_id, str)
            self.assertEqual(len(doc_id), 32)  # MD5哈希长度

    @patch("esg.vector_store.chroma_store._check_chromadb")
    def test_generate_id_empty_text(self, mock_check):
        """测试空文本"""
        mock_check.return_value = True

        with patch("esg.vector_store.chroma_store.OllamaClient"):
            from src.esg.vector_store.chroma_store import ChromaDBStore

            store = ChromaDBStore()

            doc = {"text": "", "source": "test.pdf"}
            doc_id = store._generate_id(doc)

            self.assertIsInstance(doc_id, str)


class TestChromaDBStoreAddDocument(unittest.TestCase):
    """添加文档测试"""

    @patch("esg.vector_store.chroma_store._check_chromadb")
    def test_add_document(self, mock_check):
        """测试添加单个文档"""
        mock_check.return_value = True

        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_collection.count.return_value = 0
        mock_client.get_or_create_collection.return_value = mock_collection

        with patch("esg.vector_store.chroma_store.OllamaClient") as mock_ollama:
            mock_ollama_instance = MagicMock()
            mock_ollama_instance.embed.return_value = [0.1] * 384
            mock_ollama.return_value = mock_ollama_instance

            from src.esg.vector_store.chroma_store import ChromaDBStore

            store = ChromaDBStore()
            store.client = mock_client
            store.collection = mock_collection

            doc_id = store.add_document("测试文档", "test.pdf")

            self.assertIsNotNone(doc_id)


class TestChromaDBStoreSearch(unittest.TestCase):
    """搜索测试"""

    @patch("esg.vector_store.chroma_store._check_chromadb")
    def test_search_empty_knowledge_base(self, mock_check):
        """测试空知识库搜索"""
        mock_check.return_value = True

        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_collection.count.return_value = 0
        mock_client.get_or_create_collection.return_value = mock_collection

        with patch("esg.vector_store.chroma_store.OllamaClient") as mock_ollama:
            mock_ollama_instance = MagicMock()
            mock_ollama.return_value = mock_ollama_instance

            from src.esg.vector_store.chroma_store import ChromaDBStore

            store = ChromaDBStore()
            store.client = mock_client
            store.collection = mock_collection

            results = store.search("测试查询")

            self.assertEqual(results, [])

    @patch("esg.vector_store.chroma_store._check_chromadb")
    def test_search_with_results(self, mock_check):
        """测试搜索返回结果"""
        mock_check.return_value = True

        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_collection.count.return_value = 5
        mock_collection.query.return_value = {
            "ids": [["id1", "id2"]],
            "documents": [["text1", "text2"]],
            "metadatas": [[{"source": "test.pdf"}, {"source": "test2.pdf"}]],
            "distances": [[0.1, 0.2]],
        }
        mock_client.get_or_create_collection.return_value = mock_collection

        with patch("esg.vector_store.chroma_store.OllamaClient") as mock_ollama:
            mock_ollama_instance = MagicMock()
            mock_ollama_instance.embed.return_value = [0.1] * 384
            mock_ollama.return_value = mock_ollama_instance

            from src.esg.vector_store.chroma_store import ChromaDBStore

            store = ChromaDBStore()
            store.client = mock_client
            store.collection = mock_collection

            results = store.search("测试查询", top_k=2)

            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]["id"], "id1")


class TestChromaDBStoreCount(unittest.TestCase):
    """文档计数测试"""

    @patch("esg.vector_store.chroma_store._check_chromadb")
    def test_count_with_collection(self, mock_check):
        """测试有集合时的计数"""
        mock_check.return_value = True

        mock_collection = MagicMock()
        mock_collection.count.return_value = 10

        from src.esg.vector_store.chroma_store import ChromaDBStore

        store = ChromaDBStore.__new__(ChromaDBStore)
        store.collection = mock_collection

        count = store.count()

        self.assertEqual(count, 10)

    @patch("esg.vector_store.chroma_store._check_chromadb")
    def test_count_without_collection(self, mock_check):
        """测试无集合时的计数"""
        mock_check.return_value = True

        from src.esg.vector_store.chroma_store import ChromaDBStore

        store = ChromaDBStore.__new__(ChromaDBStore)
        store.collection = None

        count = store.count()

        self.assertEqual(count, 0)


class TestChromaDBStoreIsAvailable(unittest.TestCase):
    """可用性检查测试"""

    @patch("esg.vector_store.chroma_store._check_chromadb")
    def test_is_available_true(self, mock_check):
        """测试可用"""
        mock_check.return_value = True

        mock_collection = MagicMock()

        from src.esg.vector_store.chroma_store import ChromaDBStore

        store = ChromaDBStore.__new__(ChromaDBStore)
        store.collection = mock_collection

        self.assertTrue(store.is_available())

    @patch("esg.vector_store.chroma_store._check_chromadb")
    def test_is_available_false(self, mock_check):
        """测试不可用"""
        mock_check.return_value = False

        from src.esg.vector_store.chroma_store import ChromaDBStore

        store = ChromaDBStore.__new__(ChromaDBStore)
        store.collection = None

        self.assertFalse(store.is_available())


class TestChromaDBStoreDelete(unittest.TestCase):
    """删除文档测试"""

    @patch("esg.vector_store.chroma_store._check_chromadb")
    def test_delete_document(self, mock_check):
        """测试删除文档"""
        mock_check.return_value = True

        mock_collection = MagicMock()

        from src.esg.vector_store.chroma_store import ChromaDBStore

        store = ChromaDBStore.__new__(ChromaDBStore)
        store.collection = mock_collection

        result = store.delete_document("test_id")

        self.assertTrue(result)
        mock_collection.delete.assert_called_once()

    @patch("esg.vector_store.chroma_store._check_chromadb")
    def test_delete_document_no_collection(self, mock_check):
        """测试无集合时删除"""
        mock_check.return_value = True

        from src.esg.vector_store.chroma_store import ChromaDBStore

        store = ChromaDBStore.__new__(ChromaDBStore)
        store.collection = None

        result = store.delete_document("test_id")

        self.assertFalse(result)


class TestChromaDBStoreClear(unittest.TestCase):
    """清空集合测试"""

    @patch("esg.vector_store.chroma_store._check_chromadb")
    def test_clear(self, mock_check):
        """测试清空集合"""
        mock_check.return_value = True

        mock_collection = MagicMock()

        from src.esg.vector_store.chroma_store import ChromaDBStore

        store = ChromaDBStore.__new__(ChromaDBStore)
        store.collection = mock_collection

        result = store.clear()

        self.assertTrue(result)
        mock_collection.delete.assert_called_once()


class TestVectorStoreAlias(unittest.TestCase):
    """VectorStore别名测试"""

    def test_vector_store_alias(self):
        """测试VectorStore别名"""
        from src.esg.vector_store.chroma_store import ChromaDBStore, VectorStore

        self.assertEqual(VectorStore, ChromaDBStore)


class TestGetChromaDbError(unittest.TestCase):
    """ChromaDB错误信息测试"""

    def test_get_chromadb_error(self):
        """测试获取错误信息"""
        from src.esg.vector_store.chroma_store import get_chromadb_error

        error = get_chromadb_error()
        self.assertIsNone(error)


class TestChromaDBStoreAutoLoad(unittest.TestCase):
    """自动加载测试"""

    @patch("esg.vector_store.chroma_store._check_chromadb")
    def test_auto_load_from_directory_nonexistent(self, mock_check):
        """测试加载不存在的目录"""
        mock_check.return_value = True

        mock_collection = MagicMock()
        mock_collection.count.return_value = 0

        with patch("esg.vector_store.chroma_store.OllamaClient"):
            from src.esg.vector_store.chroma_store import ChromaDBStore

            store = ChromaDBStore()
            store.collection = mock_collection

            result = store.auto_load_from_directory("/nonexistent/directory")

            self.assertEqual(result, 0)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestChromaDBStoreInit))
    suite.addTests(loader.loadTestsFromTestCase(TestChromaDBStoreMethods))
    suite.addTests(loader.loadTestsFromTestCase(TestChromaDBStoreGenerateId))
    suite.addTests(loader.loadTestsFromTestCase(TestChromaDBStoreAddDocument))
    suite.addTests(loader.loadTestsFromTestCase(TestChromaDBStoreSearch))
    suite.addTests(loader.loadTestsFromTestCase(TestChromaDBStoreCount))
    suite.addTests(loader.loadTestsFromTestCase(TestChromaDBStoreIsAvailable))
    suite.addTests(loader.loadTestsFromTestCase(TestChromaDBStoreDelete))
    suite.addTests(loader.loadTestsFromTestCase(TestChromaDBStoreClear))
    suite.addTests(loader.loadTestsFromTestCase(TestVectorStoreAlias))
    suite.addTests(loader.loadTestsFromTestCase(TestGetChromaDbError))
    suite.addTests(loader.loadTestsFromTestCase(TestChromaDBStoreAutoLoad))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
