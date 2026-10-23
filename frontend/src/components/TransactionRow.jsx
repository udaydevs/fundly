import Button from "./Button.jsx";
import StatusBadge from "./StatusBadge.jsx";
import { money, shortDate } from "../utils/format.js";

const EDGE = {
  suggested: "border-l-info",
  needs_review: "border-l-warn-edge",
  reconciled: "border-l-brand",
  ignored: "border-l-quiet-edge bg-slate-50",
};

export default function TransactionRow({ tx, busy, onApprove, onReject, onIgnore }) {
  const isCredit = tx.type === "credit";
  const open = tx.status === "suggested" || tx.status === "needs_review";
  const visibleMatches = tx.matches.filter((m) => m.status !== "rejected" || tx.status === "needs_review");

  return (
    <li
      aria-busy={busy}
      className={`rounded-md border border-l-4 border-line bg-white px-4 py-3.5 ${EDGE[tx.status] || ""} ${
        busy ? "opacity-65" : ""
      }`}
    >
      <div className="flex flex-col gap-2 sm:flex-row sm:justify-between sm:gap-4">
        <div className="min-w-0">
          <p className="break-words font-semibold">{tx.description}</p>
          <p className="text-[13px] text-muted">
            {shortDate(tx.date)}, bank reference {tx.bank_reference}
          </p>
        </div>
        <div className="flex shrink-0 items-center justify-between gap-1.5 sm:flex-col sm:items-end">
          <p className={`text-[17px] font-bold ${isCredit ? "text-brand" : "text-danger"}`}>{money(tx.amount)}</p>
          <StatusBadge status={tx.status} />
        </div>
      </div>

      {tx.reason && <p className="mt-2 text-sm text-muted">{tx.reason}</p>}

      {visibleMatches.length > 0 && (
        <ul className="mt-2.5 grid gap-2">
          {visibleMatches.map((m) => {
            const li = m.line_item;
            const tooBig = Number(tx.amount) > Number(li.amount_remaining);
            return (
              <li
                key={m.id}
                className={`flex flex-col gap-3 rounded-md border border-line bg-paper px-3 py-2.5 sm:flex-row sm:items-center sm:justify-between ${
                  m.status === "rejected" ? "opacity-60" : ""
                }`}
              >
                <div className="min-w-0">
                  <p>
                    <strong>{li.reference}</strong> {li.investor_name}
                    <span className="text-muted">, call {li.capital_call.number}</span>
                    {m.status !== "proposed" && <StatusBadge status={m.status} className="ml-2" />}
                  </p>
                  <p className="mt-0.5 text-sm">{m.reason}</p>
                  <p className="mt-0.5 text-[13px] text-muted">
                    Remaining {money(li.amount_remaining)} of {money(li.amount_called)}
                  </p>
                  {m.status === "proposed" && tooBig && (
                    <p className="mt-2.5 rounded-md border border-amber-200 bg-warn-wash px-3 py-2 text-sm text-warn">
                      This payment is now larger than the remaining amount.
                    </p>
                  )}
                </div>
                {m.status === "proposed" && open && (
                  <div className="flex shrink-0 gap-2">
                    <Button
                      variant="primary"
                      disabled={busy || tooBig}
                      onClick={() => onApprove(m.id, tx.id)}
                      aria-label={`Approve match to ${li.reference}`}
                    >
                      Approve
                    </Button>
                    <Button disabled={busy} onClick={() => onReject(m.id, tx.id)} aria-label={`Reject match to ${li.reference}`}>
                      Reject
                    </Button>
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}

      {open && (
        <div className="mt-2 flex justify-end">
          <Button variant="quiet" disabled={busy} onClick={() => onIgnore(tx.id)}>
            Ignore transaction
          </Button>
        </div>
      )}
    </li>
  );
}
