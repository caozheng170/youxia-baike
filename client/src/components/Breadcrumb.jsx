import React from 'react';
import './Breadcrumb.css';

export default function Breadcrumb({ items, onNavigate }) {
  if (!items || items.length === 0) return null;

  return (
    <nav className="breadcrumb" aria-label="Page navigation">
      <button
        className="breadcrumb-item home"
        onClick={() => onNavigate(null)}
        title="Home"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
          <polyline points="9 22 9 12 15 12 15 22" />
        </svg>
      </button>
      {items.map((item, idx) => (
        <React.Fragment key={item.id}>
          <span className="breadcrumb-sep">›</span>
          <button
            className={`breadcrumb-item ${idx === items.length - 1 ? 'active' : ''}`}
            onClick={() => {
              if (idx < items.length - 1) {
                onNavigate(item.id);
              }
            }}
            disabled={idx === items.length - 1}
          >
            {item.query.length > 24 ? item.query.slice(0, 24) + '…' : item.query}
          </button>
        </React.Fragment>
      ))}
    </nav>
  );
}
