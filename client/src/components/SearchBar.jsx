import React from 'react';
import './SearchBar.css';

export default function SearchBar({
  onSearch,
  isGenerating,
  breadcrumb = [],
  activeId,
  onNavigate,
  onClear,
}) {
  const [query, setQuery] = React.useState('');
  const hasTrail = breadcrumb && breadcrumb.length > 0;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && !isGenerating) {
      onSearch(query.trim());
    }
  };

  const handleClear = () => {
    setQuery('');
    onClear?.();
  };

  const showClear = hasTrail || query.length > 0;

  return (
    <form className="search-bar" onSubmit={handleSubmit}>
      <div className={`search-input-wrap ${hasTrail ? 'is-nav' : ''}`}>
        {hasTrail ? (
          <nav className="search-nav" aria-label="导航">
            {breadcrumb.map((item, idx) => {
              const isActive = activeId != null ? item.id === activeId : idx === breadcrumb.length - 1;
              return (
                <React.Fragment key={item.id}>
                  {idx > 0 && <span className="search-nav-sep">›</span>}
                  <button
                    type="button"
                    className={`search-nav-item ${isActive ? 'active' : ''}`}
                    onClick={() => !isActive && !isGenerating && onNavigate?.(item.id)}
                    disabled={isActive || isGenerating}
                    title={item.query}
                  >
                    <span className="search-nav-index">{idx + 1}</span>
                    <span className="search-nav-text">
                      {item.query.length > 28 ? item.query.slice(0, 28) + '…' : item.query}
                    </span>
                  </button>
                </React.Fragment>
              );
            })}
          </nav>
        ) : (
          <>
            <svg className="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <input
              type="text"
              className="search-input"
              placeholder="Explore anything... (e.g. solar system, coffee making, quantum physics)"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={isGenerating}
              autoFocus
            />
          </>
        )}

        {showClear && (
          <button
            type="button"
            className="clear-btn"
            onClick={handleClear}
            disabled={isGenerating}
            title="清空并重新开始"
            aria-label="Clear"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        )}

        {!hasTrail && (
          <button
            type="submit"
            className="search-btn"
            disabled={!query.trim() || isGenerating}
          >
            {isGenerating ? <span className="spinner" /> : 'Explore'}
          </button>
        )}
      </div>
    </form>
  );
}
