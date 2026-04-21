import os
import faiss
import numpy as np
from typing import List, Dict
from docx import Document
from sentence_transformers import SentenceTransformer
from app.config import settings
from app.utils.logger import logger

class RAGEngine:
    def __init__(self):
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.index = None
        self.documents = []
        self.kb_path = settings.KNOWLEDGE_BASE_DIR
        
        if not os.path.exists(self.kb_path):
            os.makedirs(self.kb_path)
            logger.info(f"Created knowledge base directory: {self.kb_path}")

    def load_docx(self, file_path: str) -> str:
        """Extracts text from a DOCX file."""
        doc = Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text)
        return "\n".join(full_text)

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Chunks text into smaller pieces for embedding."""
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)
        return chunks

    def build_index(self):
        """Processes all DOCX files in the knowledge directory and builds the FAISS index."""
        logger.info("Building RAG index...")
        all_chunks = []
        for filename in os.listdir(self.kb_path):
            if filename.endswith(".docx"):
                file_path = os.path.join(self.kb_path, filename)
                text = self.load_docx(file_path)
                chunks = self.chunk_text(text)
                all_chunks.extend(chunks)
        
        if not all_chunks:
            logger.warning("No DOCX files found in knowledge base. Index will be empty.")
            return

        self.documents = all_chunks
        embeddings = self.model.encode(all_chunks)
        dimension = embeddings.shape[1]
        
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(np.array(embeddings).astype('float32'))
        logger.info(f"RAG index built with {len(all_chunks)} chunks.")

    def query(self, query_text: str, k: int = 3) -> str:
        """Retrieves the most relevant chunks for a given query."""
        if not self.index or not self.documents:
            return ""
        
        query_vector = self.model.encode([query_text]).astype('float32')
        distances, indices = self.index.search(query_vector, k)
        
        results = [self.documents[i] for i in indices[0] if i != -1]
        return "\n\n".join(results)

rag_engine = RAGEngine()
