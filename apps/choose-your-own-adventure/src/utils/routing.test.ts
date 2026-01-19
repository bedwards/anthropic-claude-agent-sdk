import { describe, it, expect } from 'vitest';
import { parseHash, formatHash } from './routing';

describe('routing utilities', () => {
  describe('parseHash', () => {
    it('should parse empty hash as null/null', () => {
      expect(parseHash('')).toEqual({ storyId: null, nodeId: null });
      expect(parseHash('#')).toEqual({ storyId: null, nodeId: null });
    });

    it('should parse #home as null/null', () => {
      expect(parseHash('home')).toEqual({ storyId: null, nodeId: null });
      expect(parseHash('#home')).toEqual({ storyId: null, nodeId: null });
    });

    it('should parse storyId only', () => {
      expect(parseHash('dragon-adventure')).toEqual({
        storyId: 'dragon-adventure',
        nodeId: null,
      });
      expect(parseHash('#dragon-adventure')).toEqual({
        storyId: 'dragon-adventure',
        nodeId: null,
      });
    });

    it('should parse storyId/nodeId format', () => {
      expect(parseHash('dragon-adventure/start')).toEqual({
        storyId: 'dragon-adventure',
        nodeId: 'start',
      });
      expect(parseHash('#dragon-adventure/start')).toEqual({
        storyId: 'dragon-adventure',
        nodeId: 'start',
      });
    });

    it('should parse complex nodeIds', () => {
      expect(parseHash('dragon-adventure/node-1768845953049-qsdzf8')).toEqual({
        storyId: 'dragon-adventure',
        nodeId: 'node-1768845953049-qsdzf8',
      });
    });

    it('should handle invalid formats with multiple slashes', () => {
      expect(parseHash('story/node/extra')).toEqual({
        storyId: null,
        nodeId: null,
      });
    });

    it('should handle edge cases', () => {
      expect(parseHash('/')).toEqual({ storyId: null, nodeId: null });
      expect(parseHash('#/')).toEqual({ storyId: null, nodeId: null });
      expect(parseHash('story/')).toEqual({ storyId: 'story', nodeId: null });
    });
  });

  describe('formatHash', () => {
    it('should format null storyId as empty string', () => {
      expect(formatHash(null, null)).toBe('');
      expect(formatHash(null, 'node')).toBe('');
    });

    it('should format storyId only', () => {
      expect(formatHash('dragon-adventure', null)).toBe('#dragon-adventure');
    });

    it('should format storyId/nodeId', () => {
      expect(formatHash('dragon-adventure', 'start')).toBe('#dragon-adventure/start');
      expect(formatHash('dragon-adventure', 'node-123')).toBe('#dragon-adventure/node-123');
    });
  });


  describe('parseHash and formatHash roundtrip', () => {
    it('should be reversible for valid formats', () => {
      const cases = [
        { storyId: 'dragon-adventure', nodeId: 'start' },
        { storyId: 'dragon-adventure', nodeId: null },
        { storyId: 'story-123', nodeId: 'node-456' },
      ];

      for (const params of cases) {
        const hash = formatHash(params.storyId, params.nodeId);
        const parsed = parseHash(hash);
        expect(parsed).toEqual(params);
      }
    });
  });

  describe('URL examples from issue', () => {
    it('should handle #dragon-adventure/start', () => {
      const parsed = parseHash('#dragon-adventure/start');
      expect(parsed.storyId).toBe('dragon-adventure');
      expect(parsed.nodeId).toBe('start');
    });

    it('should handle #home', () => {
      const parsed = parseHash('#home');
      expect(parsed.storyId).toBe(null);
      expect(parsed.nodeId).toBe(null);
    });

    it('should format as #storyId/nodeId', () => {
      const hash = formatHash('dragon-adventure', 'node123');
      expect(hash).toBe('#dragon-adventure/node123');
    });
  });
});
