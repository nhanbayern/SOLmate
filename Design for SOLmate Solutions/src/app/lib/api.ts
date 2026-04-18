// ─── SOLmate API Client ─────────────────────────────────────────────────────
// Mirrors exactly: http://localhost:8080/swagger/doc.json
// Base URL: http://localhost:8080

const BASE = "http://localhost:8080";

// ─── Auth Token helpers ──────────────────────────────────────────────────────
export function getToken(): string | null {
  const path = window.location.pathname;
  // If we are in the banker portal, only use bankerToken
  if (path.startsWith("/banker")) {
    return localStorage.getItem("bankerToken");
  }
  // If we are in the customer portal, only use customerToken
  if (path.startsWith("/customer")) {
    return localStorage.getItem("customerToken");
  }
  // Fallback
  return (
    localStorage.getItem("bankerToken") ||
    localStorage.getItem("customerToken") ||
    null
  );
}

/**
 * Parse the actual login response shape:
 * { access_token: string, data: { role, user_id, customer_id, merchant_id, ... } }
 */
export function extractLoginResult(res: any): { token: string; role: string; data: any } {
  console.log("[api] Raw login response:", JSON.stringify(res, null, 2));
  // Real backend returns access_token at top level
  const token: string =
    res?.access_token ||
    res?.data?.token ||
    res?.token ||
    "";
  const role: string =
    res?.data?.role ||
    res?.role ||
    "MERCHANT";
  console.log(`[api] Extracted token=${token ? token.slice(0, 20) + "..." : "(none)"} role=${role}`);
  return { token, role, data: res?.data ?? {} };
}

export function saveToken(token: string, role: string, profileData?: any) {
  if (role === "BANKER" || role === "ADMIN") {
    localStorage.setItem("bankerToken", token);
    localStorage.setItem("bankerLoggedIn", token);
  } else {
    localStorage.setItem("customerToken", token);
    localStorage.setItem("customerLoggedIn", token);
    // Cache profile data to avoid extra GET /api/auth/me call
    if (profileData) {
      localStorage.setItem("customerProfile", JSON.stringify(profileData));
    }
  }
  console.log(`[api] Token saved for role=${role}`);
}

export function clearTokens() {
  localStorage.removeItem("bankerToken");
  localStorage.removeItem("bankerLoggedIn");
  localStorage.removeItem("customerToken");
  localStorage.removeItem("customerLoggedIn");
  localStorage.removeItem("customerProfile");
  localStorage.removeItem("customerId");
}

// ─── Core fetch wrapper ──────────────────────────────────────────────────────
export async function apiFetch(
  path: string,
  options: RequestInit = {}
): Promise<any> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = token;

  const res = await fetch(`${BASE}${path}`, { ...options, headers });

  if (res.status === 401) {
    clearTokens();
    window.location.href = "/";
    return null;
  }

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new Error(data?.error || data?.message || `HTTP ${res.status}`);
  }

  return data;
}

// ─── AUTH ────────────────────────────────────────────────────────────────────
// POST /api/auth/login
export async function authLogin(username: string, password: string) {
  return apiFetch("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

// GET /api/auth/me
export async function authMe() {
  return apiFetch("/api/auth/me");
}

// ─── STATS ───────────────────────────────────────────────────────────────────
// GET /api/stats
export async function getStats() {
  return apiFetch("/api/stats");
}

// ─── LOANS (Banker) ──────────────────────────────────────────────────────────
// GET /api/loans?limit=&offset=
export async function getLoans(limit = 50, offset = 0) {
  return apiFetch(`/api/loans?limit=${limit}&offset=${offset}`);
}

// GET /api/loans/:id
export async function getLoanDetail(id: string) {
  return apiFetch(`/api/loans/${id}`);
}

// POST /api/loans/evaluate
export async function evaluateLoan(payload: {
  loan_id: string;
  merchant_id: string;
  customer_id: string;
}) {
  return apiFetch("/api/loans/evaluate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// POST /api/loans/:id/decision
export async function decideLoan(id: string, status: "APPROVED" | "REJECTED") {
  return apiFetch(`/api/loans/${id}/decision`, {
    method: "POST",
    body: JSON.stringify({ status }),
  });
}

// ─── MERCHANTS ───────────────────────────────────────────────────────────────
// GET /api/merchants
export async function getMerchants() {
  return apiFetch("/api/merchants");
}

// GET /api/merchants/:id
export async function getMerchantDetail(id: string) {
  return apiFetch(`/api/merchants/${id}`);
}

// ─── TRANSACTIONS ────────────────────────────────────────────────────────────
// GET /api/transactions?merchant_id=&customer_id=
export async function getTransactions(merchant_id: string, customer_id: string) {
  return apiFetch(
    `/api/transactions?merchant_id=${encodeURIComponent(merchant_id)}&customer_id=${encodeURIComponent(customer_id)}`
  );
}

// ─── CUSTOMER LOANS ──────────────────────────────────────────────────────────
// GET /api/customer/loans  (customer_id inferred from JWT)
export async function getCustomerLoans() {
  return apiFetch("/api/customer/loans");
}

// POST /api/customer/loans
export async function createCustomerLoan(payload: {
  merchant_id: string;
  loan_type: string;
  requested_amount: number;
}) {
  return apiFetch("/api/customer/loans", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// ─── SSE Stream (no auth wrapper needed — uses EventSource) ──────────────────
// GET /api/loans/stream?merchant_id=
export function createLoanStream(merchant_id: string, onMessage: (data: any) => void): EventSource {
  const token = getToken();
  // EventSource doesn't support custom headers, pass token as query param workaround
  const url = `${BASE}/api/loans/stream?merchant_id=${encodeURIComponent(merchant_id)}&token=${encodeURIComponent(token || "")}`;
  const es = new EventSource(url);
  es.onmessage = (event) => {
    try {
      onMessage(JSON.parse(event.data));
    } catch {
      onMessage(event.data);
    }
  };
  return es;
}

// ─── Convenience object ───────────────────────────────────────────────────────
export const API = {
  auth: { login: authLogin, me: authMe },
  stats: { get: getStats },
  loans: {
    list: getLoans,
    detail: getLoanDetail,
    evaluate: evaluateLoan,
    decide: decideLoan,
    stream: createLoanStream,
  },
  merchants: { list: getMerchants, detail: getMerchantDetail },
  transactions: { list: getTransactions },
  customer: {
    loans: { list: getCustomerLoans, create: createCustomerLoan },
  },
};

// ─── Report text parser ───────────────────────────────────────────────────────
export function parseReportText(raw: string | null | undefined) {
  if (!raw) return { report_text_user: "", report_text_bank: "" };

  const bankMarker = "Báo cáo Ngân hàng:";
  const userMarker = "Báo cáo Khách hàng:";
  const bankIdx = raw.indexOf(bankMarker);

  if (bankIdx === -1) {
    const userText = raw.replace(userMarker, "").trim();
    return { report_text_user: userText, report_text_bank: "" };
  }

  const userText = raw.substring(0, bankIdx).replace(userMarker, "").trim();
  const bankText = raw.substring(bankIdx).replace(bankMarker, "").trim();
  return { report_text_user: userText, report_text_bank: bankText };
}
