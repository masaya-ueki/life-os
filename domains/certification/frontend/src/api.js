// FastAPI バックエンドへの薄いクライアント。トークンはメモリ保持（MVP）。
let token = null;

export function setToken(t) {
  token = t;
}

async function request(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`/api${path}`, { ...options, headers });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      detail = (await res.json()).detail || detail;
    } catch (_) {}
    throw new Error(detail);
  }
  return res.status === 204 ? null : res.json();
}

export const api = {
  login: (email, password) =>
    request("/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  certifications: () => request("/certifications"),
  genres: (certId) => request(`/certifications/${certId}/genres`),
  startQuiz: (body) =>
    request("/quiz/start", { method: "POST", body: JSON.stringify(body) }),
  grade: (body) =>
    request("/quiz/grade", { method: "POST", body: JSON.stringify(body) }),
  bank: (certId, params) => {
    const q = new URLSearchParams();
    for (const [k, v] of Object.entries(params || {})) {
      if (v !== null && v !== undefined && v !== "") q.set(k, v);
    }
    const qs = q.toString();
    return request(`/certifications/${certId}/bank${qs ? `?${qs}` : ""}`);
  },
};
