import { STATUS_LABELS } from "../utils/format.js";

// Full class names so Tailwind can see them at build time.
const STYLES = {
  suggested: "bg-info-wash text-info",
  proposed: "bg-info-wash text-info",
  needs_review: "bg-warn-wash text-warn",
  partially_funded: "bg-warn-wash text-warn",
  reconciled: "bg-brand-wash text-brand",
  approved: "bg-brand-wash text-brand",
  funded: "bg-brand-wash text-brand",
  rejected: "bg-danger-wash text-danger",
};

export default function StatusBadge({ status, className = "" }) {
  return (
    <span
      className={`inline-block whitespace-nowrap rounded-full px-2.5 py-0.5 text-[12.5px] font-semibold ${
        STYLES[status] || "bg-quiet-wash text-muted"
      } ${className}`}
    >
      {STATUS_LABELS[status] || status}
    </span>
  );
}
