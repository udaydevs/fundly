export class ApiError extends Error {
  constructor(status, message, body) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

function messageFrom(body, status) {
  if (body && typeof body === "object") {
    if (typeof body.detail === "string") return body.detail;
    const first = Object.values(body)[0];
    if (typeof first === "string") return first;
    if (Array.isArray(first) && first.length) return String(first[0]);
  }
  return `Request failed (${status})`;
}

async function request(org, path, { method = "GET", formData } = {}) {
  let res;
  try {
    res = await fetch(path, { method, headers: { "X-Organization": org }, body: formData });
  } catch {
    throw new ApiError(0, "Cannot reach the server. Check that the backend is running.");
  }
  let body = null;
  try {
    body = await res.json();
  } catch {
    /* empty or non-JSON body */
  }
  if (!res.ok) throw new ApiError(res.status, messageFrom(body, res.status), body);
  return body;
}

export function createApi(org) {
  return {
    transactions: ({ status, page = 1, pageSize = 25 } = {}) => {
      const q = new URLSearchParams({ page, page_size: pageSize });
      if (status) q.set("status", status);
      return request(org, `/api/transactions/`);
    },
    lineItems: () => request(org, "/api/line-items/"),
    importCsv: (file) => {
      const formData = new FormData();
      formData.append("file", file);
      return request(org, "/api/transactions/import/", { method: "POST", formData });
    },
    approve: (matchId) => request(org, `/api/matches/${matchId}/approve/`, { method: "POST" }),
    reject: (matchId) => request(org, `/api/matches/${matchId}/reject/`, { method: "POST" }),
    ignore: (transactionId) => request(org, `/api/transactions/${transactionId}/ignore/`, { method: "POST" }),
  };
}