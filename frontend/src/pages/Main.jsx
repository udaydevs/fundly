import Button from "../components/Button.jsx";
import ImportPanel from "../components/ImportPanel.jsx";
import LineItemsPanel from "../components/LineItemsPanel.jsx";
import TransactionList from "../components/TransactionList.jsx";
import { useReconciliationData } from "../hooks/useReconciliationData.js";

export default function ReconciliationPage({ org, orgName }) {
  const data = useReconciliationData(org);

  async function handleImport(file) {
    const summary = await data.importCsv(file);
    await data.reload();
    return summary;
  }

  return (
    <main className="mx-auto max-w-7xl px-4 pb-14 pt-6 sm:px-10">
      <h1 className="mb-4 text-[26px] font-bold tracking-tight">{orgName}</h1>

      {data.error && (
        <div
          role="alert"
          className="mb-4 flex items-center justify-between gap-3 rounded-md border border-red-200 bg-danger-wash px-3 py-2 text-sm text-danger"
        >
          <span>{data.error}</span>
          <Button variant="quiet" onClick={data.clearError}>
            Dismiss
          </Button>
        </div>
      )}

      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1.7fr)_minmax(300px,1fr)]">
        <div className="grid gap-5">
          <ImportPanel onImport={handleImport} />
          <TransactionList data={data} />
        </div>
        <aside className="order-first lg:sticky lg:top-4 lg:order-none">
          <LineItemsPanel lineItems={data.lineItems} />
        </aside>
      </div>
    </main>
  );
}