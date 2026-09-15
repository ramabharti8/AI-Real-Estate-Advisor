import { useEffect, useRef, useState } from "react";
import { api, type DocumentInfo } from "../api/client";

interface ChatEntry {
  role: "user" | "assistant";
  content: string;
  sources?: string[];
  sourceType?: "llm" | "template";
}

export default function DocumentsTab() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const [chat, setChat] = useState<ChatEntry[]>([]);
  const [asking, setAsking] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  function refreshDocs() {
    api.listDocuments().then((r) => setDocuments(r.documents)).catch(() => {});
  }

  useEffect(refreshDocs, []);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setUploadMsg(null);
    try {
      const res = await api.uploadDocument(file);
      setUploadMsg(`Indexed ${res.filename} (${res.chunk_count} chunks).`);
      refreshDocs();
    } catch (err) {
      setUploadMsg(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  }

  async function askQuestion(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    const q = question.trim();
    setChat((c) => [...c, { role: "user", content: q }]);
    setQuestion("");
    setAsking(true);
    try {
      const history = chat.map((c) => ({ role: c.role, content: c.content }));
      const res = await api.chatDocuments(q, history);
      setChat((c) => [
        ...c,
        { role: "assistant", content: res.answer, sources: res.sources, sourceType: res.source_type },
      ]);
    } catch (err) {
      setChat((c) => [
        ...c,
        { role: "assistant", content: `Error: ${err instanceof Error ? err.message : "request failed"}` },
      ]);
    } finally {
      setAsking(false);
    }
  }

  return (
    <div>
      <div className="section-label">Indexed documents</div>
      <div className="card">
        <div className="doc-list">
          {documents.length === 0 && <p className="caption">No documents indexed yet.</p>}
          {documents.map((d) => (
            <div className="doc-row" key={d.filename}>
              <span>{d.filename}</span>
              <span className="caption">
                {d.chunk_count} chunks &middot; {d.source_type}
              </span>
            </div>
          ))}
        </div>
        <div style={{ marginTop: 14 }}>
          <label className="btn-secondary" style={{ display: "inline-block", cursor: "pointer" }}>
            {uploading ? "Uploading..." : "Upload document (PDF or text)"}
            <input
              ref={fileInput}
              type="file"
              accept=".pdf,.txt,.md"
              onChange={handleUpload}
              style={{ display: "none" }}
              disabled={uploading}
            />
          </label>
          {uploadMsg && <p className="caption" style={{ marginTop: 8 }}>{uploadMsg}</p>}
        </div>
      </div>

      <div className="section-label" style={{ marginTop: 24 }}>
        Ask about your documents
      </div>
      <div className="card">
        <div className="chat-log">
          {chat.length === 0 && (
            <p className="caption">
              Ask e.g. &quot;What documents does a buyer need for a home loan?&quot; or &quot;What amenities are
              typical in a society brochure?&quot;
            </p>
          )}
          {chat.map((m, i) => (
            <div key={i} className={`chat-msg ${m.role}`}>
              <div>{m.content}</div>
              {m.role === "assistant" && (
                <div className="caption" style={{ marginTop: 6 }}>
                  <span className={`badge ${m.sourceType}`}>
                    {m.sourceType === "llm" ? "AI Generated" : "Retrieved Excerpt"}
                  </span>
                  {m.sources && m.sources.length > 0 && <span> &middot; sources: {m.sources.join(", ")}</span>}
                </div>
              )}
            </div>
          ))}
        </div>
        <form onSubmit={askQuestion} style={{ display: "flex", gap: 8, marginTop: 12 }}>
          <input
            style={{ flex: 1, padding: "8px 10px", border: "1px solid var(--line)", borderRadius: 6 }}
            placeholder="Ask a question about the indexed documents..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
          <button className="btn-primary" type="submit" disabled={asking}>
            {asking ? "Thinking..." : "Ask"}
          </button>
        </form>
      </div>
    </div>
  );
}
