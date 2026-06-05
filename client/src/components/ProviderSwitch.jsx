import React, { useEffect, useState } from 'react';
import { getConfig } from '../api/client';
import './ProviderSwitch.css';

const LABELS = {
  local: '本地',
  cloud: '线上API',
};

// Providers offered in the UI (mock is hidden from end users).
const VISIBLE = ['local', 'cloud'];

/**
 * Controlled model-source switch. The selection lives in the parent and is sent
 * with every generate/explore request, so concurrent users never affect each other.
 */
export default function ProviderSwitch({ value, onChange }) {
  const [providers, setProviders] = useState(VISIBLE);
  const [toast, setToast] = useState(null);

  // Load the provider list + server default once; seed the selection if empty.
  useEffect(() => {
    getConfig()
      .then((cfg) => {
        if (cfg.providers?.length) {
          setProviders(cfg.providers.filter((p) => VISIBLE.includes(p)));
        }
        if (!value && cfg.provider) onChange?.(cfg.provider);
      })
      .catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const showToast = (message, kind = 'success') => {
    setToast({ message, kind });
    window.clearTimeout(showToast._t);
    showToast._t = window.setTimeout(() => setToast(null), 2600);
  };

  const handleSelect = (provider) => {
    if (provider === value) return;
    onChange?.(provider);
    showToast(`已切换到「${LABELS[provider] || provider}」模型`, 'success');
  };

  return (
    <div className="provider-switch-wrap">
      <span className="provider-switch-label">模型来源</span>
      <div className="provider-switch" role="group" aria-label="模型来源">
        {providers.map((p) => (
          <button
            key={p}
            type="button"
            className={`provider-option ${value === p ? 'active' : ''}`}
            onClick={() => handleSelect(p)}
            aria-pressed={value === p}
            title={`切换到 ${LABELS[p] || p} 模型`}
          >
            {value === p && <span className="provider-dot" aria-hidden="true" />}
            {LABELS[p] || p}
          </button>
        ))}
      </div>

      {toast && (
        <div className={`provider-toast ${toast.kind}`} role="status">
          {toast.kind === 'success' ? '✓ ' : '⚠ '}
          {toast.message}
        </div>
      )}
    </div>
  );
}
