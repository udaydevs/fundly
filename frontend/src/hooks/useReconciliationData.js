import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { createApi } from "../api/header.js";

const PAGE_SIZE = 25;

export function useReconciliationData(org) {
  const api = useMemo(() => createApi(org), [org]);
  const [filter, setFilter] = useState("");
  const [page, setPage] = useState(1);
  const [txPage, setTxPage] = useState({ results: [], count: 0, status_counts: {} });
  const [lineItems, setLineItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [busyId, setBusyId] = useState(null);
  const latest = useRef(0);

  const load = useCallback(async () => {
    const ticket = ++latest.current;
    try {
      const [tx, items] = await Promise.all([
        api.transactions({ status: filter, page, pageSize: PAGE_SIZE }),
        api.lineItems(),
      ]);
      if (ticket !== latest.current) return; // a newer request superseded this one
      setTxPage(tx);
      setLineItems(items);
      setError(null);
    } catch (e) {
      if (ticket !== latest.current) return;
      if (e.status === 404 && page > 1) setPage(1); // the page disappeared after items were actioned
      else setError(e.message);
    } finally {
      if (ticket === latest.current) setLoading(false);
    }
  }, [api, filter, page]);

  useEffect(() => {
    setLoading(true);
    load();
  }, [load]);

  // Run an action, then reload both lists so balances and statuses are never stale.
  const act = useCallback(
    async (id, fn) => {
      setBusyId(id);
      setError(null);
      try {
        await fn();
      } catch (e) {
        setError(e.message);
      } finally {
        setBusyId(null);
        await load();
      }
    },
    [load]
  );

  return {
    transactions: txPage.results,
    counts: txPage.status_counts || {},
    lineItems,
    filter,
    setFilter: (f) => {
      setFilter(f);
      setPage(1);
    },
    page,
    setPage,
    pageCount: Math.max(1, Math.ceil(txPage.count / PAGE_SIZE)),
    loading,
    error,
    clearError: () => setError(null),
    busyId,
    reload: load,
    approve: (matchId, txId) => act(`tx-${txId}`, () => api.approve(matchId)),
    reject: (matchId, txId) => act(`tx-${txId}`, () => api.reject(matchId)),
    ignore: (txId) => act(`tx-${txId}`, () => api.ignore(txId)),
    importCsv: (file) => api.importCsv(file),
  };
}
