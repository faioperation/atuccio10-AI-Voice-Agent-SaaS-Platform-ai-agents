import os
import json
import faiss
import numpy as np
from typing import List
from docx import Document
from sentence_transformers import SentenceTransformer
from app.config import settings
from app.utils.logger import logger

_INDEX_FILE = ".faiss_index"
_DOCS_FILE  = ".faiss_docs.json"


class RAGEngine:
    def __init__(self):
        self.model     = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.index     = None
        self.documents: List[str] = []
        self.kb_path   = settings.KNOWLEDGE_BASE_DIR

        if not os.path.exists(self.kb_path):
            os.makedirs(self.kb_path)
            logger.info(f"Created knowledge base directory: {self.kb_path}")

        # Try to load a previously saved index so startup is fast
        if not self._load_index():
            logger.info("No cached FAISS index found; will build on first use.")

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _index_path(self) -> str:
        return os.path.join(self.kb_path, _INDEX_FILE)

    def _docs_path(self) -> str:
        return os.path.join(self.kb_path, _DOCS_FILE)

    def _save_index(self):
        """Persist FAISS index and document list to the knowledge base dir."""
        if self.index is None or not self.documents:
            return
        try:
            faiss.write_index(self.index, self._index_path())
            with open(self._docs_path(), "w", encoding="utf-8") as f:
                json.dump(self.documents, f, ensure_ascii=False)
            logger.info(f"FAISS index saved ({len(self.documents)} chunks).")
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")

    def _load_index(self) -> bool:
        """Load a previously persisted FAISS index. Returns True on success."""
        idx_path  = self._index_path()
        docs_path = self._docs_path()
        if not (os.path.exists(idx_path) and os.path.exists(docs_path)):
            return False
        try:
            self.index = faiss.read_index(idx_path)
            with open(docs_path, "r", encoding="utf-8") as f:
                self.documents = json.load(f)
            logger.info(f"FAISS index loaded from disk ({len(self.documents)} chunks).")
            return True
        except Exception as e:
            logger.error(f"Failed to load FAISS index: {e}")
            return False

    # ------------------------------------------------------------------
    # Document processing
    # ------------------------------------------------------------------

    def load_docx(self, file_path: str) -> str:
        """Extract plain text from a DOCX file."""
        doc = Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping word-level chunks."""
        words  = text.split()
        chunks = []
        step   = chunk_size - overlap
        for i in range(0, len(words), step):
            chunk = " ".join(words[i : i + chunk_size])
            if chunk:
                chunks.append(chunk)
        return chunks

    def build_index(self):
        """Process all DOCX files in the knowledge directory and rebuild the FAISS index."""
        logger.info("Building RAG index...")
        all_chunks: List[str] = []

        for filename in os.listdir(self.kb_path):
            if filename.endswith(".docx"):
                file_path = os.path.join(self.kb_path, filename)
                text      = self.load_docx(file_path)
                chunks    = self.chunk_text(text)
                all_chunks.extend(chunks)
                logger.info(f"Indexed '{filename}' → {len(chunks)} chunks.")

        if not all_chunks:
            logger.warning("No DOCX files found in knowledge base. RAG index is empty.")
            return

        self.documents = all_chunks
        embeddings     = self.model.encode(all_chunks, show_progress_bar=False)
        dimension      = embeddings.shape[1]

        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(np.array(embeddings, dtype="float32"))
        logger.info(f"RAG index built with {len(all_chunks)} chunks.")

        # Persist to disk so the next startup skips re-encoding
        self._save_index()

    def query(self, query_text: str, k: int = 3) -> str:
        """Retrieve the top-k most relevant chunks for a query."""
        if not self.index or not self.documents:
            logger.warning("RAG index is empty — returning no context.")
            return ""

        query_vector          = self.model.encode([query_text], show_progress_bar=False).astype("float32")
        distances, indices    = self.index.search(query_vector, k)
        results               = [self.documents[i] for i in indices[0] if i != -1]
        return "\n\n".join(results)


rag_engine = RAGEngine()
