import streamlit as st
import uuid
import io
from core import get_llm, setup_kb, create_graph, add_document_to_kb

st.set_page_config(
    page_title="Legal Document Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
* { font-family: 'Inter', sans-serif; }
.stApp { background: #0f1117; }
section[data-testid="stSidebar"] { background: #161b27 !important; border-right: 1px solid #2d3748; }
.main-header {
    background: linear-gradient(135deg, #1a2744 0%, #243564 100%);
    border: 1px solid #2d4a8a;
    border-radius: 12px;
    padding: 20px 28px;
    margin-bottom: 20px;
}
.main-header h1 { color: #e2e8f0; margin: 0; font-size: 1.6rem; font-weight: 700; }
.main-header p { color: #94a3b8; margin: 4px 0 0 0; font-size: 0.9rem; }
.disclaimer-box {
    background: #1e1b2e;
    border: 1px solid #4a3f6b;
    border-left: 4px solid #7c3aed;
    border-radius: 8px;
    padding: 10px 16px;
    margin-bottom: 16px;
    color: #a78bfa;
    font-size: 0.82rem;
}
.user-bubble {
    background: linear-gradient(135deg, #1e3a5f, #1a2e52);
    border: 1px solid #2d5a9e;
    border-radius: 12px 12px 4px 12px;
    padding: 12px 16px;
    color: #e2e8f0;
    margin: 8px 0;
    max-width: 85%;
    margin-left: auto;
}
.bot-bubble {
    background: #161b27;
    border: 1px solid #2d3748;
    border-radius: 12px 12px 12px 4px;
    padding: 12px 16px;
    color: #e2e8f0;
    margin: 8px 0;
    max-width: 90%;
}
.source-tag {
    display: inline-block;
    background: #1e3a5f;
    border: 1px solid #2d5a9e;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.75rem;
    color: #93c5fd;
    margin: 4px 3px 0 0;
}
.upload-section {
    background: #161b27;
    border: 1px dashed #2d4a8a;
    border-radius: 10px;
    padding: 16px;
    margin-top: 12px;
}
.doc-chip {
    background: #1a2e52;
    border: 1px solid #2d5a9e;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 0.78rem;
    color: #93c5fd;
    margin: 3px 0;
}
</style>
""", unsafe_allow_html=True)


@st.cache_resource(show_spinner="⚖️ Loading legal assistant...")
def init_agent():
    llm = get_llm()
    emb, col = setup_kb()
    app = create_graph(llm, emb, col)
    return llm, emb, col, app


llm, embedder, collection, agent_app = init_agent()

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploaded_docs" not in st.session_state:
    st.session_state.uploaded_docs = []

# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚖️ Legal Document Assistant")
    st.markdown("*Powered by Qwen2.5:3b + Ollama*")
    st.divider()

    # PDF Upload
    st.markdown("### 📄 Upload Case Documents")
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Upload a PDF or TXT file",
        type=["pdf", "txt"],
        label_visibility="collapsed"
    )
    doc_name = st.text_input("Document label (e.g. 'Smith v. Jones contract')", placeholder="Optional label")

    if uploaded_file and st.button("➕ Add to Knowledge Base", type="primary"):
        with st.spinner("Parsing and indexing document..."):
            try:
                if uploaded_file.type == "application/pdf":
                    try:
                        import pdfplumber
                        with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
                            text = "\n".join(p.extract_text() or "" for p in pdf.pages)
                    except ImportError:
                        import PyPDF2
                        reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
                        text = "\n".join(page.extract_text() or "" for page in reader.pages)
                else:
                    text = uploaded_file.read().decode("utf-8", errors="ignore")

                label = doc_name.strip() if doc_name.strip() else uploaded_file.name
                doc_id = f"upload_{uuid.uuid4().hex[:8]}"
                add_document_to_kb(embedder, text, doc_id, label)
                st.session_state.uploaded_docs.append(label)
                st.success(f"✅ '{label}' added to KB")
            except Exception as e:
                st.error(f"Error: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.uploaded_docs:
        st.markdown("**Uploaded Documents:**")
        for d in st.session_state.uploaded_docs:
            st.markdown(f'<div class="doc-chip">📎 {d}</div>', unsafe_allow_html=True)

    st.divider()

    st.markdown("### 📚 Built-in Knowledge Base")
    topics = [
        "Contract Formation & Breach", "Tort Law — Negligence & Liability",
        "Criminal Law & Procedure", "Evidence Rules",
        "Civil Procedure & Jurisdiction", "Constitutional Rights (4th, 5th, 6th)",
        "IP — Copyright, Patents & Trademarks", "Employment Law",
        "Property & Real Estate Law", "Family Law & Divorce",
        "Corporate & Business Entities", "Legal Research & Citation",
        "Litigation & Motions", "Appeals & Standards of Review",
        "ADR — Mediation & Arbitration", "Legal Document Types",
        "Statute of Limitations", "Attorney Ethics"
    ]
    for t in topics:
        st.markdown(f"• {t}")

    st.divider()
    if st.button("🗑️ New Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.rerun()

# ── Main Chat Area ─────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <h1>⚖️ Legal Document Assistant</h1>
  <p>AI-powered legal research for paralegals and junior lawyers • Upload case documents • Ask legal questions</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="disclaimer-box">
  ⚠️ <b>Research Assistant Only</b> — This tool provides legal research support and does not constitute legal advice.
  Always verify answers against primary sources and consult a qualified attorney for legal matters.
</div>
""", unsafe_allow_html=True)

# Welcome message
if not st.session_state.messages:
    st.markdown("""
    <div class="bot-bubble">
      👋 Hello! I'm your Legal Document Assistant.<br><br>
      I can help you research:<br>
      • Contract law, torts, criminal & civil procedure<br>
      • Constitutional rights, evidence, and litigation<br>
      • IP, employment, property, and family law<br>
      • <b>Upload your own case documents</b> using the sidebar<br><br>
      What legal question can I help you with today?
    </div>
    """, unsafe_allow_html=True)

# Display conversation
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="user-bubble">🧑‍💼 {msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="bot-bubble">⚖️ {msg["content"]}</div>', unsafe_allow_html=True)
        if msg.get("sources"):
            sources_html = "".join(f'<span class="source-tag">📎 {s}</span>' for s in msg["sources"])
            st.markdown(f"<div style='margin-left:8px;margin-bottom:8px;'>{sources_html}</div>", unsafe_allow_html=True)

# Input
if prompt := st.chat_input("Ask a legal research question or upload a document in the sidebar..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("⚖️ Researching..."):
        config = {"configurable": {"thread_id": st.session_state.thread_id}}
        result = agent_app.invoke({"question": prompt}, config=config)

    answer = result.get("answer", "I couldn't retrieve an answer. Please try rephrasing.")
    sources = result.get("sources", [])

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources
    })
    st.rerun()
