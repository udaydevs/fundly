import Button from "./Button.jsx";
import Panel from "./Panel.jsx";
import TransactionRow from "./TransactionRow.jsx";

const FILTERS = [
  { value: "", label: "All" },
  { value: "suggested", label: "Suggested" },
  { value: "needs_review", label: "Needs review" },
  { value: "reconciled", label: "Reconciled" },
  { value: "ignored", label: "Ignored" },
];

export default function TransactionList({ data }) {
  const {
    transactions = [],
    counts = {},
    filter = "",
    setFilter = () => {},
    page = 1,
    setPage = () => {},
    pageCount = 1,
    loading = false,
    busyId = null
  } = data;
const all = Object.values(counts).reduce(
    (sum, count) => sum + count,
    0
  );
  return (
    <Panel title="Transactions" titleId="tx-title">
      <div role="group" aria-label="Filter by status" className="mb-3.5 mt-2.5 flex flex-wrap gap-2">
        {FILTERS.map((f) => {
          const on = filter === f.value;
          return (
            <button
              key={f.value}
              aria-pressed={on}
              onClick={() => setFilter(f.value)}
              className={`rounded-full border px-3 py-1 text-sm ${
                on ? "border-ink bg-ink text-white" : "border-line bg-white hover:bg-slate-100"
              }`}
            >
              {f.label} <span className={on ? "ml-1 text-slate-300" : "ml-1 text-muted"}>{f.value ? counts[f.value] ?? 0 : all}</span>
            </button>
          );
        })}
      </div>

      {loading && transactions.length === 0 ? (
        <p className="py-5 text-muted">Loading transactions…</p>
      ) : transactions.length === 0 ? (
        <p className="py-5 text-muted">
          {all === 0
            ? "No transactions yet. Import a bank statement to see suggested matches."
            : "No transactions with this status."}
        </p>
      ) : (
        <ul className="grid gap-3">
          {transactions.map((tx) => (
            <TransactionRow
              key={tx.id}
              tx={tx}
              busy={busyId === `tx-${tx.id}`}
              onApprove={data.approve}
              onReject={data.reject}
              onIgnore={data.ignore}
            />
          ))}
        </ul>
      )}

      {pageCount > 1 && (
        <nav aria-label="Pagination" className="mt-4 flex items-center justify-center gap-3.5">
          <Button disabled={page <= 1} onClick={() => setPage(page - 1)}>
            Previous
          </Button>
          <span>
            Page {page} of {pageCount}
          </span>
          <Button disabled={page >= pageCount} onClick={() => setPage(page + 1)}>
            Next
          </Button>
        </nav>
      )}
    </Panel>
  );
}
