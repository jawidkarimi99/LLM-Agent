from simple_qa import load_text_from_file
from rag_engine import chunk_text, build_faiss_index, retrieve
from rag_qa import ask_gemini_with_context


def main():
    print("=== RAG Document QA ===")

    path = input("Enter file path: ").strip()
    question = input("Enter your question: ").strip()

    # 1. Load text
    text = load_text_from_file(path)

    # 2. Chunk text
    chunks = chunk_text(text, max_chars=500)

    # 3. Build FAISS index
    index, _ = build_faiss_index(chunks)

    # 4. Retrieve relevant chunks
    top_chunks = retrieve(question, chunks, index, top_k=3)

    print("\n--- Retrieved Chunks ---")
    for i, ch in enumerate(top_chunks, start=1):
        print(f"[Chunk {i}]")
        print(ch[:300], "...\n")

    # 5. Ask Gemini using RAG
    answer = ask_gemini_with_context(top_chunks, question)

    print("\n=== ANSWER ===\n")
    print(answer)


if __name__ == "__main__":
    main()
