from export_utils import export_to_csv, export_to_excel, export_to_docx
import database
from document_ingestor import DocumentIngestor
from rag_engine import VectorStore
from rag_qa import ask_gemini_with_context
from rag_engine import build_vector_store_from_db, run_rag_query
from flask import (
    Flask,
    request,
    render_template,
    jsonify,
    send_file,
    redirect,
    url_for,
    send_from_directory,
    session
)
import os
import io

from dotenv import load_dotenv
load_dotenv()


# ---------------------------------------------------
# CREATE APP ONE TIME ONLY
# ---------------------------------------------------
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "super-secret-key-change-this")
app.config["UPLOAD_FOLDER"] = "uploads"

# Make sure uploads folder exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Initialize DB + ingestor
database.init_db()
ingestor = DocumentIngestor()

# Chat history in memory
chat_history: list[dict] = []


# ----------------------------------------------------------
# FIXED: move vector store helper before any route that uses it
# ----------------------------------------------------------
def _build_vector_store():
    """
    Load all docs from DB and build FAISS vector store.
    Used for both /ask and /chat/send.
    """
    docs = database.get_all_documents()
    if not docs:
        return None, []

    vs = VectorStore()
    sources = []

    for (doc_id, source_type, path_or_url, raw_text, summary) in docs:
        if not raw_text:
            continue
        vs.add_document(raw_text, source_name=path_or_url)
        sources.append(path_or_url)

    if not vs.chunks:
        return None, sources

    vs.build()
    return vs, sources


# ------------------------
# ROUTES
# ------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat")
def chat():
    return render_template("chat.html", messages=chat_history)


@app.route("/documents")
def documents():
    docs = database.get_all_documents()
    return render_template("documents.html", docs=docs)


@app.route("/documents/delete/<int:doc_id>", methods=["POST"])
def delete_document(doc_id):
    database.delete_document(doc_id)
    return redirect(url_for("documents"))


@app.route("/reset_kb", methods=["POST"])
def reset_kb():
    global chat_history

    database.clear_all_documents()

    upload_dir = app.config["UPLOAD_FOLDER"]
    for f in os.listdir(upload_dir):
        try:
            os.remove(os.path.join(upload_dir, f))
        except:
            pass

    chat_history = []

    return jsonify({"success": True})


@app.route("/upload", methods=["POST"])
def upload():
    files = request.files.getlist("file")
    if not files:
        return jsonify({"error": "No files uploaded"}), 400

    from ocr_utils import extract_text_from_image, extract_text_from_scanned_pdf

    results = []

    for file in files:
        filename = file.filename
        lower = filename.lower()
        file_bytes = file.read()

        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        with open(save_path, "wb") as f:
            f.write(file_bytes)

        # Images → OCR
        if lower.endswith((".png", ".jpg", ".jpeg")):
            text = extract_text_from_image(file_bytes)
            database.add_document("image", save_path, text)
            results.append({"file": filename, "type": "image", "ocr": True})
            continue

        # PDF → OCR or fallback
        if lower.endswith(".pdf"):
            text = extract_text_from_scanned_pdf(save_path)
            if not text or text.startswith("[OCR_PDF_ERROR]"):
                text = ingestor.load(save_path)
            database.add_document("pdf", save_path, text)
            results.append({"file": filename, "type": "pdf", "ocr": True})
            continue

        # TXT / DOCX / other
        text = ingestor.load(save_path)
        database.add_document("file", save_path, text)
        results.append({"file": filename, "type": "file", "ocr": False})

    return jsonify({"success": True, "results": results})


@app.route("/fetch_url", methods=["POST"])
def fetch_url():
    url = request.form.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        text = ingestor.load(url)
        database.add_document("url", url, text)
        return jsonify({"success": True, "url": url})
    except Exception as e:
        return jsonify({"error": f"Failed to fetch: {str(e)}"}), 500


