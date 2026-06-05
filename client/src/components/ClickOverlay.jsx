import React from 'react';
import './ClickOverlay.css';

export default function ClickOverlay({ clickPoint, isGenerating, intent, onCancel }) {
  if (!clickPoint && !isGenerating) return null;

  return (
    <div className="click-overlay">
      {clickPoint && (
        <div
          className="water-ripple"
          style={{ left: clickPoint.x, top: clickPoint.y }}
        >
          <span className="water-ripple__drop" />
          <span className="water-ripple__wave water-ripple__wave--1" />
          <span className="water-ripple__wave water-ripple__wave--2" />
          <span className="water-ripple__wave water-ripple__wave--3" />
        </div>
      )}

      {isGenerating && clickPoint && (
        <div
          className="intent-card"
          style={{
            left: clickPoint.x,
            top: clickPoint.y,
            transform: `translate(${
              (clickPoint.fx ?? 0.5) > 0.6 ? 'calc(-100% - 18px)' : '18px'
            }, ${
              (clickPoint.fy ?? 0.5) < 0.2
                ? '-8%'
                : (clickPoint.fy ?? 0.5) > 0.8
                ? '-92%'
                : '-50%'
            })`,
          }}
        >
          <span className="intent-spinner" />
          <span className="intent-text">
            {intent
              ? <>正在了解「<strong>{intent}</strong>」…</>
              : '正在识别点击位置…'}
          </span>
          {onCancel && (
            <button
              type="button"
              className="intent-close"
              onClick={onCancel}
              title="取消"
              aria-label="取消"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          )}
        </div>
      )}

      {isGenerating && !clickPoint && (
        <div className="generating-indicator">
          <div className="generating-dots"><span /><span /><span /></div>
          <span className="generating-text">生成中…</span>
        </div>
      )}
    </div>
  );
}
