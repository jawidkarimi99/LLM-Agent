from database import init_db, add_document, get_all_documents


def main():
    print("Initializing DB...")
    init_db()

    print("Adding sample document...")
    add_document(
        source_type="file",
        path_or_url="/path/to/example.txt",
        raw_text="Hello, this is a test document."
    )

    print("Stored documents:")
    docs = get_all_documents()
    for d in docs:
        print(d)


if __name__ == "__main__":
    main()
