/** API client for Flipbook backend. */

// In dev, leave VITE_API_BASE empty so requests hit `/api` and go through the Vite proxy.
// In production (e.g. Netlify), set VITE_API_BASE to the backend origin,
// e.g. https://your-backend.hf.space — requests then go to that origin's /api.
export const API_BASE = `${import.meta.env.VITE_API_BASE || ''}/api`;

/**
 * Generate a new page from a query. Returns an event source for SSE.
 * @param {string} query - Search query
 * @param {{ onPreview: Function, onFull: Function, onError: Function, onIntent: Function, provider: string }} handlers
 * @returns {EventSource}
 */
export function generatePage(query, { onPreview, onFull, onError, onIntent, provider }) {
  return streamSSE(
    `${API_BASE}/generate`,
    { query, provider },
    { onPreview, onFull, onError, onIntent }
  );
}

/**
 * Explore by clicking on a page. Returns an event source for SSE.
 * @param {string} pageId - Parent page ID
 * @param {number} clickX - Normalized X (0-1)
 * @param {number} clickY - Normalized Y (0-1)
 * @param {{ onPreview: Function, onFull: Function, onError: Function, onIntent: Function, provider: string }} handlers
 * @returns {EventSource}
 */
export function explorePage(pageId, clickX, clickY, { onPreview, onFull, onError, onIntent, provider }) {
  return streamSSE(
    `${API_BASE}/explore`,
    { page_id: pageId, click_x: clickX, click_y: clickY, provider },
    { onPreview, onFull, onError, onIntent }
  );
}

/**
 * Get the active model provider and available providers.
 */
export async function getConfig() {
  const resp = await fetch(`${API_BASE}/config`);
  if (!resp.ok) throw new Error('Failed to load config');
  return resp.json();
}

/**
 * Switch the active model provider (local / cloud / mock).
 */
export async function setProvider(provider) {
  const resp = await fetch(`${API_BASE}/config`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ provider }),
  });
  if (!resp.ok) throw new Error('Failed to switch provider');
  return resp.json();
}

/**
 * Get page metadata.
 */
export async function getPage(pageId) {
  const resp = await fetch(`${API_BASE}/page/${pageId}`);
  if (!resp.ok) throw new Error(`Page not found: ${pageId}`);
  return resp.json();
}

/**
 * Get share data for a page.
 */
export async function sharePage(pageId) {
  const resp = await fetch(`${API_BASE}/share/${pageId}`);
  if (!resp.ok) throw new Error(`Share failed: ${pageId}`);
  return resp.json();
}

/**
 * Download image as PNG.
 */
export async function downloadImage(imageDataUrl, filename = 'flipbook-page.png') {
  const link = document.createElement('a');
  link.href = imageDataUrl;
  link.download = filename;
  link.click();
}

// ── Internal ──────────────────────────────────────────────

function streamSSE(url, body, { onPreview, onFull, onError, onIntent }) {
  // We'll use fetch + ReadableStream for POST-based SSE
  // (EventSource only supports GET)
  const controller = new AbortController();

  (async () => {
    try {
      const resp = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: controller.signal,
      });

      if (!resp.ok) {
        onError?.(new Error(`HTTP ${resp.status}`));
        return;
      }

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // keep incomplete line

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === 'intent') onIntent?.(data);
              else if (data.type === 'preview') onPreview?.(data);
              else if (data.type === 'full') onFull?.(data);
            } catch (e) {
              // Ignore malformed JSON
            }
          }
        }
      }
    } catch (e) {
      if (e.name !== 'AbortError') {
        onError?.(e);
      }
    }
  })();

  return {
    close: () => controller.abort(),
  };
}
