'use client';

import { useEffect } from 'react';

// This hook guards against accidental page unloads.
// In SPA mode it will NOT work when user clicks Next's Link
export function useUnloadWarning(enabled = true) {
  useEffect(() => {
    if (!enabled) return;

    const handleBeforeUnload = (e) => {
      e.preventDefault();
      e.returnValue = '';
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [enabled]);
}
