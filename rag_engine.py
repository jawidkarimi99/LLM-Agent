import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

import database  # <-- required for loading docs

# Global embedder
embedder = SentenceTransformer("all-MiniLM-L6-v2")


# -----------------------------
# Vector Store Class
# -----------------------------
class VectorStore:
    def __init__(self):
        self.chunks = []
        self.metadatas = []
        self.index = None

    def add_document(self, text, source_name, max_chars=500):
        """Chunk and store text from a document."""
        chunk_list = self._chunk_text(text, max_chars)

        for i, chunk in enumerate(chunk_list):
            self.chunks.append(chunk)
            self.metadatas.append({
                "source": source_name,
                "chunk_id": i
            })

    def _chunk_text(self, text, max_chars=500):
        """Split text into multiple chunks."""
        chunks = []
        current = ""

        for line in text.split("\n"):
            if len(current) + len(line) < max_chars:
                current += line + "\n"
            else:
                chunks.append(current.strip())
                current = line + "\n"

        if current.strip():
            chunks.append(current.strip())

        return chunks

    def build(self):
        if not self.chunks:
            raise ValueError("No chunks to index.")

        embeddings = embedder.encode(self.chunks)
        embeddings = np.array(embeddings).astype("float32")

        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dim)
        self.index.add(embeddings)

    def search(self, query, top_k=5):
        if self.index is None:
            raise RuntimeError("Index not built.")

        query_embed = embedder.encode([query]).astype("float32")
        distances, indices = self.index.search(query_embed, top_k)

        results = []
        for idx in indices[0]:
            results.append({
                "text": self.chunks[idx],
                "meta": self.metadatas[idx]
            })

        return results


# ----------------------------------------------------
# NEW: Build vector store using all docs in DATABASE
# ----------------------------------------------------
def build_vector_store_from_db():
    """
    Loads all raw_text from DB, builds FAISS index.

    Returns:
        vs: VectorStore or None
        texts: list of all document texts (flattened)
    """
    docs = database.get_all_documents()
    if not docs:
        return None, []

    vs = VectorStore()
    all_texts = []

    for doc_id, source_type, path_or_url, raw_text, summary in docs:
        if not raw_text:
            continue

        vs.add_document(raw_text, source_name=path_or_url)
        all_texts.append(raw_text)

    if not vs.chunks:
        return None, all_texts

    vs.build()
    return vs, all_texts


# ----------------------------------------------------
# NEW: General RAG Query Helper
# ----------------------------------------------------
def run_rag_query(question, top_k=4):
    """
    Runs a question against vector DB.
    Returns retrieved_chunks.
    """
    vs, _ = build_vector_store_from_db()

    if vs is None:
        return []

    hits = vs.search(question, top_k=top_k)
    return [h["text"] for h in hits]
