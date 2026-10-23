export default function Panel({ title, titleId, children, className = "" }) {
  return (
    <section aria-labelledby={titleId} className={`rounded-md border border-line bg-paper p-5 ${className}`}>
      <h2 id={titleId} className="mb-1.5 text-[17px] font-semibold">
        {title}
      </h2>
      {children}
    </section>
  );
}
