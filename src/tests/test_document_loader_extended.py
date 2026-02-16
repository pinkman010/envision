"""文档加载器扩展单元测试

覆盖DocumentLoader的更多使用场景和边界情况。
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestDocumentLoaderFull(unittest.TestCase):
    """DocumentLoader完整功能测试"""

    def test_document_loader_init_with_none(self):
        """测试使用None初始化"""
        from src.esg.vector_store.document_loader import DocumentLoader

        loader = DocumentLoader(data_dir=None)
        self.assertIsNone(loader.data_dir)

    def test_document_loader_init_with_path(self):
        """测试使用Path初始化"""
        from src.esg.vector_store.document_loader import DocumentLoader

        loader = DocumentLoader(data_dir=tempfile.gettempdir())
        self.assertIsNotNone(loader.data_dir)

    def test_resolve_path_absolute(self):
        """测试解析绝对路径"""
        from src.esg.vector_store.document_loader import DocumentLoader

        loader = DocumentLoader()
        abs_path = Path("/absolute/path/file.json")
        result = loader._resolve_path(abs_path)
        self.assertEqual(result, abs_path)

    def test_resolve_path_relative(self):
        """测试解析相对路径"""
        from src.esg.vector_store.document_loader import DocumentLoader

        loader = DocumentLoader(data_dir=tempfile.gettempdir())
        rel_path = Path("relative/path/file.json")
        result = loader._resolve_path(rel_path)
        self.assertTrue(result.is_absolute())

    def test_resolve_path_with_none_datadir(self):
        """测试data_dir为None时解析路径"""
        from src.esg.vector_store.document_loader import DocumentLoader

        loader = DocumentLoader(data_dir=None)
        # 当data_dir为None时，相对路径不会被拼接
        result = loader._resolve_path(Path("test.json"))
        # 此时应该直接返回原路径（因为没有base路径）
        self.assertIsNotNone(result)


class TestLoadJson(unittest.TestCase):
    """JSON加载测试"""

    def test_load_json_from_list(self):
        """测试加载JSON列表"""
        from src.esg.vector_store.document_loader import DocumentLoader

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(
                [
                    {"text": "文档1内容", "source": "source1"},
                    {"text": "文档2内容", "source": "source2"},
                ],
                f,
            )
            temp_path = f.name

        try:
            loader = DocumentLoader(data_dir=None)
            docs = loader.load_json(temp_path)
            self.assertEqual(len(docs), 2)
            self.assertEqual(docs[0]["text"], "文档1内容")
        finally:
            os.unlink(temp_path)

    def test_load_json_with_documents_key(self):
        """测试加载包含documents键的JSON"""
        from src.esg.vector_store.document_loader import DocumentLoader

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(
                {
                    "documents": [
                        {"text": "文档1", "source": "src1"},
                    ]
                },
                f,
            )
            temp_path = f.name

        try:
            loader = DocumentLoader(data_dir=None)
            docs = loader.load_json(temp_path)
            self.assertEqual(len(docs), 1)
        finally:
            os.unlink(temp_path)

    def test_load_json_with_data_key(self):
        """测试加载包含data键的JSON"""
        from src.esg.vector_store.document_loader import DocumentLoader

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(
                {
                    "data": [
                        {"text": "文档1", "source": "src1"},
                    ]
                },
                f,
            )
            temp_path = f.name

        try:
            loader = DocumentLoader(data_dir=None)
            docs = loader.load_json(temp_path)
            self.assertEqual(len(docs), 1)
        finally:
            os.unlink(temp_path)

    def test_load_json_with_items_key(self):
        """测试加载包含items键的JSON"""
        from src.esg.vector_store.document_loader import DocumentLoader

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(
                {
                    "items": [
                        {"text": "文档1", "source": "src1"},
                    ]
                },
                f,
            )
            temp_path = f.name

        try:
            loader = DocumentLoader(data_dir=None)
            docs = loader.load_json(temp_path)
            self.assertEqual(len(docs), 1)
        finally:
            os.unlink(temp_path)

    def test_load_json_with_single_object(self):
        """测试加载单个对象"""
        from src.esg.vector_store.document_loader import DocumentLoader

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump({"text": "单个文档", "source": "src1"}, f)
            temp_path = f.name

        try:
            loader = DocumentLoader(data_dir=None)
            docs = loader.load_json(temp_path)
            self.assertEqual(len(docs), 1)
            self.assertEqual(docs[0]["text"], "单个文档")
        finally:
            os.unlink(temp_path)

    def test_load_json_string_list(self):
        """测试加载字符串列表"""
        from src.esg.vector_store.document_loader import DocumentLoader

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(["字符串1", "字符串2"], f)
            temp_path = f.name

        try:
            loader = DocumentLoader(data_dir=None)
            docs = loader.load_json(temp_path)
            self.assertEqual(len(docs), 2)
            self.assertEqual(docs[0]["text"], "字符串1")
        finally:
            os.unlink(temp_path)

    def test_load_json_with_content_field(self):
        """测试使用content字段"""
        from src.esg.vector_store.document_loader import DocumentLoader

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(
                [
                    {"content": "使用content字段", "source": "src1"},
                ],
                f,
            )
            temp_path = f.name

        try:
            loader = DocumentLoader(data_dir=None)
            docs = loader.load_json(temp_path)
            self.assertEqual(docs[0]["text"], "使用content字段")
        finally:
            os.unlink(temp_path)

    def test_load_json_with_custom_fields(self):
        """测试自定义字段映射"""
        from src.esg.vector_store.document_loader import DocumentLoader

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(
                [
                    {"content_text": "自定义内容", "source_file": "my_source"},
                ],
                f,
            )
            temp_path = f.name

        try:
            loader = DocumentLoader(data_dir=None)
            docs = loader.load_json(
                temp_path, text_field="content_text", source_field="source_file"
            )
            self.assertEqual(docs[0]["text"], "自定义内容")
        finally:
            os.unlink(temp_path)

    def test_load_json_nonexistent(self):
        """测试加载不存在的文件"""
        from src.esg.vector_store.document_loader import DocumentLoader

        loader = DocumentLoader(data_dir=None)
        with self.assertRaises(FileNotFoundError):
            loader.load_json("/nonexistent/path/file.json")


class TestLoadJsonl(unittest.TestCase):
    """JSONL加载测试"""

    def test_load_jsonl_basic(self):
        """测试基本JSONL加载"""
        from src.esg.vector_store.document_loader import DocumentLoader

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as f:
            f.write('{"text": "line1"}\n')
            f.write('{"text": "line2"}\n')
            temp_path = f.name

        try:
            loader = DocumentLoader(data_dir=None)
            docs = loader.load_jsonl(temp_path)
            self.assertEqual(len(docs), 2)
        finally:
            os.unlink(temp_path)

    def test_load_jsonl_with_empty_lines(self):
        """测试包含空行的JSONL"""
        from src.esg.vector_store.document_loader import DocumentLoader

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as f:
            f.write('{"text": "line1"}\n')
            f.write("\n")
            f.write('{"text": "line2"}\n')
            temp_path = f.name

        try:
            loader = DocumentLoader(data_dir=None)
            docs = loader.load_jsonl(temp_path)
            self.assertEqual(len(docs), 2)
        finally:
            os.unlink(temp_path)

    def test_load_jsonl_with_invalid_lines(self):
        """测试包含无效行的JSONL"""
        from src.esg.vector_store.document_loader import DocumentLoader

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as f:
            f.write('{"text": "line1"}\n')
            f.write("invalid json\n")
            f.write('{"text": "line2"}\n')
            temp_path = f.name

        try:
            loader = DocumentLoader(data_dir=None)
            docs = loader.load_jsonl(temp_path)
            self.assertEqual(len(docs), 2)  # 只应加载有效的行
        finally:
            os.unlink(temp_path)

    def test_load_jsonl_with_content_field(self):
        """测试使用content字段"""
        from src.esg.vector_store.document_loader import DocumentLoader

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as f:
            f.write('{"content": "使用content"}\n')
            temp_path = f.name

        try:
            loader = DocumentLoader(data_dir=None)
            docs = loader.load_jsonl(temp_path)
            self.assertEqual(docs[0]["text"], "使用content")
        finally:
            os.unlink(temp_path)

    def test_load_jsonl_nonexistent(self):
        """测试加载不存在的JSONL文件"""
        from src.esg.vector_store.document_loader import DocumentLoader

        loader = DocumentLoader(data_dir=None)
        with self.assertRaises(FileNotFoundError):
            loader.load_jsonl("/nonexistent/path/file.jsonl")


class TestChunkDocuments(unittest.TestCase):
    """文档分块测试"""

    def test_chunk_documents_basic(self):
        """测试基本分块功能"""
        from src.esg.vector_store.document_loader import DocumentLoader

        loader = DocumentLoader()
        documents = [
            {"text": "这是第一段文本内容" * 100, "source": "test1"},
            {"text": "这是第二段文本内容" * 100, "source": "test2"},
        ]

        chunks = loader.chunk_documents(documents, chunk_size=500, chunk_overlap=50)
        self.assertIsInstance(chunks, list)
        self.assertGreater(len(chunks), 0)

    def test_chunk_documents_with_empty_text(self):
        """测试空文本分块"""
        from src.esg.vector_store.document_loader import DocumentLoader

        loader = DocumentLoader()
        documents = [
            {"text": "", "source": "test1"},
            {"text": None, "source": "test2"},
        ]

        chunks = loader.chunk_documents(documents, chunk_size=500, chunk_overlap=50)
        self.assertEqual(len(chunks), 0)

    def test_chunk_documents_small_text(self):
        """测试小文本分块"""
        from src.esg.vector_store.document_loader import DocumentLoader

        loader = DocumentLoader()
        documents = [
            {"text": "短文本", "source": "test1"},
        ]

        chunks = loader.chunk_documents(documents, chunk_size=500, chunk_overlap=50)
        self.assertEqual(len(chunks), 1)

    def test_split_text_empty(self):
        """测试分割空文本"""
        from src.esg.vector_store.document_loader import DocumentLoader

        loader = DocumentLoader()
        result = loader._split_text("", 100, 10)
        self.assertEqual(len(result), 0)

    def test_split_text_small(self):
        """测试分割小于块大小的文本"""
        from src.esg.vector_store.document_loader import DocumentLoader

        loader = DocumentLoader()
        result = loader._split_text("短文本", 100, 10)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "短文本")

    def test_split_text_large(self):
        """测试分割大文本"""
        from src.esg.vector_store.document_loader import DocumentLoader

        loader = DocumentLoader()
        # 创建一个大于chunk_size的文本
        text = "这是一个测试文本，" * 100  # 约800字符
        result = loader._split_text(text, 200, 50)
        self.assertGreater(len(result), 1)


class TestLoadDirectory(unittest.TestCase):
    """目录加载测试"""

    def test_load_directory_nonexistent(self):
        """测试加载不存在的目录"""
        from src.esg.vector_store.document_loader import DocumentLoader

        loader = DocumentLoader()
        docs = loader.load_directory("/nonexistent/directory")
        self.assertEqual(len(docs), 0)

    def test_load_directory_empty(self):
        """测试加载空目录"""
        from src.esg.vector_store.document_loader import DocumentLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = DocumentLoader()
            docs = loader.load_directory(tmpdir)
            self.assertEqual(len(docs), 0)

    def test_load_directory_with_files(self):
        """测试加载包含文件的目录"""
        from src.esg.vector_store.document_loader import DocumentLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建JSON文件
            json_path = Path(tmpdir) / "test.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump([{"text": "测试文档"}], f)

            loader = DocumentLoader()
            docs = loader.load_directory(tmpdir, pattern="*.json")
            self.assertEqual(len(docs), 1)


class TestLoadDocumentsForRag(unittest.TestCase):
    """便捷函数测试"""

    def test_load_documents_for_rag_basic(self):
        """测试load_documents_for_rag基本功能"""
        from src.esg.vector_store.document_loader import load_documents_for_rag

        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建JSON文件
            json_path = Path(tmpdir) / "test.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump([{"text": "测试文档"}], f)

            result = load_documents_for_rag(tmpdir, chunk_size=100, chunk_overlap=10)
            self.assertIsInstance(result, list)


class TestDocumentChunk(unittest.TestCase):
    """DocumentChunk数据类测试"""

    def test_document_chunk_creation(self):
        """测试创建DocumentChunk"""
        from src.esg.vector_store.document_loader import DocumentChunk

        chunk = DocumentChunk(
            text="测试文本",
            source="test_source",
            chunk_index=0,
            total_chunks=1,
            metadata={"key": "value"},
        )

        self.assertEqual(chunk.text, "测试文本")
        self.assertEqual(chunk.source, "test_source")
        self.assertEqual(chunk.chunk_index, 0)
        self.assertEqual(chunk.total_chunks, 1)
        self.assertEqual(chunk.metadata["key"], "value")


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestDocumentLoaderFull))
    suite.addTests(loader.loadTestsFromTestCase(TestLoadJson))
    suite.addTests(loader.loadTestsFromTestCase(TestLoadJsonl))
    suite.addTests(loader.loadTestsFromTestCase(TestChunkDocuments))
    suite.addTests(loader.loadTestsFromTestCase(TestLoadDirectory))
    suite.addTests(loader.loadTestsFromTestCase(TestLoadDocumentsForRag))
    suite.addTests(loader.loadTestsFromTestCase(TestDocumentChunk))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
