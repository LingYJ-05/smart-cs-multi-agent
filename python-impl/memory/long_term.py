"""
长期记忆 — 基于向量数据库的持久化记忆
存储用户画像、历史工单、知识库文档等需要持久化的信息。
支持语义相似度检索，用于RAG知识检索Agent。
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

try:
    import faiss
except ImportError:
    faiss = None


class LongTermMemory:
    """
    长期记忆：基于FAISS的向量检索。

    特点：
    - 向量化存储，支持语义相似度检索
    - 持久化到磁盘，跨会话保持
    - 支持增量更新和批量导入
    - 生产环境可切换为Milvus/Pinecone

    文档分块策略：
    - 固定长度分块 (512 tokens) + 重叠窗口 (128 tokens)
    - 按段落自然分割优先
    """

    def __init__(
        self,
        index_path: str = "./vector_store/faiss_index",
        embedding_dim: int = 1536,
    ):
        self.index_path = Path(index_path)
        self.embedding_dim = embedding_dim
        self._documents: list[dict[str, Any]] = []
        self._index = None
        self._init_index()

    def _init_index(self):
        """初始化FAISS索引"""
        if faiss is None:
            self._index = None
            return

        metadata_path = self.index_path.with_suffix(".meta.json")
        if self.index_path.exists():
            try:
                self._index = faiss.read_index(str(self.index_path))
                if metadata_path.exists():
                    with open(metadata_path, "r", encoding="utf-8") as f:
                        self._documents = json.load(f)
            except Exception:
                self._index = faiss.IndexFlatIP(self.embedding_dim)
        else:
            self._index = faiss.IndexFlatIP(self.embedding_dim)

    def _simple_embedding(self, text: str) -> np.ndarray:
        """
        简易文本嵌入（演示用）。
        生产环境应替换为 OpenAI Embedding API 或本地模型。
        """
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        np.random.seed(int(text_hash[:8], 16) % (2**32))
        vec = np.random.randn(self.embedding_dim).astype(np.float32)
        vec /= np.linalg.norm(vec)
        return vec

    def add_document(self, content: str, source: str = "", metadata: dict | None = None) -> str:
        """添加文档到向量库"""
        doc_id = hashlib.md5(content.encode()).hexdigest()[:12]

        doc = {
            "id": doc_id,
            "content": content,
            "source": source,
            "metadata": metadata or {},
        }
        self._documents.append(doc)

        if self._index is not None:
            embedding = self._simple_embedding(content)
            self._index.add(embedding.reshape(1, -1))

        return doc_id

    def add_documents_batch(self, documents: list[dict]) -> list[str]:
        """批量添加文档"""
        doc_ids = []
        for doc in documents:
            doc_id = self.add_document(
                content=doc.get("content", ""),
                source=doc.get("source", ""),
                metadata=doc.get("metadata", {}),
            )
            doc_ids.append(doc_id)
        return doc_ids

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """语义相似度检索"""
        if self._index is None or not self._documents:
            return self._fallback_search(query, top_k)

        query_vec = self._simple_embedding(query).reshape(1, -1)
        scores, indices = self._index.search(query_vec, min(top_k, len(self._documents)))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self._documents):
                continue
            doc = self._documents[idx].copy()
            doc["score"] = float(score)
            results.append(doc)

        return results

    def _fallback_search(self, query: str, top_k: int) -> list[dict]:
        """当FAISS不可用时的关键词回退搜索"""
        scored = []
        query_terms = set(query.lower().split())

        for doc in self._documents:
            content_lower = doc["content"].lower()
            score = sum(1 for term in query_terms if term in content_lower)
            if score > 0:
                scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[:top_k]]

    def save(self):
        """持久化索引到磁盘"""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        if self._index is not None:
            faiss.write_index(self._index, str(self.index_path))

        metadata_path = self.index_path.with_suffix(".meta.json")
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(self._documents, f, ensure_ascii=False, indent=2)

    def load_knowledge_base(self, kb_dir: str) -> int:
        """从目录批量加载知识库文档"""
        kb_path = Path(kb_dir)
        if not kb_path.exists():
            return 0

        count = 0
        for file_path in kb_path.glob("**/*.txt"):
            content = file_path.read_text(encoding="utf-8")
            chunks = self._chunk_text(content)
            for chunk in chunks:
                self.add_document(
                    content=chunk,
                    source=str(file_path.name),
                    metadata={"file": str(file_path)},
                )
                count += 1

        return count

    @staticmethod
    def _split_text_by_separator(text: str, separator: str) -> list[str]:
        """按分隔符分割文本，保留分隔符"""
        if not separator:
            return list(text)
        parts = text.split(separator)
        return [p + separator for p in parts[:-1]] + [parts[-1]]

    @staticmethod
    def _merge_small_chunks(chunks: list[str], chunk_size: int, separator: str) -> list[str]:
        """合并过小的分块"""
        merged = []
        current = ""
        for chunk in chunks:
            if len(current) + len(chunk) <= chunk_size:
                current += chunk
            else:
                if current:
                    merged.append(current.strip())
                current = chunk
        if current.strip():
            merged.append(current.strip())
        return merged

    @classmethod
    def _recursive_chunk(
        cls,
        text: str,
        chunk_size: int,
        overlap: int,
        separators: list[str],
        separator_idx: int = 0,
    ) -> list[str]:
        """
        递归文档切块：按分隔符层级逐级细分。
        分隔符层级：段落(\\n\\n) → 换行(\\n) → 中文句号(。) → 英文句号(.) → 分号(；) → 逗号(，) → 空格 → 字符
        """
        if separator_idx >= len(separators):
            chunks = []
            for i in range(0, len(text), chunk_size):
                chunks.append(text[i:i + chunk_size])
            return chunks

        separator = separators[separator_idx]
        splits = cls._split_text_by_separator(text, separator)

        if len(splits) <= 1:
            return cls._recursive_chunk(text, chunk_size, overlap, separators, separator_idx + 1)

        chunks = []
        current_chunk = ""

        for split in splits:
            if len(current_chunk) + len(split) <= chunk_size:
                current_chunk += split
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())

                if len(split) > chunk_size:
                    sub_chunks = cls._recursive_chunk(
                        split, chunk_size, overlap, separators, separator_idx + 1
                    )
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    overlap_text = current_chunk[-overlap:] if current_chunk and len(current_chunk) > overlap else ""
                    current_chunk = overlap_text + split

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    @staticmethod
    def _chunk_text(text: str, chunk_size: int = 512, overlap: int = 128) -> list[str]:
        """
        递归文档切块（RecursiveCharacterTextSplitter）。
        
        分层策略：
        1. 段落边界（\\n\\n）- 优先保持段落完整性
        2. 换行符（\\n）- 保持行完整性
        3. 中文句号（。）- 保持中文句子完整性
        4. 英文句号（.）- 保持英文句子完整性
        5. 分号（；/;）- 保持分句完整性
        6. 逗号（，/,）- 保持短语完整性
        7. 空格 - 保持词语完整性
        8. 字符 - 最后兜底，按字符切割
        
        同时应用重叠窗口确保上下文连贯。
        """
        if not text or not text.strip():
            return []

        if len(text) <= chunk_size:
            return [text.strip()]

        separators = [
            "\n\n",
            "\n",
            "。",
            ".",
            "；",
            ";",
            "，",
            ",",
            " ",
            "",
        ]

        chunks = LongTermMemory._recursive_chunk(
            text, chunk_size, overlap, separators
        )

        result = []
        for chunk in chunks:
            chunk = chunk.strip()
            if chunk:
                result.append(chunk)

        return result if result else [text[:chunk_size]]
