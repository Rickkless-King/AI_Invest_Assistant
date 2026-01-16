"""
RAG服务模块 - 检索增强生成

核心原理（面试必背）：
1. Embedding（向量化）：把文字变成向量，语义相近的文字向量也相近
2. 向量数据库：存储向量，支持快速找到"最相近"的内容
3. 检索增强：用户提问时，先检索相关内容，再让LLM基于这些内容回答

流程：
用户问题 → 向量化 → 检索相似文档 → 文档+问题给LLM → 生成回答
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
import hashlib
import json

# PDF解析
from pypdf import PdfReader

# 文本分块 - 把长文档切成小段
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 向量数据库 - 存储和检索向量
import chromadb
from chromadb.config import Settings

# 向量化模型 - 把文字变成向量
from sentence_transformers import SentenceTransformer


class TradingRAGService:
    """
    交易书籍RAG服务

    面试时这样解释：
    "我实现了一个RAG系统，用来让AI助手能够引用交易书籍的内容。
    具体来说，我先用sentence-transformers把书籍内容向量化存入ChromaDB，
    用户提问时先检索相关段落，再把这些段落作为context传给LLM生成回答。"
    """

    def __init__(self,
                 rag_material_path: str = None,
                 persist_directory: str = None):
        """
        初始化RAG服务

        Args:
            rag_material_path: PDF书籍所在目录
            persist_directory: 向量数据库持久化目录
        """
        # 设置路径
        base_path = Path(__file__).parent.parent.parent  # AI_Invest_Assistant目录
        self.rag_material_path = Path(rag_material_path) if rag_material_path else base_path / "rag_material"
        self.persist_directory = Path(persist_directory) if persist_directory else base_path / "data" / "chroma_db"

        # 确保目录存在
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        # ========== 核心组件1: Embedding模型 ==========
        # 这个模型把文字变成向量（一串数字）
        # 使用多语言模型，支持中文
        # 面试点：为什么用这个模型？因为支持中文，且不需要API费用
        print("正在加载Embedding模型...")
        self.embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        print("Embedding模型加载完成")

        # ========== 核心组件2: 向量数据库 ==========
        # ChromaDB：轻量级向量数据库，数据存在本地
        # 面试点：为什么用ChromaDB？轻量、易用、支持持久化
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False)
        )

        # 获取或创建collection（类似数据库的表）
        self.collection = self.chroma_client.get_or_create_collection(
            name="trading_books",
            metadata={"description": "交易书籍知识库"}
        )

        # ========== 核心组件3: 文本分块器 ==========
        # 为什么要分块？因为：
        # 1. LLM有token限制，不能一次传入整本书
        # 2. 检索时需要找到具体段落，不是整本书
        # 面试点：chunk_size和chunk_overlap怎么选？
        # - chunk_size: 每块大小，太大检索不精确，太小丢失上下文
        # - chunk_overlap: 重叠部分，避免重要内容被切断
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,      # 每块约500字符
            chunk_overlap=100,   # 重叠100字符，保证上下文连贯
            separators=["\n\n", "\n", "。", "！", "？", ".", " "],  # 优先在这些位置切分
        )

        # 记录已处理的文件（避免重复处理）
        self.processed_files_path = self.persist_directory / "processed_files.json"
        self.processed_files = self._load_processed_files()

    def _load_processed_files(self) -> Dict:
        """加载已处理文件记录"""
        if self.processed_files_path.exists():
            with open(self.processed_files_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_processed_files(self):
        """保存已处理文件记录"""
        with open(self.processed_files_path, 'w', encoding='utf-8') as f:
            json.dump(self.processed_files, f, ensure_ascii=False, indent=2)

    def _get_file_hash(self, file_path: Path) -> str:
        """计算文件hash，用于检测文件是否变化"""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        """
        从PDF提取文本

        面试点：PDF解析的挑战？
        - 中文PDF可能有编码问题
        - 扫描版PDF需要OCR（这里不处理）
        - 有些PDF有加密
        """
        try:
            reader = PdfReader(str(pdf_path))
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
        except Exception as e:
            print(f"解析PDF失败 {pdf_path.name}: {e}")
            return ""

    def index_documents(self, force_reindex: bool = False) -> Dict:
        """
        索引所有PDF文档

        这是RAG的"离线"阶段：
        1. 读取PDF
        2. 分块
        3. 向量化
        4. 存入向量数据库

        Args:
            force_reindex: 是否强制重新索引（即使文件没变）

        Returns:
            处理结果统计
        """
        results = {
            "processed": [],
            "skipped": [],
            "failed": [],
            "total_chunks": 0
        }

        # 遍历rag_material目录下的所有PDF
        pdf_files = list(self.rag_material_path.glob("*.pdf"))
        print(f"找到 {len(pdf_files)} 个PDF文件")

        for pdf_path in pdf_files:
            file_hash = self._get_file_hash(pdf_path)
            file_name = pdf_path.name

            # 检查是否需要处理
            if not force_reindex and file_name in self.processed_files:
                if self.processed_files[file_name]["hash"] == file_hash:
                    print(f"跳过（未变化）: {file_name}")
                    results["skipped"].append(file_name)
                    continue

            print(f"处理中: {file_name}")

            # ========== 步骤1: 提取文本 ==========
            text = self._extract_text_from_pdf(pdf_path)
            if not text:
                results["failed"].append(file_name)
                continue

            # ========== 步骤2: 文本分块 ==========
            # 把长文本切成小段
            chunks = self.text_splitter.split_text(text)
            print(f"  分成 {len(chunks)} 个块")

            # ========== 步骤3: 向量化并存储 ==========
            # 为每个chunk生成唯一ID
            chunk_ids = [f"{file_name}_{i}" for i in range(len(chunks))]

            # 准备metadata（元数据，记录这个chunk来自哪本书）
            metadatas = [{"source": file_name, "chunk_index": i} for i in range(len(chunks))]

            # 向量化：把文字变成向量
            # 面试点：这一步是整个RAG最核心的地方
            embeddings = self.embedding_model.encode(chunks).tolist()

            # 先删除这个文件的旧数据（如果有）
            try:
                existing_ids = [f"{file_name}_{i}" for i in range(10000)]  # 假设最多10000块
                self.collection.delete(ids=existing_ids)
            except:
                pass

            # 存入向量数据库
            self.collection.add(
                ids=chunk_ids,
                documents=chunks,
                embeddings=embeddings,
                metadatas=metadatas
            )

            # 记录已处理
            self.processed_files[file_name] = {
                "hash": file_hash,
                "chunks": len(chunks)
            }
            results["processed"].append(file_name)
            results["total_chunks"] += len(chunks)

        # 保存处理记录
        self._save_processed_files()

        print(f"\n索引完成: 处理{len(results['processed'])}个, 跳过{len(results['skipped'])}个, 失败{len(results['failed'])}个")
        return results

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        检索相关文档

        这是RAG的"在线"阶段：
        1. 把用户问题向量化
        2. 在向量数据库中找到最相似的chunks
        3. 返回这些chunks

        Args:
            query: 用户问题
            top_k: 返回最相关的k个结果

        Returns:
            相关文档列表，每个包含content和source
        """
        # 检查数据库是否为空
        if self.collection.count() == 0:
            print("向量数据库为空，请先运行 index_documents()")
            return []

        # ========== 步骤1: 向量化查询 ==========
        query_embedding = self.embedding_model.encode([query]).tolist()

        # ========== 步骤2: 相似度搜索 ==========
        # ChromaDB会计算query向量与所有存储向量的相似度
        # 返回最相似的top_k个
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        # ========== 步骤3: 整理结果 ==========
        retrieved_docs = []
        for i in range(len(results["documents"][0])):
            retrieved_docs.append({
                "content": results["documents"][0][i],
                "source": results["metadatas"][0][i]["source"],
                "distance": results["distances"][0][i]  # 距离越小越相似
            })

        return retrieved_docs

    def get_context_for_llm(self, query: str, top_k: int = 3) -> str:
        """
        获取用于LLM的上下文

        这个方法是给LLM用的：
        1. 检索相关文档
        2. 格式化成LLM能理解的context

        Args:
            query: 用户问题
            top_k: 检索数量

        Returns:
            格式化的context字符串
        """
        docs = self.retrieve(query, top_k)

        if not docs:
            return ""

        # 格式化context
        context_parts = []
        for i, doc in enumerate(docs, 1):
            # 去掉.pdf后缀，让来源更美观
            source_name = doc["source"].replace(".pdf", "")
            context_parts.append(f"【参考资料{i} - 来源：{source_name}】\n{doc['content']}")

        context = "\n\n".join(context_parts)
        return context

    def get_stats(self) -> Dict:
        """获取知识库统计信息"""
        return {
            "total_chunks": self.collection.count(),
            "processed_files": list(self.processed_files.keys()),
            "rag_material_path": str(self.rag_material_path),
            "persist_directory": str(self.persist_directory)
        }


