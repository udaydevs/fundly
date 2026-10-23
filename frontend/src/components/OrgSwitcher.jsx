export default function OrgSwitcher({ organizations, value, onChange }) {
  return (
    <div className="relative w-fit">
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 -960 960 960"
    className="pointer-events-none absolute left-2.5 top-1/2 z-10 h-4.25 w-4.25 -translate-y-1/2 text-slate-700"
    fill="currentColor"
  >
    <path d="M80-120v-720h400v160h400v560H80Zm80-80h240v-80H160v80Zm0-160h240v-80H160v80Zm0-160h240v-80H160v80Zm0-160h240v-80H160v80Zm320 480h320v-400H480v400Zm80-240v-80h160v80H560Zm0 160v-80h160v80H560Z" />
  </svg>

  <select
    value={value}
    onChange={(e) => onChange(e.target.value)}
    className="h-8 min-w-70 cursor-pointer appearance-none rounded-lg border border-slate-200 bg-white pl-9 pr-8 text-[13px] font-medium text-slate-800 shadow-sm outline-none"
  >
    {organizations.map((o) => (
      <option key={o.slug} value={o.slug}>
        {o.name}
      </option>
    ))}
  </select>

  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    className="pointer-events-none absolute right-2 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500"
  >
    <path d="m6 9 6 6 6-6" />
  </svg>
</div>
  );
}
