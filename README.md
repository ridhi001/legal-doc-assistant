# ⚖️ Legal Document Assistant

An AI-powered legal research assistant for **paralegals and junior lawyers**, built with **LangGraph**, **ChromaDB**, and **Ollama (Qwen2.5:3b)**. Fully offline. No API keys required.

> **Disclaimer:** This tool provides legal research support only. It does not constitute legal advice. Always verify with primary sources and a qualified attorney.

---

## 🏗️ Architecture

Same 8-node LangGraph state machine as the E-Commerce FAQ Bot, adapted for legal research:

```
User Question
    │
    ▼
memory → router ──► retrieve → answer
                ├──► skip    → answer  → eval → save → END
                └──► tool    → answer
```

## 🚀 Setup & Run

### Prerequisites
- Python 3.9+
- [Ollama](https://ollama.com) installed

### 1. Install dependencies
```bash
cd legal-doc-assistant
pip install -r requirements.txt
```

### 2. Pull the model
```bash
ollama pull qwen2.5:3b
```

### 3. Run the app
```bash
streamlit run capstone_streamlit.py
```

---

## ✨ Key Features

### 📄 PDF / TXT Document Upload
- Upload your own case documents, contracts, or legal briefs via the sidebar
- Uploaded text is automatically chunked and indexed into ChromaDB
- The assistant can immediately answer questions about uploaded documents

### 📚 Pre-loaded Legal Knowledge Base (25 topics)
| Category | Topics |
|----------|--------|
| Contract Law | Formation, breach, remedies, defences |
| Tort Law | Negligence, strict liability, vicarious liability |
| Criminal Law | Elements of crime, criminal procedure |
| Evidence | Admissibility, hearsay, best evidence rule |
| Civil Procedure | Jurisdiction, pleadings, discovery, motions |
| Constitutional Law | 4th, 5th, and 6th Amendment rights |
| Intellectual Property | Copyright, patents, trademarks |
| Employment Law | Wrongful termination, discrimination |
| Property Law | Real property transfer, title |
| Family Law | Divorce, property division |
| Corporate Law | Business entity types |
| Legal Research | Citation format, primary vs secondary authority |
| Litigation | Pre-trial motions, appeals, standards of review |
| ADR | Mediation, arbitration |
| Ethics | Attorney professional responsibility |

### 🔧 Tool: Legal Deadline Helper
- Ask "What is today's date?" to get current date/time for calculating limitations periods and filing deadlines

---

## 📁 Project Structure

```
├── agent.py                  # LangGraph agent, KB, LLM, PDF chunking
├── capstone_streamlit.py     # Streamlit UI with PDF upload
├── requirements.txt
├── README.md
└── .gitignore
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | Qwen2.5:3b via Ollama (local) |
| Agent Framework | LangGraph |
| Vector Store | ChromaDB |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| PDF Parsing | pdfplumber / PyPDF2 |
| UI | Streamlit |
| Memory | LangGraph MemorySaver |
