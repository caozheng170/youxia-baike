import { useState, useCallback, useRef } from 'react';
import { generatePage, explorePage, API_BASE } from '../api/client';

/**
 * Hook for managing page generation and exploration state.
 *
 * `breadcrumb` is the FULL explored path and is preserved when you navigate
 * back to an earlier level (so forward levels stay switchable). Exploring from
 * a level branches: it truncates anything after that level, then appends.
 */
export function usePageGenerator() {
  const [currentPage, setCurrentPage] = useState(null);
  const [breadcrumb, setBreadcrumb] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isPreview, setIsPreview] = useState(false);
  const [exploreIntent, setExploreIntent] = useState(null);
  const streamRef = useRef(null);

  const generate = useCallback(async (query, provider) => {
    streamRef.current?.close();
    setIsGenerating(true);
    setIsPreview(true);
    setCurrentPage(null);
    setExploreIntent(null);

    const stream = generatePage(query, {
      provider,
      onPreview: (data) => {
        setCurrentPage({ id: data.page_id, query: data.query, image: data.image });
        // A brand-new search starts a fresh path.
        setBreadcrumb([{ id: data.page_id, query: data.query }]);
        setActiveId(data.page_id);
      },
      onFull: (data) => {
        setCurrentPage((prev) => (prev ? { ...prev, image: data.image } : prev));
        setIsPreview(false);
        setIsGenerating(false);
      },
      onError: (err) => {
        console.error('Generation error:', err);
        setIsGenerating(false);
      },
    });

    streamRef.current = stream;
  }, []);

  const explore = useCallback(async (pageId, clickX, clickY, provider) => {
    streamRef.current?.close();
    setIsGenerating(true);
    setIsPreview(true);
    setExploreIntent(null);

    const stream = explorePage(pageId, clickX, clickY, {
      provider,
      onIntent: (data) => {
        setExploreIntent(data.intent || '');
      },
      onPreview: (data) => {
        setCurrentPage({ id: data.page_id, query: data.query, image: data.image });
        setActiveId(data.page_id);
        // Branch from the explored level: keep up to it, drop deeper, append child.
        setBreadcrumb((prev) => {
          const idx = prev.findIndex((t) => t.id === pageId);
          const base = idx >= 0 ? prev.slice(0, idx + 1) : prev;
          return [...base, { id: data.page_id, query: data.query }];
        });
      },
      onFull: (data) => {
        setCurrentPage((prev) => (prev ? { ...prev, image: data.image } : prev));
        setIsPreview(false);
        setIsGenerating(false);
        setExploreIntent(null);
      },
      onError: (err) => {
        console.error('Explore error:', err);
        setIsGenerating(false);
        setExploreIntent(null);
      },
    });

    streamRef.current = stream;
  }, []);

  const cancel = useCallback(() => {
    streamRef.current?.close();
    streamRef.current = null;
    setIsGenerating(false);
    setIsPreview(false);
    setExploreIntent(null);
  }, []);

  const navigateTo = useCallback((pageId) => {
    // Switch which level is shown WITHOUT shrinking the explored path.
    streamRef.current?.close();
    setExploreIntent(null);
    fetch(`${API_BASE}/page/${pageId}`)
      .then((r) => r.json())
      .then((data) => {
        setCurrentPage({
          id: data.id,
          query: data.query,
          image: data.has_image
            ? `${API_BASE}/page/${pageId}/image`
            : data.has_preview
            ? `${API_BASE}/page/${pageId}/preview`
            : null,
        });
        setActiveId(pageId);
        setIsPreview(!data.has_image);
        setIsGenerating(false);
        // NOTE: breadcrumb is intentionally left untouched (preserve full path).
      })
      .catch(console.error);
  }, []);

  const reset = useCallback(() => {
    streamRef.current?.close();
    setCurrentPage(null);
    setBreadcrumb([]);
    setActiveId(null);
    setIsGenerating(false);
    setIsPreview(false);
    setExploreIntent(null);
  }, []);

  return {
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
  };
}
