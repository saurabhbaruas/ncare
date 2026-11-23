import { useRef, useState } from "react";
import api, { errorText } from "../api";

const MAX_MB = 10; // same limit as the backend (MAX_UPLOAD_MB)

export default function UploadBox({ onUploaded }) {
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState(null); // { type: "success" | "error", text, errors }

  // Quick checks in the browser so the user gets instant feedback (the server checks again)
  function chooseFile(selected) {
    setMessage(null);
    setProgress(0);
    if (!selected) return;

    if (!/\.(xlsx|xls)$/i.test(selected.name)) {
      setFile(null);
      return setMessage({ type: "error", text: "Please choose an Excel file (.xlsx or .xls)." });
    }
    if (selected.size > MAX_MB * 1024 * 1024) {
      setFile(null);
      return setMessage({ type: "error", text: `File is too big. The limit is ${MAX_MB} MB.` });
    }
    setFile(selected);
  }

  function onDrop(e) {
    e.preventDefault(); // stops the browser from opening the file
    setDragging(false);
    chooseFile(e.dataTransfer.files[0]);
  }

  // A normal <a href> link can't send the API key header, so we download the file with axios instead
  async function downloadTemplate() {
    try {
      const res = await api.get("/patients/template", { responseType: "blob" });
      const url = URL.createObjectURL(res.data);
      const link = document.createElement("a");
      link.href = url;
      link.download = "patient_template.xlsx";
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setMessage({ type: "error", text: errorText(err) });
    }
  }

  async function upload() {
    const form = new FormData();
    form.append("file", file);
    setUploading(true);
    setMessage(null);

    try {
      const res = await api.post("/patients/upload", form, {
        // axios reports how much of the file has been sent
        onUploadProgress: (e) => setProgress(Math.round((e.loaded * 100) / (e.total || file.size))),
      });
      setMessage({ type: "success", text: res.data.message });
      setFile(null);
      onUploaded(); // tells the table to reload
    } catch (err) {
      setMessage({ type: "error", text: errorText(err), errors: err.response?.data?.detail?.errors });
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = ""; // allows choosing the same file again after fixing it
    }
  }

  return (
    <section id="upload" className="card">
      <div className="card-title-row">
        <h2>Upload patients</h2>
        <button type="button" className="link link-button" onClick={downloadTemplate}>Download template</button>
      </div>
      <p className="muted">
        Excel file with exactly these columns: Patient ID, First Name, Last Name, Date of Birth, Gender.
      </p>

      {/* the dashed drop area; clicking it opens the normal file picker */}
      <div
        className={`dropzone ${dragging ? "dragging" : ""}`}
        onClick={() => inputRef.current.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        <input ref={inputRef} type="file" accept=".xlsx,.xls" hidden
               onChange={(e) => chooseFile(e.target.files[0])} />
        {file ? (
          <p><strong>{file.name}</strong> <span className="muted">({(file.size / 1024).toFixed(1)} KB)</span></p>
        ) : (
          <p>Drag &amp; drop your Excel file here, or <span className="link">browse</span></p>
        )}
      </div>

      {uploading && (
        <div className="progress"><div className="progress-bar" style={{ width: `${progress}%` }} /></div>
      )}

      {message && (
        <div className={`alert alert-${message.type}`}>
          <p>{message.text}</p>
          {message.errors && (
            <ul>{message.errors.map((e) => <li key={e}>{e}</li>)}</ul>
          )}
        </div>
      )}

      <button className="btn" disabled={!file || uploading} onClick={upload}>
        {uploading ? `Uploading... ${progress}%` : "Upload file"}
      </button>
    </section>
  );
}