# ==================== 便捷函数 ====================

# 全局实例（单例模式）
_rag_service_instance = None

def get_rag_service() -> TradingRAGService:
    """
    获取RAG服务实例（单例）

    使用单例是因为：
    1. 加载Embedding模型比较慢，只需要加载一次
    2. 向量数据库连接只需要一个
    """
    global _rag_service_instance
    if _rag_service_instance is None:
        _rag_service_instance = TradingRAGService()
    return _rag_service_instance


def reset_rag_service():
    """重置RAG服务实例"""
    global _rag_service_instance
    _rag_service_instance = None


# ==================== 测试代码 ====================

if __name__ == "__main__":
    """
    测试RAG服务

    运行方式：
    cd AI_Invest_Assistant
    python -m backend.rag.rag_service
    """
    print("=" * 50)
    print("RAG服务测试")
    print("=" * 50)

    # 1. 初始化服务
    print("\n1. 初始化RAG服务...")
    rag = get_rag_service()

    # 2. 索引文档
    print("\n2. 索引PDF文档...")
    results = rag.index_documents()
    print(f"   结果: {results}")

    # 3. 查看统计
    print("\n3. 知识库统计:")
    stats = rag.get_stats()
    print(f"   总chunks: {stats['total_chunks']}")
    print(f"   已处理文件: {stats['processed_files']}")

    # 4. 测试检索
    print("\n4. 测试检索:")
    test_queries = [
        "止损应该怎么设置？",
        "什么是趋势跟踪？",
        "如何控制交易风险？"
    ]

    for query in test_queries:
        print(f"\n   问题: {query}")
        docs = rag.retrieve(query, top_k=2)
        for doc in docs:
            print(f"   - 来源: {doc['source']}")
            print(f"     内容: {doc['content'][:100]}...")
            print(f"     相似度距离: {doc['distance']:.4f}")

    print("\n" + "=" * 50)
    print("测试完成！")
