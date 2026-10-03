const configuredUrl = import.meta.env.VITE_API_BASE_URL?.trim();
export const apiBase = (
  configuredUrl || (import.meta.env.DEV ? "http://127.0.0.1:8000" : "")
).replace(/\/+$/, "");

export async function askQuestion(question, signal) {
  if (!apiBase)
    throw new Error(
      "The demo backend is not connected yet. Please try again once the service is configured.",
    );
  const response = await fetch(`${apiBase}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
    signal,
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = typeof data?.detail === "string" ? data.detail : null;
    throw new Error(
      detail ||
        (response.status === 429
          ? "The demo is receiving too many requests. Please wait a minute and try again."
          : `The research service could not complete the request (${response.status}). Please try again.`),
    );
  }
  if (
    !data ||
    typeof data.answer !== "string" ||
    typeof data.question !== "string" ||
    !Array.isArray(data.sources) ||
    !data.sources.every(
      (source) =>
        source &&
        typeof source === "object" &&
        ["company", "regulator", "vertical", "document", "excerpt"].every(
          (key) => source[key] == null || typeof source[key] === "string",
        ),
    )
  )
    throw new Error(
      "The research service returned an unexpected response. Please try again.",
    );
  return data;
}

export async function checkHealth(signal) {
  if (!apiBase) return "unconfigured";
  const response = await fetch(`${apiBase}/health`, { signal });
  if (!response.ok) return "offline";
  const data = await response.json();
  return data.chain_initialized
    ? "ready"
    : data.status === "degraded"
      ? "offline"
      : "warming";
}
