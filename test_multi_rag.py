from document_ingestor import DocumentIngestor
from rag_engine import VectorStore
from rag_multi_qa import ask_gemini


def main():
    ingestor = DocumentIngestor()
    store = VectorStore()

    print("Enter file paths separated by commas:")
    paths = input().split(",")

    for path in paths:
        path = path.strip()
        print(f"Loading: {path}")
        text = ingestor.load(path)
        store.add_document(text, source_name=path)

    # Build FAISS index
    store.build()

    question = input("\nEnter your question: ")

    # Retrieve
    results = store.search(question, top_k=5)

    # Answer with Gemini
    answer = ask_gemini(results, question)

    print("\n=== ANSWER ===\n")
    print(answer)


if __name__ == "__main__":
    main()
