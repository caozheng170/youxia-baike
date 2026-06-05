import React, { useCallback } from 'react';
import { sharePage, downloadImage } from '../api/client';
import './ActionBar.css';

export default function ActionBar({ page, onRegenerate }) {
  const handleShare = useCallback(async () => {
    if (!page?.id) return;
    try {
      const data = await sharePage(page.id);
      const url = `${window.location.origin}${data.share_url}`;
      await navigator.clipboard.writeText(url);
      // Simple visual feedback
      const btn = document.querySelector('.action-btn.share');
      const orig = btn.textContent;
      btn.textContent = '✓ Copied!';
      setTimeout(() => { btn.textContent = orig; }, 1500);
    } catch (e) {
      console.error('Share failed:', e);
    }
  }, [page?.id]);

  const handleDownload = useCallback(() => {
    if (!page?.image) return;
    downloadImage(page.image, `flipbook-${page.id}.png`);
  }, [page]);

  const handleRegenerate = useCallback(() => {
    if (onRegenerate && page?.query) {
      onRegenerate(page.query);
    }
  }, [onRegenerate, page?.query]);

  if (!page) return null;

  return (
    <div className="action-bar">
      <button className="action-btn share" onClick={handleShare} title="Copy share link">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="18" cy="5" r="3" />
          <circle cx="6" cy="12" r="3" />
          <circle cx="18" cy="19" r="3" />
          <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" />
          <line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
        </svg>
        Share
      </button>
      <button className="action-btn download" onClick={handleDownload} title="Download image">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="7 10 12 15 17 10" />
          <line x1="12" y1="15" x2="12" y2="3" />
        </svg>
        Download
      </button>
      <button className="action-btn regenerate" onClick={handleRegenerate} title="Regenerate this page">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="23 4 23 10 17 10" />
          <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
        </svg>
        Regenerate
      </button>
    </div>
  );
}
