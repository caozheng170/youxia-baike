import React, { useState } from 'react';
import SearchBar from './components/SearchBar';
import PageView from './components/PageView';
import ClickOverlay from './components/ClickOverlay';
import ActionBar from './components/ActionBar';
import { usePageGenerator } from './hooks/usePageGenerator';
import './App.css';

export default function App() {
  const {
    currentPage,
    breadcrumb,
    activeId,
    isGenerating,
    isPreview,
    exploreIntent,
    generate,
    explore,
    navigateTo,
    reset,
    cancel,
  } = usePageGenerator();

  // Selected model source, remembered locally and sent with each request.
  // Provider stays in localStorage; UI switch is hidden on the public site.
  const [provider] = useState(() => {
    try {
      return localStorage.getItem('provider') || 'cloud';
    } catch {
      return 'cloud';
    }
  });

  const handleSearch = (query) => {
    generate(query, provider);
  };

  const handleExplore = (pageId, clickX, clickY) => {
    explore(pageId, clickX, clickY, provider);
  };

  const handleRegenerate = (query) => {
    generate(query, provider);
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-brand" onClick={reset} title="回到首页">
          <span className="app-logo">📖</span>
          <h1 className="app-title">游侠百科</h1>
        </div>
      </header>

      <SearchBar
        onSearch={handleSearch}
        isGenerating={isGenerating}
        breadcrumb={breadcrumb}
        activeId={activeId}
        onNavigate={navigateTo}
        onClear={reset}
      />

      <main className="app-main">
        <PageView
          page={currentPage}
          isGenerating={isGenerating}
          isPreview={isPreview}
          exploreIntent={exploreIntent}
          onExplore={handleExplore}
          onCancel={cancel}
        />
      </main>

      <ActionBar page={currentPage} onRegenerate={handleRegenerate} />

      <footer className="app-footer">
        <span>Powered by 太湖边的虎子</span>
      </footer>
    </div>
  );
}
