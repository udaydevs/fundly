import Panel from "./Panel.jsx";
import StatusBadge from "./StatusBadge.jsx";
import { fundedPercent, money, shortDate } from "../utils/format.js";

function groupByCall(items) {
  const groups = new Map();
  for (const li of items) {
    const key = li.cap_call.id;
    if (!groups.has(key)) groups.set(key, { call: li.cap_call, items: [] });
    groups.get(key).items.push(li);
  }
  return [...groups.values()];
}

function Figure({ label, value }) {
  return (
    <div>
      <dt className="text-muted">{label}</dt>
      <dd className="text-sm font-semibold">{value}</dd>
    </div>
  );
}

export default function LineItemsPanel({ lineItems }) {
  const groups = groupByCall(lineItems);
  return (
    <Panel title="Capital call line items" titleId="li-title">
      {groups.length === 0 && <p className="py-5 text-muted">No capital calls for this organization.</p>}
      {groups.map(({ call, items }) => (
        <div key={call.id} className="mt-5 first:mt-3">
          <h3 className="flex flex-col font-semibold">
            Call {call.number}
            <span className="text-[13px] font-normal text-muted">
              sent {shortDate(call.call_date)}, due {shortDate(call.due_date)}
            </span>
          </h3>
          <ul className="mt-2">
            {items.map((li) => {
              const pct = fundedPercent(li.amount_funded, li.amount_called);
              return (
                <li key={li.id} className="border-t border-line py-3">
                  <div className="flex items-center justify-between gap-2.5">
                    <p>
                      <strong>{li.investor_name}</strong>
                      <span className="text-muted"> {li.reference}</span>
                    </p>
                    <StatusBadge status={li.status} />
                  </div>
                  <div
                    role="progressbar"
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-valuenow={Math.round(pct)}
                    aria-label={`${li.investor_name} funded`}
                    className="my-2 h-2.5 overflow-hidden rounded-sm bg-slate-200"
                  >
                    <span className="block h-full bg-brand transition-[width] duration-500 motion-reduce:transition-none" style={{ width: `${pct}%` }} />
                  </div>
                  <dl className="grid grid-cols-3 gap-2 text-[13px]">
                    <Figure label="Called" value={money(li.amount_called)} />
                    <Figure label="Funded" value={money(li.amount_funded)} />
                    <Figure label="Remaining" value={money(li.amount_remaining)} />
                  </dl>
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </Panel>
  );
}
