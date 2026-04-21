"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import {
  Scale,
  Send,
  RefreshCw,
  Bot,
  User,
  Upload,
  FileText,
  X,
  CheckCircle,
  AlertCircle,
  BookOpen,
  Gavel,
  FileSearch,
  Clock,
} from "lucide-react";

const API_BASE = "http://localhost:8001";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: string[];
  loading?: boolean;
}

interface UploadedDoc {
  label: string;
  wordCount: number;
  status: "success" | "error";
  error?: string;
}

const QUICK_QUESTIONS = [
  { label: "Negligence Elements", icon: Gavel, q: "What elements must a plaintiff prove to establish negligence?" },
  { label: "Contract Formation", icon: FileText, q: "What are the essential elements of a valid contract?" },
  { label: "Statute of Limitations", icon: Clock, q: "What is the statute of limitations for personal injury claims?" },
  { label: "Hearsay Rule", icon: BookOpen, q: "What is the hearsay rule and what are its main exceptions?" },
];

export default function LegalChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [threadId, setThreadId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [uploadedDocs, setUploadedDocs] = useState<UploadedDoc[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const container = scrollContainerRef.current;
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  }, [messages]);

  const sendMessage = useCallback(
    async (question: string) => {
      if (!question.trim() || isLoading) return;

      const userMsg: Message = { id: crypto.randomUUID(), role: "user", content: question.trim() };
      const loadingMsg: Message = { id: crypto.randomUUID(), role: "assistant", content: "", loading: true };

      setMessages((prev) => [...prev, userMsg, loadingMsg]);
      setInput("");
      setIsLoading(true);

      try {
        const res = await fetch(`${API_BASE}/api/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question: question.trim(), thread_id: threadId }),
        });
        if (!res.ok) throw new Error("API error");
        const data = await res.json();
        setThreadId(data.thread_id);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === loadingMsg.id
              ? { ...m, content: data.answer, sources: data.sources, loading: false }
              : m
          )
        );
      } catch {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === loadingMsg.id
              ? { ...m, content: "⚠️ Could not reach the API. Make sure `uvicorn api:app` is running on port 8001.", loading: false }
              : m
          )
        );
      } finally {
        setIsLoading(false);
      }
    },
    [threadId, isLoading]
  );

  const uploadFile = async (file: File) => {
    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    formData.append("label", file.name.replace(/\.[^.]+$/, ""));

    try {
      const res = await fetch(`${API_BASE}/api/upload`, { method: "POST", body: formData });
      const data = await res.json();
      if (data.success) {
        setUploadedDocs((prev) => [
          ...prev,
          { label: data.label, wordCount: data.word_count, status: "success" },
        ]);
      } else {
        setUploadedDocs((prev) => [
          ...prev,
          { label: file.name, wordCount: 0, status: "error", error: data.error },
        ]);
      }
    } catch {
      setUploadedDocs((prev) => [
        ...prev,
        { label: file.name, wordCount: 0, status: "error", error: "Upload failed" },
      ]);
    } finally {
      setIsUploading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadFile(file);
    e.target.value = "";
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file && (file.type === "application/pdf" || file.name.endsWith(".txt"))) {
      uploadFile(file);
    }
  };

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Sidebar */}
      <aside className="w-72 shrink-0 border-r border-border bg-card flex flex-col">
        {/* Brand */}
        <div className="p-4 border-b border-border">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center">
              <Scale className="h-4 w-4 text-primary" />
            </div>
            <div>
              <p className="font-semibold text-foreground text-sm">LexAI</p>
              <p className="text-xs text-muted-foreground">Legal Research Assistant</p>
            </div>
          </div>
        </div>

        {/* Upload */}
        <div className="p-4 flex-1 overflow-y-auto">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
            Upload Documents
          </p>
          <div
            className={`border-2 border-dashed rounded-xl p-4 text-center transition-colors cursor-pointer ${
              isDragging
                ? "border-primary bg-primary/5"
                : "border-border hover:border-primary/50 hover:bg-accent/50"
            }`}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.txt"
              className="hidden"
              onChange={handleFileChange}
            />
            <Upload className="h-5 w-5 text-muted-foreground mx-auto mb-2" />
            <p className="text-xs text-muted-foreground">
              {isUploading ? "Uploading..." : "Drop a PDF or TXT here"}
            </p>
            <p className="text-xs text-muted-foreground/60 mt-1">or click to browse</p>
          </div>

          {uploadedDocs.length > 0 && (
            <div className="mt-4 space-y-2">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Indexed Documents
              </p>
              {uploadedDocs.map((doc, i) => (
                <div
                  key={i}
                  className="flex items-start gap-2 p-2.5 rounded-lg bg-background border border-border text-xs"
                >
                  {doc.status === "success" ? (
                    <CheckCircle className="h-4 w-4 text-green-500 shrink-0 mt-0.5" />
                  ) : (
                    <AlertCircle className="h-4 w-4 text-destructive shrink-0 mt-0.5" />
                  )}
                  <div className="min-w-0">
                    <p className="font-medium text-foreground truncate">{doc.label}</p>
                    {doc.status === "success" ? (
                      <p className="text-muted-foreground">{doc.wordCount.toLocaleString()} words indexed</p>
                    ) : (
                      <p className="text-destructive">{doc.error}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          <Separator className="my-4" />

          {/* KB Topics */}
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
            Built-in Knowledge
          </p>
          {[
            "Contract Law", "Tort Law", "Criminal Procedure",
            "Evidence Rules", "Civil Procedure", "Constitutional Rights",
            "IP Law", "Employment Law", "Property Law", "Attorney Ethics",
          ].map((topic) => (
            <div key={topic} className="flex items-center gap-2 py-1 text-xs text-muted-foreground">
              <BookOpen className="h-3 w-3 shrink-0" />
              {topic}
            </div>
          ))}
        </div>

        {/* Disclaimer */}
        <div className="p-3 border-t border-border">
          <p className="text-xs text-muted-foreground/70 text-center">
            ⚠️ Research tool only — not legal advice
          </p>
        </div>
      </aside>

      {/* Main Chat */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Header */}
        <header className="shrink-0 border-b border-border bg-card/80 backdrop-blur-md px-6 py-3 flex items-center justify-between">
          <div>
            <h1 className="font-semibold text-foreground text-sm">Legal Research Chat</h1>
            <p className="text-xs text-muted-foreground flex items-center gap-1">
              <span className="h-1.5 w-1.5 rounded-full bg-green-500 inline-block" />
              Qwen2.5:3b • Ollama • Fully Local
            </p>
          </div>
          <div className="flex items-center gap-2">
            {uploadedDocs.filter((d) => d.status === "success").length > 0 && (
              <Badge variant="secondary" className="gap-1 text-xs">
                <FileSearch className="h-3 w-3" />
                {uploadedDocs.filter((d) => d.status === "success").length} doc
                {uploadedDocs.filter((d) => d.status === "success").length > 1 ? "s" : ""} indexed
              </Badge>
            )}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => { setMessages([]); setThreadId(null); }}
              className="h-8 w-8 text-muted-foreground hover:text-foreground"
              title="New conversation"
            >
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </header>

        {/* Messages */}
        <div ref={scrollContainerRef} className="flex-1 min-h-0 overflow-y-auto">
          <div className="max-w-3xl mx-auto px-6 py-6 space-y-4">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center py-16 gap-6 text-center">
                <div className="h-16 w-16 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center">
                  <Scale className="h-8 w-8 text-primary" />
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-foreground">Legal Research Ready</h2>
                  <p className="text-muted-foreground text-sm mt-1">
                    Ask a legal question or upload a case document to get started.
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-2 w-full max-w-xl">
                  {QUICK_QUESTIONS.map(({ label, icon: Icon, q }) => (
                    <button
                      key={label}
                      onClick={() => sendMessage(q)}
                      className="flex items-center gap-2 px-3 py-2.5 rounded-lg border border-border bg-card text-sm text-muted-foreground hover:text-foreground hover:bg-accent transition-colors text-left"
                    >
                      <Icon className="h-4 w-4 shrink-0 text-primary" />
                      {label}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg) => (
              <div key={msg.id} className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
                <Avatar className="h-8 w-8 shrink-0 mt-0.5">
                  <AvatarFallback
                    className={
                      msg.role === "user"
                        ? "bg-primary text-primary-foreground text-xs"
                        : "bg-muted text-muted-foreground text-xs"
                    }
                  >
                    {msg.role === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                  </AvatarFallback>
                </Avatar>

                <div className={`flex flex-col gap-1 max-w-[80%] ${msg.role === "user" ? "items-end" : ""}`}>
                  {msg.loading ? (
                    <div className="rounded-2xl rounded-tl-sm bg-card border border-border px-4 py-3 space-y-2">
                      <Skeleton className="h-3 w-48" />
                      <Skeleton className="h-3 w-64" />
                      <Skeleton className="h-3 w-36" />
                    </div>
                  ) : (
                    <div
                      className={`rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                        msg.role === "user"
                          ? "rounded-tr-sm bg-primary text-primary-foreground"
                          : "rounded-tl-sm bg-card border border-border text-foreground"
                      }`}
                    >
                      {msg.content}
                    </div>
                  )}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="flex flex-wrap gap-1 px-1">
                      {msg.sources.map((s) => (
                        <Badge key={s} variant="secondary" className="text-xs py-0">
                          📎 {s}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            <div ref={bottomRef} />
          </div>
        </div>

        {/* Input */}
        <div className="shrink-0 border-t border-border bg-card/80 backdrop-blur-md px-6 py-3">
          <form
            onSubmit={(e) => { e.preventDefault(); sendMessage(input); }}
            className="flex gap-2"
          >
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a legal research question..."
              disabled={isLoading}
              className="flex-1 bg-background"
            />
            <Button type="submit" disabled={isLoading || !input.trim()} size="icon">
              <Send className="h-4 w-4" />
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
