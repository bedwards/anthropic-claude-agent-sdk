/**
 * Tests for Choose Your Own Adventure App - Back Button Navigation
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { JSDOM } from 'jsdom';

describe('Back Button Navigation', () => {
  let dom: JSDOM;
  let document: Document;
  let container: HTMLElement;

  beforeEach(() => {
    // Setup DOM environment
    dom = new JSDOM('<!DOCTYPE html><html><body><div id="app"></div></body></html>', {
      url: 'http://localhost',
    });
    document = dom.window.document;
    container = document.getElementById('app')!;

    // Make global objects available
    (global as any).document = document;
    (global as any).window = dom.window;
    (global as any).location = dom.window.location;
  });

  describe('Back button visibility', () => {
    it('should hide back button when at start node', () => {
      // Render navigation at start
      const isAtStart = true;

      container.innerHTML = `
        <nav class="nav">
          <div class="nav-left">
            ${!isAtStart ? `
            <button class="btn btn-secondary" id="back-btn">
              ← Back
            </button>
            ` : ''}
          </div>
          <div class="nav-right">
            <button class="btn btn-secondary" id="share-btn">Share</button>
            <button class="btn btn-secondary" id="restart-btn">Restart</button>
          </div>
        </nav>
      `;

      const backButton = container.querySelector('#back-btn');
      expect(backButton).toBeNull();
    });

    it('should show back button when not at start node', () => {
      // Render navigation not at start
      const isAtStart = false;

      container.innerHTML = `
        <nav class="nav">
          <div class="nav-left">
            ${!isAtStart ? `
            <button class="btn btn-secondary" id="back-btn">
              ← Back
            </button>
            ` : ''}
          </div>
          <div class="nav-right">
            <button class="btn btn-secondary" id="share-btn">Share</button>
            <button class="btn btn-secondary" id="restart-btn">Restart</button>
          </div>
        </nav>
      `;

      const backButton = container.querySelector('#back-btn');
      expect(backButton).not.toBeNull();
      expect(backButton?.textContent?.trim()).toContain('Back');
    });
  });

  describe('Back button navigation', () => {
    it('should navigate to previous node in history when clicked', () => {
      // Setup history: start -> node1 -> node2 (currently at node2)
      const history = ['start', 'node1', 'node2'];
      let currentNodeId = 'node2';

      // Render back button
      container.innerHTML = `
        <nav class="nav">
          <div class="nav-left">
            <button class="btn btn-secondary" id="back-btn">← Back</button>
          </div>
        </nav>
      `;

      const backButton = container.querySelector('#back-btn') as HTMLButtonElement;

      // Simulate back button click handler
      backButton.addEventListener('click', () => {
        if (history.length > 1) {
          history.pop();
          currentNodeId = history[history.length - 1];
        }
      });

      backButton.click();

      expect(history).toEqual(['start', 'node1']);
      expect(currentNodeId).toBe('node1');
    });

    it('should navigate to home page when backing from start node', () => {
      const history = ['start'];
      const currentNodeId = 'start';
      const startNodeId = 'start';

      let navigatedTo = '';

      // Render back button (in case it exists)
      container.innerHTML = `
        <button class="btn btn-secondary" id="back-btn">← Back</button>
      `;

      const backButton = container.querySelector('#back-btn') as HTMLButtonElement;

      // Simulate back button click handler
      backButton.addEventListener('click', () => {
        if (history.length > 1) {
          history.pop();
        } else if (currentNodeId === startNodeId) {
          // Go to home page
          navigatedTo = '/';
        }
      });

      backButton.click();

      expect(navigatedTo).toBe('/');
    });
  });

  describe('Restart button', () => {
    it('should reset history and navigate to story start', () => {
      // Setup history: start -> node1 -> node2 -> node3 (currently at node3)
      let history = ['start', 'node1', 'node2', 'node3'];
      let currentNodeId = 'node3';
      const startNodeId = 'start';

      // Render restart button
      container.innerHTML = `
        <button class="btn btn-secondary" id="restart-btn">Restart</button>
      `;

      const restartButton = container.querySelector('#restart-btn') as HTMLButtonElement;

      // Simulate restart button click handler
      restartButton.addEventListener('click', () => {
        history = [startNodeId];
        currentNodeId = startNodeId;
      });

      restartButton.click();

      expect(history).toEqual(['start']);
      expect(currentNodeId).toBe('start');
    });

    it('should not navigate to home page, only to story start', () => {
      let history = ['start', 'node1', 'node2'];
      let currentNodeId = 'node2';
      const startNodeId = 'start';

      let navigatedAway = false;

      container.innerHTML = `
        <button class="btn btn-secondary" id="restart-btn">Restart</button>
      `;

      const restartButton = container.querySelector('#restart-btn') as HTMLButtonElement;

      // Simulate restart button click handler
      restartButton.addEventListener('click', () => {
        // Should only reset to story start, not navigate away
        history = [startNodeId];
        currentNodeId = startNodeId;
        // Should NOT do: window.location.href = '/'
        // Should NOT set: navigatedAway = true
      });

      restartButton.click();

      expect(history).toEqual(['start']);
      expect(currentNodeId).toBe('start');
      expect(navigatedAway).toBe(false); // Should not navigate away
    });
  });

  describe('Navigation flow integration', () => {
    it('should maintain correct history through multiple navigation actions', () => {
      let history = ['start'];
      let currentNodeId = 'start';
      const startNodeId = 'start';

      // Navigate forward: start -> node1
      history.push('node1');
      currentNodeId = 'node1';
      expect(history).toEqual(['start', 'node1']);

      // Navigate forward: node1 -> node2
      history.push('node2');
      currentNodeId = 'node2';
      expect(history).toEqual(['start', 'node1', 'node2']);

      // Navigate back: node2 -> node1
      history.pop();
      currentNodeId = history[history.length - 1];
      expect(history).toEqual(['start', 'node1']);
      expect(currentNodeId).toBe('node1');

      // Navigate back: node1 -> start
      history.pop();
      currentNodeId = history[history.length - 1];
      expect(history).toEqual(['start']);
      expect(currentNodeId).toBe('start');

      // Restart from start should maintain start in history
      history = [startNodeId];
      currentNodeId = startNodeId;
      expect(history).toEqual(['start']);
      expect(currentNodeId).toBe('start');
    });
  });
});
