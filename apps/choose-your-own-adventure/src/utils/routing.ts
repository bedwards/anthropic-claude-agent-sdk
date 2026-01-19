/**
 * URL Routing utilities for CYOA app
 * Handles URL format: #storyId/nodeId or #home
 */

export interface RouteParams {
  storyId: string | null;
  nodeId: string | null;
}

/**
 * Parse the URL hash into storyId and nodeId
 * Supports formats:
 * - #storyId/nodeId (e.g., #dragon-adventure/start)
 * - #home or empty (returns null for both)
 * - #storyId (returns storyId with null nodeId)
 * - Invalid formats return null for both
 */
export function parseHash(hash: string): RouteParams {
  // Remove leading # if present
  const cleanHash = hash.startsWith('#') ? hash.slice(1) : hash;

  // Empty hash or #home
  if (!cleanHash || cleanHash === 'home') {
    return { storyId: null, nodeId: null };
  }

  // Split by first /
  const parts = cleanHash.split('/');

  if (parts.length === 1) {
    // Just storyId provided (e.g., #dragon-adventure)
    const storyId = parts[0] || null;
    return { storyId, nodeId: null };
  } else if (parts.length === 2) {
    // Both storyId and nodeId provided
    const storyId = parts[0] || null;
    const nodeId = parts[1] || null;
    return { storyId, nodeId };
  } else {
    // Invalid format (more than one /)
    return { storyId: null, nodeId: null };
  }
}

/**
 * Format storyId and nodeId into a URL hash
 * Returns empty string for home, or #storyId/nodeId format
 */
export function formatHash(storyId: string | null, nodeId: string | null): string {
  if (!storyId) {
    return '';
  }

  if (!nodeId) {
    return `#${storyId}`;
  }

  return `#${storyId}/${nodeId}`;
}

/**
 * Get the current route params from window.location.hash
 */
export function getCurrentRoute(): RouteParams {
  return parseHash(window.location.hash);
}

/**
 * Set the URL hash without triggering a page reload
 */
export function setRoute(storyId: string | null, nodeId: string | null): void {
  const hash = formatHash(storyId, nodeId);
  if (hash) {
    window.location.hash = hash;
  } else {
    // Remove hash entirely for home
    history.replaceState(null, '', window.location.pathname);
  }
}
