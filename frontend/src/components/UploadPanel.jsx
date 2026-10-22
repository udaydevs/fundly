import { useRef, useState } from "react";

export default function CsvUploader() {
  const [file, setFile] = useState(null);
  const [error, setError] = useState("");
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);

  const validateFile = (selectedFile) => {
    if (!selectedFile) return;

    const isCsv =
      selectedFile.name.toLowerCase().endsWith(".csv") &&
      (selectedFile.type === "text/csv" ||
        selectedFile.type === "application/vnd.ms-excel" ||
        selectedFile.type === "");

    if (!isCsv) {
      setError("Please select a valid CSV file");
      setFile(null);
      return;
    }

    setError("");
    setFile(selectedFile);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    validateFile(e.dataTransfer.files[0]);
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024)
      return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const removeFile = () => {
    setFile(null);
    setError("");
    if (inputRef.current) inputRef.current.value = "";
  };

  const handleUpload = () => {
    if (!file) return;
    console.log("Selected CSV:", file);
    alert(`Ready to upload: ${file.name}`);
  };

  return (
    <div className=" bg-slate-50 flex items-center justify-center p-4">
      <div className="w-full max-w-xl rounded-2xl border border-slate-200 bg-white p-6 sm:p-8 shadow-xl shadow-slate-200/50">
        <div className="mb-7 flex items-center gap-4">
        </div>

        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          className={`cursor-pointer rounded-xl border-2 border-dashed p-8 text-center transition sm:p-12 ${
            dragging
              ? "border-emerald-500 bg-emerald-50"
              : "border-slate-300 bg-slate-50 hover:border-emerald-400 hover:bg-emerald-50/50"
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".csv,text/csv"
            className="hidden"
            onChange={(e) => {
              validateFile(e.target.files?.[0]);
              e.target.value = "";
            }}
          />

          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 text-emerald-700">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              className="h-7 w-7"
            >
              <path d="M12 16V4m-5 5 5-5 5 5" />
              <path d="M20 16.5v3A1.5 1.5 0 0 1 18.5 21h-13A1.5 1.5 0 0 1 4 19.5v-3" />
            </svg>
          </div>

          <p className="text-base font-semibold text-slate-800">
            Drop your CSV file here
          </p>
          <p className="mt-2 text-sm text-slate-500">
            or{" "}
            <span className="font-semibold text-emerald-700 underline underline-offset-2">
              browse files
            </span>
          </p>
          <p className="mt-4 text-xs text-slate-400">
            CSV files only
          </p>
        </div>

        {error && (
          <div
            role="alert"
            className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
          >
            {error}
          </div>
        )}

        {file && (
          <div className="mt-5 flex items-center gap-3 rounded-xl border border-slate-200 bg-white p-4">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-emerald-50 text-xs font-bold text-emerald-700">
              CSV
            </div>

            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-slate-800">
                {file.name}
              </p>
              <p className="mt-1 text-xs text-slate-500">
                {formatSize(file.size)} · Ready to upload
              </p>
            </div>

            <button
              type="button"
              onClick={removeFile}
              aria-label="Remove selected file"
              className="rounded-lg p-2 text-slate-400 hover:bg-red-50 hover:text-red-600"
            >
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                className="h-5 w-5"
              >
                <path d="m18 6-12 12M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}

        <button
          type="button"
          disabled={!file}
          onClick={handleUpload}
          className="mt-6 w-full rounded-xl bg-emerald-600 px-5 py-3.5 text-sm font-semibold text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          Upload CSV
        </button>
      </div>
    </div>
  );
}
