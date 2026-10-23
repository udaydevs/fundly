import { useRef, useState } from "react";
import Button from "./Button.jsx";
import Panel from "./Panel.jsx";

export default function ImportPanel({ onImport }) {
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  async function submit(e) {
    e.preventDefault();
    if (!file) return;
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      setResult(await onImport(file));
      setFile(null);
      if (inputRef.current) inputRef.current.value = "";
    } catch (err) {
      const missing = err.body?.missing_columns;
      setError(missing?.length ? `${err.message}. Nothing was imported.` : err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Panel title="Import a bank statement" titleId="import-title">
      <p className="mb-3.5 max-w-prose text-muted">
        CSV with the columns date, description, amount, type and reference. Credits are matched to line items; debits
        are set aside.
      </p>
      <form onSubmit={submit} className="flex flex-wrap items-center gap-3">
        <input
          ref={inputRef}
          type="file"
          accept=".csv,text/csv"
          aria-label="Bank statement CSV file"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="min-w-0 flex-1 basis-60 rounded-md border border-dashed border-slate-400 bg-white p-2 text-sm file:mr-3 file:rounded file:border-0 file:bg-quiet-wash file:px-3 file:py-1 file:font-medium"
        />
        <Button variant="primary" type="submit" disabled={!file || busy}>
          {busy ? "Importing…" : "Import statement"}
        </Button>
      </form>

      {error && (
        <p role="alert" className="mt-2.5 rounded-md border border-red-200 bg-danger-wash px-3 py-2 text-sm text-danger">
          {error}
        </p>
      )}
      {result && <ImportResult result={result} />}
    </Panel>
  );
}

function IssueTable({ caption, columns, rows }) {
  return (
    <table className="w-full border-collapse text-sm">
      <caption className="pb-1.5 text-left font-semibold">{caption}</caption>
      <thead>
        <tr>
          {columns.map((c) => (
            <th key={c} scope="col" className="border-t border-line py-1.5 pr-3 text-left font-medium text-muted first:w-px first:whitespace-nowrap">
              {c}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map(([key, a, b]) => (
          <tr key={key}>
            <td className="w-px whitespace-nowrap border-t border-line py-1.5 pr-3 align-top">{a}</td>
            <td className="border-t border-line py-1.5 pr-3 align-top">{b}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function ImportResult({ result }) {
  const { imported, duplicates, errors, duplicate_details: dupes = [], breakdown = {} } = result;
  return (
    <div role="status" className="mt-4 grid gap-3 border-t border-line pt-3.5">
      <p className="max-w-prose">
        <strong>{imported}</strong> {imported === 1 ? "row" : "rows"} imported
        {imported > 0 && (
          <span className="text-muted">
            {" "}
            ({breakdown.suggested || 0} suggested, {breakdown.needs_review || 0} need review, {breakdown.ignored || 0}{" "}
            ignored)
          </span>
        )}
        . <strong>{duplicates}</strong> {duplicates === 1 ? "duplicate" : "duplicates"} skipped,{" "}
        <strong>{errors.length}</strong> {errors.length === 1 ? "row" : "rows"} with errors.
      </p>
      {errors.length > 0 && (
        <IssueTable
          caption="Rows that were skipped"
          columns={["Line", "Problem"]}
          rows={errors.map((e) => [`e-${e.line}`, e.line, e.message])}
        />
      )}
      {dupes.length > 0 && (
        <IssueTable
          caption="Duplicate bank references"
          columns={["Line", "Bank reference"]}
          rows={dupes.map((d) => [`d-${d.line}`, d.line, d.reference])}
        />
      )}
    </div>
  );
}
