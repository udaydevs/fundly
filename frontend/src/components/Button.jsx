const VARIANTS = {
  default: "border-slate-300 bg-white hover:bg-slate-100",
  primary: "border-brand bg-brand text-white hover:bg-brand-dark",
  quiet: "border-transparent bg-transparent px-2 text-muted hover:bg-quiet-wash hover:text-ink",
};

export default function Button({ variant = "default", className = "", type = "button", ...props }) {
  return (
    <button
      type={type}
      className={`rounded-md border px-3.5 py-1.5 font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${VARIANTS[variant]} ${className}`}
      {...props}
    />
  );
}
