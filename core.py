import os
import re
import datetime
from typing import TypedDict, List
from sentence_transformers import SentenceTransformer
import chromadb
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

OLLAMA_PATH = "/usr/local/bin/ollama"
OLLAMA_MODEL = "qwen2.5:3b"

def _ensure_ollama_running():
    import subprocess, time
    try:
        import httpx
        httpx.get("http://localhost:11434", timeout=2)
        return
    except Exception:
        pass
    subprocess.Popen([OLLAMA_PATH, "serve"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)

def get_llm():
    print(f"🦙 Starting Ollama local model: {OLLAMA_MODEL}")
    _ensure_ollama_running()
    from langchain_ollama import ChatOllama
    llm = ChatOllama(model=OLLAMA_MODEL, temperature=0, base_url="http://localhost:11434")
    print("✅ Ollama ready!")
    return llm

# Global chroma client — shared so Streamlit uploads persist in the same collection
_chroma_client = None
_collection = None

def setup_kb():
    global _chroma_client, _collection
    embedder = SentenceTransformer("all-MiniLM-L6-v2")

    if _chroma_client is None:
        _chroma_client = chromadb.Client()
    if _collection is None:
        _collection = _chroma_client.get_or_create_collection(name="legal_docs")

    # Pre-loaded sample legal knowledge base (25 chunks)
    documents = [
        {"id": "doc_001", "topic": "Contract Formation", "text": "A valid contract requires four essential elements: offer, acceptance, consideration, and mutual assent (also called 'meeting of the minds'). An offer is a proposal made by one party (offeror) to another (offeree) to enter into a legally binding agreement. Acceptance must be unconditional and mirror the terms of the offer exactly — any variation constitutes a counter-offer, not acceptance. Consideration is something of legal value exchanged by both parties. Without consideration, a promise is generally unenforceable as a gift."},
        {"id": "doc_002", "topic": "Contract Breach and Remedies", "text": "A breach of contract occurs when a party fails to perform their contractual obligations without a legally recognized excuse. Breaches can be material (significant, allowing the non-breaching party to terminate and sue) or minor (partial, allowing a damages claim but not termination). Remedies include: (1) Compensatory damages — to put the claimant in the position they would have been in had the contract been performed; (2) Expectation damages — loss of the benefit of the bargain; (3) Consequential damages — foreseeable losses arising from the breach; (4) Specific performance — a court order to fulfill the contract, typically for unique goods or real property; (5) Rescission — cancellation of the contract."},
        {"id": "doc_003", "topic": "Tort Law — Negligence", "text": "To establish negligence, a claimant must prove four elements: (1) Duty of care — the defendant owed a legal duty to the claimant; (2) Breach — the defendant breached that duty by falling below the standard of a reasonable person; (3) Causation — the breach caused the claimant's harm (both factual causation using the 'but-for' test, and legal/proximate causation); (4) Damages — the claimant suffered actual, quantifiable harm. Contributory negligence by the claimant may reduce or bar recovery depending on the jurisdiction's comparative fault rules."},
        {"id": "doc_004", "topic": "Tort Law — Liability Types", "text": "Strict liability imposes liability without fault for abnormally dangerous activities or defective products, regardless of the care taken. Vicarious liability holds an employer responsible for torts committed by employees within the scope of their employment. Product liability can arise under negligence, strict liability, or breach of warranty theories when a defective product causes harm. Defamation (libel in written form, slander if spoken) requires a false statement of fact, publication to a third party, and damages to reputation."},
        {"id": "doc_005", "topic": "Criminal Law — Elements of a Crime", "text": "Most crimes require two elements: actus reus (the guilty act — a physical act, omission where there is a duty to act, or a state of affairs) and mens rea (the guilty mind — the required mental state). Common mens rea levels include: intention (purposely bringing about a result), recklessness (conscious disregard of a substantial and unjustifiable risk), and negligence (failure to be aware of a risk that a reasonable person would have recognized). Strict liability offences require only the actus reus with no mens rea needed."},
        {"id": "doc_006", "topic": "Criminal Procedure — Arrest to Trial", "text": "The criminal justice process typically follows: (1) Investigation and arrest; (2) Booking and initial appearance before a magistrate; (3) Bail determination; (4) Preliminary hearing or grand jury indictment; (5) Arraignment — defendant enters a plea; (6) Discovery — exchange of evidence between prosecution and defense; (7) Pre-trial motions (e.g., motion to suppress illegally obtained evidence); (8) Trial — jury selection, opening statements, presentation of evidence, closing arguments, jury deliberation, verdict; (9) Sentencing if convicted; (10) Appeal."},
        {"id": "doc_007", "topic": "Evidence — Admissibility Rules", "text": "For evidence to be admissible in court it must be relevant (tending to make a fact of consequence more or less probable), not subject to an exclusionary rule, and competent. Key exclusionary rules include: hearsay (an out-of-court statement offered for the truth of the matter asserted) is generally inadmissible unless a recognized exception applies such as dying declarations, business records, or excited utterances. The best evidence rule requires original documents when proving document contents. Character evidence is generally inadmissible to prove conduct on a particular occasion."},
        {"id": "doc_008", "topic": "Civil Procedure — Jurisdiction", "text": "A court must have both subject matter jurisdiction (authority over the type of case) and personal jurisdiction (authority over the parties) to hear a case. Federal subject matter jurisdiction arises from federal question jurisdiction (cases arising under federal law, treaties, or the constitution) or diversity jurisdiction (parties from different states with amount in controversy exceeding $75,000). Personal jurisdiction requires either the defendant's physical presence in the state, domicile, consent, or sufficient minimum contacts with the forum state to satisfy due process."},
        {"id": "doc_009", "topic": "Civil Procedure — Pleadings and Discovery", "text": "Civil litigation begins with a complaint (plaintiff's statement of claim) filed in the appropriate court. The defendant must respond with an answer (admitting or denying allegations) or a motion to dismiss. Discovery allows parties to obtain evidence from each other through: interrogatories (written questions), depositions (oral testimony under oath), requests for production of documents, and requests for admission. The Federal Rules of Civil Procedure require initial disclosures of witnesses and documents regardless of a formal request."},
        {"id": "doc_010", "topic": "Constitutional Rights — Fourth Amendment", "text": "The Fourth Amendment protects against unreasonable searches and seizures by government actors. A search or seizure is 'reasonable' if conducted pursuant to a valid warrant supported by probable cause and particularly describing the place to be searched and items to be seized. Warrantless searches are permissible under recognized exceptions including: consent, exigent circumstances, search incident to lawful arrest, plain view, automobile exception, and stop-and-frisk (Terry stops) based on reasonable articulable suspicion."},
        {"id": "doc_011", "topic": "Constitutional Rights — Fifth and Sixth Amendments", "text": "The Fifth Amendment protects against: (1) double jeopardy (being tried twice for the same offence); (2) self-incrimination (the right to remain silent, codified in Miranda warnings); (3) deprivation of life, liberty, or property without due process of law; and (4) taking of private property for public use without just compensation. The Sixth Amendment guarantees: the right to a speedy and public trial by an impartial jury, the right to be informed of charges, the right to confront witnesses, and the right to counsel. The right to counsel attaches at the initiation of formal adversarial proceedings."},
        {"id": "doc_012", "topic": "Contract Law — Defences", "text": "Several defences may excuse non-performance of a contract: (1) Misrepresentation — a false statement of fact that induces entry into the contract; (2) Duress — entering a contract under improper threat or coercion; (3) Undue influence — one party takes unfair advantage of a position of trust; (4) Illegality — contracts for an illegal purpose are void; (5) Frustration of purpose — a supervening event makes performance radically different from what was contemplated; (6) Mistake — where both parties share a fundamental mistake of fact (common mistake) the contract may be void."},
        {"id": "doc_013", "topic": "Intellectual Property — Copyright", "text": "Copyright protects original works of authorship fixed in a tangible medium of expression, including literary, musical, dramatic, pictorial, sculptural, and audiovisual works and software. Protection arises automatically upon creation — registration is not required for protection but is necessary to sue for statutory damages and attorneys' fees. Copyright lasts for the life of the author plus 70 years (for works created after 1978). Fair use is a defence permitting limited use of copyrighted material for purposes such as criticism, comment, news reporting, teaching, scholarship, and research."},
        {"id": "doc_014", "topic": "Intellectual Property — Patents and Trademarks", "text": "A utility patent protects new, useful, and non-obvious inventions or discoveries for 20 years from the filing date. To obtain patent protection, the invention must be novel (not previously disclosed), non-obvious to a person of ordinary skill in the field, and have utility. A trademark is any word, name, symbol, or device used in commerce to identify and distinguish goods or services. Trademark rights arise from use in commerce and can last indefinitely if continually used and renewed. Unlike patents, trademarks protect brand identity, not the underlying invention."},
        {"id": "doc_015", "topic": "Employment Law — Wrongful Termination", "text": "In at-will employment jurisdictions, an employer may terminate an employee for any reason or no reason, unless the termination violates: (1) an employment contract or collective bargaining agreement; (2) anti-discrimination statutes (Title VII, ADA, ADEA) — termination cannot be based on race, color, religion, sex, national origin, disability, or age; (3) whistleblower protections; (4) the implied covenant of good faith and fair dealing; or (5) public policy exceptions. Wrongful termination claimants typically seek reinstatement, back pay, front pay, compensatory damages, and attorneys' fees."},
        {"id": "doc_016", "topic": "Property Law — Real Property Transfer", "text": "Transfer of real property typically requires: (1) a written contract of sale (statute of frauds requires land contracts to be in writing); (2) due diligence period — title search to verify clear title, survey, and property inspection; (3) a deed conveying title — warranty deed (grantor warrants title), quitclaim deed (no warranty), or special warranty deed; (4) closing — signing of documents, payment of purchase price, recording of deed in the county recorder's office. Recording gives constructive notice to subsequent purchasers. Bona fide purchasers for value without notice of prior claims are generally protected against unrecorded interests."},
        {"id": "doc_017", "topic": "Family Law — Divorce Grounds and Property Division", "text": "No-fault divorce is available in all US states and allows dissolution of marriage based on irreconcilable differences or irretrievable breakdown without proving spousal wrongdoing. Equitable distribution states divide marital property (acquired during the marriage) fairly but not necessarily equally, considering factors such as length of marriage, each spouse's contribution, economic circumstances, and child custody arrangements. Community property states (including California, Texas, and Arizona) split marital assets 50/50. Separate property (owned before marriage or received as a gift or inheritance during marriage) is generally not subject to division."},
        {"id": "doc_018", "topic": "Corporate Law — Business Entities", "text": "Common business entity types: (1) Sole proprietorship — no legal distinction between owner and business, unlimited personal liability; (2) Partnership — general partners share profits and liability; limited partners have liability limited to their investment; (3) Limited Liability Company (LLC) — members enjoy limited liability with pass-through taxation; (4) Corporation — separate legal entity owned by shareholders, provides the strongest liability protection, subject to double taxation (corporate tax + dividend tax) unless S-Corp election; (5) S-Corporation — pass-through taxation, limited to 100 US shareholders. Formation requires filing articles of incorporation or organization with the state."},
        {"id": "doc_019", "topic": "Legal Research and Citation", "text": "Legal citation follows the Bluebook (for law reviews and courts) or ALWD Guide to Legal Citation. Case citations include: party names, volume number, reporter abbreviation, first page, pinpoint page, and court and year in parentheses. Example: Brown v. Board of Education, 347 U.S. 483, 495 (1954). Statutes are cited to the official code: 42 U.S.C. § 1983 (2018). Secondary sources such as law review articles, treatises, and Restatements are persuasive but not binding authority. Primary binding authority includes constitutions, statutes, regulations, and case law from the controlling jurisdiction."},
        {"id": "doc_020", "topic": "Litigation — Pre-Trial Motions", "text": "Common pre-trial motions in civil litigation: (1) Motion to dismiss — argues the complaint fails to state a claim upon which relief can be granted; (2) Motion for summary judgment — argues there is no genuine dispute of material fact and the moving party is entitled to judgment as a matter of law; (3) Motion to suppress — in criminal cases, seeks to exclude evidence obtained in violation of constitutional rights; (4) Motion in limine — seeks to admit or exclude specific evidence at trial; (5) Motion for change of venue — seeks to move the trial to a different location due to pretrial publicity or convenience of witnesses."},
        {"id": "doc_021", "topic": "Appeals — Standards of Review", "text": "Appellate courts apply different standards of review depending on the type of decision being reviewed: (1) De novo — questions of law are reviewed without deference to the lower court; (2) Clearly erroneous — factual findings of a trial court are upheld unless clearly wrong; (3) Abuse of discretion — discretionary decisions (such as evidentiary rulings) are upheld unless the court abused its discretion; (4) Substantial evidence — agency factual findings are upheld if supported by substantial evidence in the record. Appeals courts do not hear new evidence or retry facts — they review the record from the lower court."},
        {"id": "doc_022", "topic": "Alternative Dispute Resolution", "text": "Alternatives to litigation include: (1) Negotiation — direct discussion between parties to reach a settlement; (2) Mediation — a neutral third party (mediator) facilitates negotiation but has no power to impose a decision; (3) Arbitration — a neutral arbitrator hears evidence and issues a binding award; (4) Mini-trial — a structured settlement negotiation with senior executives and a neutral advisor; (5) Early Neutral Evaluation — a neutral expert evaluates the merits of the case. Arbitration clauses in commercial contracts frequently require disputes to be resolved by arbitration rather than litigation, which is generally enforceable under the Federal Arbitration Act."},
        {"id": "doc_023", "topic": "Legal Document Types", "text": "Common legal documents include: (1) Affidavit — a written sworn statement of fact; (2) Deposition transcript — verbatim record of sworn oral testimony taken outside of court; (3) Memorandum of Law — legal brief analyzing law as applied to facts, submitted to a court; (4) Demand letter — formal notice of a legal claim prior to filing suit; (5) Non-Disclosure Agreement (NDA) — contract requiring parties to keep confidential information secret; (6) Power of Attorney — document authorizing an agent to act on behalf of a principal; (7) Promissory Note — written promise to pay a specific sum; (8) Settlement Agreement — contract resolving a dispute without trial."},
        {"id": "doc_024", "topic": "Statute of Limitations", "text": "A statute of limitations is a law setting the maximum time period after an event within which legal proceedings may be initiated. After the period expires, the claim is time-barred. Common limitations periods: contract claims — 3 to 6 years depending on the state and whether written or oral; personal injury tort claims — 2 to 3 years; medical malpractice — 2 to 3 years; fraud — 3 to 6 years from discovery; federal civil rights claims under 42 U.S.C. § 1983 — borrowed from state personal injury law. The limitations period typically begins to run when the cause of action accrues, which may be the date of the injury or, under the discovery rule, when the plaintiff knew or reasonably should have known of the injury."},
        {"id": "doc_025", "topic": "Professional Responsibility — Attorney Ethics", "text": "Attorneys are bound by the Model Rules of Professional Conduct (adopted with variations by most states). Key duties include: (1) Competence — providing legal services with the legal knowledge, skill, thoroughness, and preparation reasonably necessary; (2) Confidentiality — not revealing information relating to representation of a client without consent, with narrow exceptions for preventing certain crimes; (3) Loyalty — avoiding conflicts of interest without informed written consent; (4) Communication — keeping clients reasonably informed about their matter; (5) Candor to the tribunal — not knowingly making false statements of law or fact to a court; (6) Prohibition on dishonesty — no fraud, deceit, or misrepresentation."},
    ]

    if _collection.count() == 0:
        _collection.add(
            documents=[d["text"] for d in documents],
            metadatas=[{"topic": d["topic"]} for d in documents],
            ids=[d["id"] for d in documents]
        )
        print(f"✅ Loaded {len(documents)} legal knowledge base documents.")
    return embedder, _collection


def add_document_to_kb(embedder, text: str, doc_id: str, topic: str):
    """Dynamically add an uploaded PDF's text to the knowledge base."""
    global _collection
    if _collection is None:
        return
    chunks = _chunk_text(text, chunk_size=400, overlap=50)
    for i, chunk in enumerate(chunks):
        chunk_id = f"{doc_id}_chunk_{i}"
        try:
            _collection.add(
                documents=[chunk],
                metadatas=[{"topic": topic, "source": doc_id}],
                ids=[chunk_id]
            )
        except Exception:
            pass
    print(f"✅ Added {len(chunks)} chunks from '{topic}' to KB.")


def _chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start += chunk_size - overlap
    return chunks


class LegalState(TypedDict):
    question: str
    messages: List[BaseMessage]
    route: str
    retrieved: str
    sources: List[str]
    tool_result: str
    answer: str
    faithfulness: float
    eval_retries: int
    user_name: str


def create_graph(llm, embedder, collection):

    # NODE 1: Memory
    def memory_node(state: LegalState):
        messages = state.get("messages", [])
        question = state.get("question", "")
        user_name = state.get("user_name", "")
        q_lower = question.lower()
        if "my name is " in q_lower:
            parts = q_lower.split("my name is ")
            if len(parts) > 1:
                name_words = parts[1].strip().split()
                if name_words:
                    user_name = name_words[0].capitalize()
        messages.append(HumanMessage(content=question))
        if len(messages) > 6:
            messages = messages[-6:]
        return {"messages": messages, "user_name": user_name, "route": "", "eval_retries": 0}

    # NODE 2: Router
    def router_node(state: LegalState):
        q = state["question"].lower().strip()

        # Keyword-based pre-routing
        greetings = {"hi", "hello", "hey", "thanks", "thank you", "bye", "goodbye"}
        if any(w in q.split() for w in greetings) and len(q.split()) < 6:
            return {"route": "skip"}
        if any(w in q for w in ["what time", "what date", "today", "current date", "deadline"]):
            return {"route": "tool"}

        prompt = f"""You are a legal assistant routing system.
Classify this question into EXACTLY ONE of these routes:
- retrieve: legal questions about cases, contracts, laws, procedures, rights, evidence, torts, crimes
- skip: greetings, thank-you, off-topic non-legal chatter
- tool: asking for today's date, current time, or deadline calculations

Question: {state['question']}

Reply with ONE word only (retrieve, skip, or tool):"""
        try:
            response = llm.invoke(prompt).content.strip().lower()
            first_word = response.split()[0] if response.split() else "retrieve"
            if first_word in ("retrieve", "skip", "tool"):
                return {"route": first_word}
        except Exception:
            pass
        return {"route": "retrieve"}

    # NODE 3: Retrieval
    def retrieval_node(state: LegalState):
        q = state["question"]
        q_emb = embedder.encode(q).tolist()
        results = collection.query(query_embeddings=[q_emb], n_results=5)
        retrieved_text = ""
        sources = []
        if results and results.get("documents") and results["documents"][0]:
            for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                topic = meta.get("topic", "Unknown")
                source = meta.get("source", "Built-in KB")
                retrieved_text += f"[{topic}]\n{doc}\n\n"
                if topic not in sources:
                    sources.append(topic)
        return {"retrieved": retrieved_text.strip(), "sources": sources}

    # NODE 4: Skip
    def skip_node(state: LegalState):
        return {"retrieved": "", "sources": []}

    # NODE 5: Tool (Date / Deadline)
    def tool_node(state: LegalState):
        try:
            now = datetime.datetime.now()
            res = (f"Current date and time: {now.strftime('%A, %B %d, %Y at %I:%M %p')}. "
                   f"Day of week: {now.strftime('%A')}. "
                   f"This information can be used for calculating legal deadlines and statute of limitations periods.")
        except Exception as e:
            res = f"Error fetching date/time: {str(e)}"
        return {"tool_result": res, "eval_retries": 0}

    # NODE 6: Answer
    def answer_node(state: LegalState):
        q = state["question"]
        ret = state.get("retrieved", "")
        tool_res = state.get("tool_result", "")
        msgs = state.get("messages", [])
        u_name = state.get("user_name", "")
        greeting = f"Hi {u_name}! " if u_name else ""

        context_parts = []
        if ret.strip():
            context_parts.append(f"LEGAL REFERENCE MATERIAL:\n{ret}")
        if tool_res.strip():
            context_parts.append(f"SYSTEM INFORMATION:\n{tool_res}")
        context_block = "\n\n".join(context_parts) if context_parts else "No specific legal material found."

        history_lines = []
        for m in msgs[:-1]:
            role = "User" if isinstance(m, HumanMessage) else "Assistant"
            history_lines.append(f"{role}: {m.content}")
        history_block = "\n".join(history_lines)

        user_msg = f"""You are a knowledgeable legal research assistant helping paralegals and junior lawyers. Answer the question {f'(addressing {u_name})' if u_name else ''} using ONLY the legal reference material provided below. Be precise, cite the relevant legal doctrine or rule, and use clear legal terminology. If the answer is not in the material, say so clearly and recommend consulting a senior attorney or primary sources.

DISCLAIMER: This assistant provides legal research support only and does not constitute legal advice.

{context_block}
"""
        if history_block:
            user_msg += f"\nConversation history:\n{history_block}\n"

        user_msg += f"\nQuestion: {q}\n\nAnswer:"

        ans = llm.invoke(user_msg).content.strip()
        for prefix in ["Answer:", "Assistant:", "Response:"]:
            if ans.startswith(prefix):
                ans = ans[len(prefix):].strip()

        return {"answer": greeting + ans}

    # NODE 7: Eval
    def eval_node(state: LegalState):
        ret = state.get("retrieved", "")
        if not ret.strip():
            return {"faithfulness": 1.0}
        ans = state["answer"]
        prompt = f"""Rate how faithfully this legal answer uses only the provided context.
Respond with ONE number between 0.0 and 1.0.
Context: {ret[:800]}
Answer: {ans[:400]}
Score:"""
        try:
            score_str = llm.invoke(prompt).content.strip()
            match = re.search(r"0\.\d+|1\.0|0|1", score_str)
            score = float(match.group()) if match else 0.5
        except Exception:
            score = 0.5
        retries = state.get("eval_retries", 0) + 1
        return {"faithfulness": score, "eval_retries": retries}

    # NODE 8: Save
    def save_node(state: LegalState):
        msgs = state.get("messages", [])
        if state.get("answer"):
            msgs.append(AIMessage(content=state["answer"]))
        return {"messages": msgs}

    # Conditional Edges
    def route_decision(state: LegalState):
        return state.get("route", "retrieve")

    def eval_decision(state: LegalState):
        score = state.get("faithfulness", 1.0)
        retries = state.get("eval_retries", 0)
        if score < 0.7 and retries < 2:
            return "answer"
        return "save"

    # Build Graph
    g = StateGraph(LegalState)
    g.add_node("memory", memory_node)
    g.add_node("router", router_node)
    g.add_node("retrieve", retrieval_node)
    g.add_node("skip", skip_node)
    g.add_node("tool", tool_node)
    g.add_node("answer", answer_node)
    g.add_node("eval", eval_node)
    g.add_node("save", save_node)

    g.set_entry_point("memory")
    g.add_edge("memory", "router")
    g.add_conditional_edges("router", route_decision, {
        "retrieve": "retrieve",
        "skip": "skip",
        "tool": "tool"
    })
    g.add_edge("retrieve", "answer")
    g.add_edge("skip", "answer")
    g.add_edge("tool", "answer")
    g.add_edge("answer", "eval")
    g.add_conditional_edges("eval", eval_decision, {
        "answer": "answer",
        "save": "save"
    })
    g.add_edge("save", END)

    checkpointer = MemorySaver()
    return g.compile(checkpointer=checkpointer)
