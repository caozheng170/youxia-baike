import React, { useRef, useState, useCallback, useEffect } from 'react';
import ClickOverlay from './ClickOverlay';
import './PageView.css';

export default function PageView({
  page,
  isGenerating,
  isPreview,
  exploreIntent,
  onExplore,
  onCancel,
}) {
  const imgRef = useRef(null);
  const [clickPoint, setClickPoint] = useState(null);

  // Keep the click marker visible while generating; clear it once done.
  useEffect(() => {
    if (!isGenerating) setClickPoint(null);
  }, [isGenerating]);

  const handleClick = useCallback(
    (e) => {
      if (isGenerating || !page?.id) return;

      const rect = imgRef.current?.getBoundingClientRect();
      if (!rect) return;

      const x = (e.clientX - rect.left) / rect.width;
      const y = (e.clientY - rect.top) / rect.height;

      // Mark the click point (stays during loading, shows the intent card).
      // fx/fy are normalized (0-1) so the overlay can flip the card near edges.
      setClickPoint({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
        fx: x,
        fy: y,
      });

      // Trigger exploration
      onExplore(page.id, x, y);
    },
    [isGenerating, page?.id, onExplore]
  );

  if (!page) {
    if (isGenerating) {
      return (
        <div className="page-view empty">
          <div className="creating-content">
            <div className="creating-icon" aria-hidden="true">
              <span className="creating-ring" />
              <span className="creating-ring creating-ring--delay" />
              <span className="creating-core">✦</span>
            </div>
            <h2 className="creating-title">Creating image…</h2>
            <p className="creating-subtitle">Waiting for the AI to paint your page</p>
            <div className="creating-progress" role="progressbar" aria-label="Generating image">
              <div className="creating-progress-bar" />
            </div>
            <p className="creating-hint">This may take up to a minute</p>
          </div>
        </div>
      );
    }

    return (
      <div className="page-view empty">
        <div className="empty-content">
          <div className="empty-icon">📖</div>
          <h2>What would you like to explore?</h2>
          <p>Type a topic above to generate a visual page, then click anywhere to dive deeper.</p>
          <div className="empty-suggestions">
            {['Solar System', 'Coffee Making', 'Quantum Physics', 'Human Brain', 'Jazz Music'].map((s) => (
              <span key={s} className="suggestion-chip" onClick={() => {
                const input = document.querySelector('.search-input');
                if (input) {
                  const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                  nativeInputValueSetter.call(input, s);
                  input.dispatchEvent(new Event('input', { bubbles: true }));
                  input.focus();
                }
              }}>
                {s}
              </span>
            ))}
          </div>
        </div>
      </div>
    );
  }

  const isUrl = page.image && !page.image.startsWith('data:');

  return (
    <div className="page-view">
      <div className="page-image-container">
        <img
          ref={imgRef}
          src={page.image}
          alt={page.query}
          className={`page-image ${isPreview ? 'preview' : 'full'} ${isGenerating ? 'generating' : ''}`}
          onClick={handleClick}
          draggable={false}
        />
        <ClickOverlay
          clickPoint={clickPoint}
          isGenerating={isGenerating}
          intent={exploreIntent}
          onCancel={onCancel}
        />
      </div>
      {page.query && (
        <div className="page-query-label">
          {page.query}
        </div>
      )}
    </div>
  );
}
