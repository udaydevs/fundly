const moneyFmt = new Intl.NumberFormat("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export function money(value) {
  return moneyFmt.format(Number(value));
}

export function shortDate(iso) {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d)).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  });
}

export const STATUS_LABELS = {
  suggested: "Suggested",
  needs_review: "Needs review",
  reconciled: "Reconciled",
  ignored: "Ignored",
  proposed: "Proposed",
  approved: "Approved",
  rejected: "Rejected",
  open: "Open",
  partially_funded: "Partly funded",
  funded: "Funded",
};

export function fundedPercent(funded, called) {
  const c = Number(called);
  return c > 0 ? Math.min(100, (Number(funded) / c) * 100) : 0;
}
