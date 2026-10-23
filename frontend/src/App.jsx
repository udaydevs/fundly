import { useState } from "react";
import ReconciliationPage from "./pages/Main.jsx";
import OrgSwitcher from "./components/OrgSwitcher.jsx";

export const ORGANIZATIONS = [
  { slug: "northwind", name: "Northwind Ventures" },
  { slug: "bluebird", name: "Bluebird Capital" },
];

export default function App() {
  const [org, setOrg] = useState(() => localStorage.getItem("wireline.org") || ORGANIZATIONS[0].slug);

  function changeOrg(slug) {
    localStorage.setItem("wireline.org", slug);
    setOrg(slug);
  }

  const current = ORGANIZATIONS.find((o) => o.slug === org) || ORGANIZATIONS[0];

  return (
    <div className="min-h-screen">
      <header className="flex flex-wrap items-center justify-between gap-4 bg-[#F9F6F1] px-4 py-3.5 text-white sm:px-10">
        <div className="flex flex-wrap items-baseline gap-x-1">
          <span className="text-[32px] font-extrabold text-[#258B8F] tracking-tight">fundly</span>
          <span className="text-sm font-medium text-black">Bank Reconciliation</span>
        </div>
        <OrgSwitcher organizations={ORGANIZATIONS} value={current.slug} onChange={changeOrg} />
      </header>
      <ReconciliationPage key={current.slug} org={current.slug} orgName={current.name} />
    </div>
  );
}