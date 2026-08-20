import React, { useEffect, useMemo, useState } from "react";

type DocumentItem = {
  id: number;
  title: string;
  original_filename: string;
  safe_filename: string;
  mime_type?: string | null;
  file_size_bytes: number;
  status: string;
  raw_text: string;
  cleaned_text?: string | null;
  language_code: string;
  created_at: string;
  updated_at: string;
};

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function App() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [transcript, setTranscript] = useState<DocumentItem | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(false);

  const loadDocuments = async () => {
    setIsLoadingDocuments(true);
    try {
      const response = await fetch(`${API_BASE}/api/v1/documents`);
      if (!response.ok) {
        throw new Error("Unable to load documents");
      }
      const data = (await response.json()) as DocumentItem[];
      setDocuments(data);
      if (data[0]) {
        setTranscript(data[0]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load documents");
    } finally {
      setIsLoadingDocuments(false);
    }
  };

  useEffect(() => {
    void loadDocuments();
  }, []);

  const selectedSummary = useMemo(() => {
    if (!selectedFile) return "No file selected";
    return `${selectedFile.name} (${(selectedFile.size / 1024 / 1024).toFixed(2)} MB)`;
  }, [selectedFile]);

  const handleUpload = async () => {
    if (!selectedFile) {
      setError("Please choose an MP3 or audio file first.");
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const response = await fetch(`${API_BASE}/api/v1/documents`, {
        method: "POST",
        body: formData,
      });

      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail ?? "Upload failed");
      }

      setTranscript(payload as DocumentItem);
      await loadDocuments();
      setSelectedFile(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong while uploading");
    } finally {
      setIsUploading(false);
    }
  };

  const handleDownload = async (documentId: number, format: "txt" | "docx" | "pdf") => {
    const response = await fetch(`${API_BASE}/api/v1/documents/${documentId}/download?format=${format}`);
    if (!response.ok) {
      setError("Download failed");
      return;
    }

    const payload = await response.json();
    const blob = new Blob([payload.content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = payload.filename;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  return (
    <main className="app-shell">
      <div className="app-frame">
        <header className="topbar">
          <div>
            <p className="eyebrow">Local-first transcription</p>
            <h1>MP3 into a Book</h1>
          </div>
          <span className="pill">{documents.length} documents</span>
        </header>

        <section className="upload-panel">
          <div className="upload-zone">
            <label className="file-picker">
              <input
                type="file"
                accept=".mp3,.wav,.m4a,.ogg,.webm,.mp4"
                onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
              />
              <span>Choose audio file</span>
            </label>
            <p>{selectedSummary}</p>
          </div>

          <button className="primary-button" disabled={!selectedFile || isUploading} onClick={handleUpload}>
            {isUploading ? "Uploading…" : "Transcribe"}
          </button>
        </section>

        {error && <div className="error-box">{error}</div>}

        <div className="content-grid">
          <aside className="sidebar">
            <h2>Recent documents</h2>
            {isLoadingDocuments ? (
              <p>Loading…</p>
            ) : documents.length === 0 ? (
              <p>No documents yet.</p>
            ) : (
              <ul className="document-list">
                {documents.map((document) => (
                  <li
                    key={document.id}
                    className={transcript?.id === document.id ? "active" : ""}
                    onClick={() => setTranscript(document)}
                  >
                    <strong>{document.title}</strong>
                    <span>{document.original_filename}</span>
                    <small>{document.status}</small>
                  </li>
                ))}
              </ul>
            )}
          </aside>

          <section className="transcript-panel">
            {transcript ? (
              <>
                <div className="transcript-header">
                  <div>
                    <p className="eyebrow">Current transcript</p>
                    <h2>{transcript.title}</h2>
                  </div>
                  <div className="download-actions">
                    <button onClick={() => handleDownload(transcript.id, "txt")}>TXT</button>
                    <button onClick={() => handleDownload(transcript.id, "docx")}>DOCX</button>
                    <button onClick={() => handleDownload(transcript.id, "pdf")}>PDF</button>
                  </div>
                </div>

                <dl className="meta-list">
                  <div>
                    <dt>Original file</dt>
                    <dd>{transcript.original_filename}</dd>
                  </div>
                  <div>
                    <dt>Status</dt>
                    <dd>{transcript.status}</dd>
                  </div>
                  <div>
                    <dt>Language</dt>
                    <dd>{transcript.language_code}</dd>
                  </div>
                </dl>

                <textarea readOnly value={transcript.cleaned_text ?? transcript.raw_text} />
              </>
            ) : (
              <div className="empty-state">
                <h2>No transcript yet</h2>
                <p>Upload an MP3 to see the text here.</p>
              </div>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}

export default App;