@app.route("/ask", methods=["POST"])
def ask_question():
    question = request.form.get("question", "").strip()
    if not question:
        return jsonify({"answer": "Please enter a question.", "chunks": []})

    vs, kb_texts = _build_vector_store()
    if vs is None:
        # no documents → still produce an answer without RAG
        answer = ask_gemini_with_context([], question)
        session["last_export"] = []
        session["last_answer"] = answer
        session["last_question"] = question
        return jsonify({"answer": answer, "chunks": []})

    search_results = vs.search(question, top_k=4)
    retrieved_chunks = [item["text"] for item in search_results]

    answer = ask_gemini_with_context(retrieved_chunks, question)

    # 🔥 REQUIRED FOR EXPORT
    session["last_export"] = retrieved_chunks
    session["last_answer"] = answer
    session["last_question"] = question

    return jsonify({"answer": answer, "chunks": retrieved_chunks})


@app.route("/export_results", methods=["POST"])
def export_results():
    export_format = request.form.get("format", "csv")

    rows = session.get("last_export", [])
    answer = session.get("last_answer", "")
    question = session.get("last_question", "")

    if not rows:
        return jsonify({"error": "No data to export."}), 400

    buffer = io.BytesIO()

    if export_format == "csv":
        export_to_csv(rows, question, answer, buffer)
        buffer.seek(0)
        return send_file(buffer, mimetype="text/csv",
                         as_attachment=True, download_name="rag_export.csv")

    elif export_format == "excel":
        export_to_excel(rows, question, answer, buffer)
        buffer.seek(0)
        return send_file(buffer, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                         as_attachment=True, download_name="rag_export.xlsx")

    elif export_format == "docx":
        export_to_docx(rows, question, answer, buffer)
        buffer.seek(0)
        return send_file(buffer, mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                         as_attachment=True, download_name="rag_export.docx")

    return jsonify({"error": "Invalid format"}), 400


@app.route("/chat/send", methods=["POST"])
def chat_send():
    """
    Chat endpoint:
    - Keeps short-term conversation history
    - Uses RAG only if documents exist
    - If no documents in KB → answer normally (ChatGPT-like)
    """
    global chat_history

    message = request.form.get("message", "").strip()
    if not message:
        return jsonify({"error": "Empty message."}), 400

    # Build vector store (if docs exist)
    vs, _ = _build_vector_store()

    # Build short conversation summary (last 6 turns)
    history_text_lines = []
    for turn in chat_history[-6:]:
        role = turn["role"]
        content = turn["content"]
        history_text_lines.append(f"{role.capitalize()}: {content}")
    history_text = "\n".join(history_text_lines)

    # If documents exist → do RAG retrieval
    if vs is not None:
        search_results = vs.search(message, top_k=4)
        retrieved_chunks = [item["text"] for item in search_results]
    else:
        # No documents → empty context
        retrieved_chunks = []

    # Final prompt
    question_for_llm = (
        "You are in a conversation with the user.\n"
        "If external document context is provided, use it; otherwise answer normally.\n\n"
        "Conversation so far:\n"
        f"{history_text}\n\n"
        f"User's latest message: {message}\n\n"
        "Reply as a helpful assistant."
    )

    answer = ask_gemini_with_context(retrieved_chunks, question_for_llm)

    # Update chat history
    chat_history.append({"role": "user", "content": message})
    chat_history.append({"role": "assistant", "content": answer})

    return jsonify({"messages": chat_history})


@app.route("/chat/clear", methods=["POST"])
def chat_clear():
    global chat_history
    chat_history = []
    return jsonify({"success": True, "messages": []})


@app.route("/summarize", methods=["POST"])
def summarize():
    docs = database.get_all_documents()
    if not docs:
        return jsonify({"error": "No documents in DB."})

    summaries = []
    for (doc_id, source_type, src, raw_text, summary) in docs:
        if summary and summary.strip():
            new = summary
        else:
            chunk = (raw_text or "")[:8000]
            prompt = f"Summarize this clearly:\n\n{chunk}"
            new = ask_gemini_with_context([chunk], prompt)
            database.update_summary(doc_id, new)

        summaries.append({"id": doc_id, "source": src, "summary": new})

    return jsonify({"summaries": summaries})


@app.route("/visualize")
def visualize():
    docs = database.get_all_documents()
    data = []
    for (doc_id, t, src, raw, sumry) in docs:
        data.append({
            "id": doc_id,
            "source": src,
            "type": t,
            "length": len(raw or ""),
            "summary_length": len(sumry or "") if sumry else 0,
        })
    return render_template("visualize.html", data=data)


@app.route("/files/<path:filename>")
def serve_uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    app.run(debug=True)
