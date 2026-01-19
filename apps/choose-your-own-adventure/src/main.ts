/**
 * Choose Your Own Adventure - Main Entry Point
 */

import './styles/main.css';
import { StoryEngine } from './engine/StoryEngine';
import { storyList, getStory } from './stories';
import type { StoryNode } from './engine/types';

class App {
  private engine: StoryEngine | null = null;
  private container: HTMLElement;

  constructor() {
    this.container = document.getElementById('app')!;
    this.init();
  }

  private init(): void {
    // Check for shared state in URL hash
    const hash = window.location.hash.slice(1);
    if (hash) {
      this.loadFromHash(hash);
    } else {
      this.showStorySelection();
    }

    // Listen for hash changes
    window.addEventListener('hashchange', () => {
      const newHash = window.location.hash.slice(1);
      if (newHash) {
        this.loadFromHash(newHash);
      }
    });
  }

  private loadFromHash(hash: string): void {
    try {
      const data = JSON.parse(atob(hash));
      const story = getStory(data.s);
      if (story) {
        this.startStory(data.s, true);
        this.engine?.importFromHash(hash);
      } else {
        this.showStorySelection();
      }
    } catch {
      this.showStorySelection();
    }
  }

  private showStorySelection(): void {
    this.container.innerHTML = `
      <div class="header">
        <h1>Choose Your Own Adventure</h1>
        <p>Select a story to begin your journey</p>
      </div>
      <div class="story-select">
        ${storyList.map(story => `
          <div class="story-option" data-story-id="${story.id}">
            <h3>${story.title}</h3>
            <p>${story.description}</p>
            <span class="story-theme">${story.theme}</span>
          </div>
        `).join('')}
      </div>
      ${this.renderSavedGames()}
    `;

    // Add click handlers for story selection
    this.container.querySelectorAll('.story-option').forEach(el => {
      el.addEventListener('click', () => {
        const storyId = (el as HTMLElement).dataset.storyId!;
        this.startStory(storyId);
      });
    });

    // Add click handlers for saved games
    this.container.querySelectorAll('.saved-game').forEach(el => {
      el.addEventListener('click', () => {
        const storyId = (el as HTMLElement).dataset.storyId!;
        const slot = (el as HTMLElement).dataset.slot!;
        this.startStory(storyId);
        this.engine?.load(slot);
      });
    });
  }

  private renderSavedGames(): string {
    const saves = StoryEngine.loadAllSaves();
    const entries = Object.entries(saves);

    if (entries.length === 0) return '';

    return `
      <div class="story-card">
        <h2>Continue Your Adventure</h2>
        <div class="story-select">
          ${entries.map(([slot, save]) => `
            <div class="story-option saved-game" data-story-id="${save.state.storyId}" data-slot="${slot}">
              <h3>${save.storyTitle}</h3>
              <p>Saved: ${new Date(save.savedAt).toLocaleString()}</p>
              <span class="story-theme">${slot}</span>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  private startStory(storyId: string, skipClear: boolean = false): void {
    const story = getStory(storyId);
    if (!story) {
      console.error(`Story not found: ${storyId}`);
      return;
    }

    this.engine = new StoryEngine(story);
    this.engine.subscribe((_state, node) => this.renderNode(node));

    if (!skipClear) {
      window.location.hash = '';
    }

    this.renderNode(this.engine.getCurrentNode());
  }

  private renderNode(node: StoryNode): void {
    const isEnding = node.isEnding;
    const endingClass = isEnding ? ` ending ${node.endingType || 'neutral'}` : '';
    const progress = this.engine?.getProgress() || 0;

    this.container.innerHTML = `
      <nav class="nav">
        <div class="nav-left">
          <button class="btn btn-secondary" id="back-btn" ${(this.engine?.getState().history.length || 0) <= 1 ? 'disabled' : ''}>
            ← Back
          </button>
        </div>
        <div class="nav-right">
          <button class="btn btn-secondary" id="share-btn">Share</button>
          <button class="btn btn-secondary" id="save-btn">Save</button>
          <button class="btn btn-secondary" id="home-btn">Stories</button>
        </div>
      </nav>

      <div class="progress-bar">
        <div class="progress-fill" style="width: ${progress}%"></div>
      </div>

      <div class="story-card${endingClass}">
        <h2 class="fire-effect">${node.title}</h2>
        <div class="story-content">
          ${this.formatContent(node.content)}
        </div>

        ${isEnding ? this.renderEndingActions() : this.renderChoices()}
      </div>
    `;

    // Bind event handlers
    this.bindEventHandlers();
  }

  private formatContent(content: string): string {
    return content
      .split('\n\n')
      .map(p => `<p>${p}</p>`)
      .join('');
  }

  private renderChoices(): string {
    const choices = this.engine?.getAvailableChoices() || [];

    if (choices.length === 0) {
      return '<p class="text-muted">No choices available...</p>';
    }

    return `
      <div class="choices">
        ${choices.map(choice => `
          <button class="choice-btn" data-choice-id="${choice.id}">
            ${choice.text}
          </button>
        `).join('')}
      </div>
    `;
  }

  private renderEndingActions(): string {
    return `
      <div class="actions">
        <button class="btn" id="restart-btn">Play Again</button>
        <button class="btn btn-secondary" id="home-btn-ending">Choose Another Story</button>
      </div>
    `;
  }

  private bindEventHandlers(): void {
    // Choice buttons
    this.container.querySelectorAll('.choice-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const choiceId = (btn as HTMLElement).dataset.choiceId!;
        this.engine?.makeChoice(choiceId);
      });
    });

    // Back button
    this.container.querySelector('#back-btn')?.addEventListener('click', () => {
      this.engine?.goBack();
    });

    // Share button
    this.container.querySelector('#share-btn')?.addEventListener('click', () => {
      this.showShareModal();
    });

    // Save button
    this.container.querySelector('#save-btn')?.addEventListener('click', () => {
      this.engine?.save('autosave');
      this.showToast('Game saved!');
    });

    // Home button
    this.container.querySelector('#home-btn')?.addEventListener('click', () => {
      this.showStorySelection();
    });

    // Restart button (for endings)
    this.container.querySelector('#restart-btn')?.addEventListener('click', () => {
      this.engine?.restart();
    });

    // Home button in ending
    this.container.querySelector('#home-btn-ending')?.addEventListener('click', () => {
      this.showStorySelection();
    });
  }

  private showShareModal(): void {
    const hash = this.engine?.exportToHash() || '';
    const shareUrl = `${window.location.origin}${window.location.pathname}#${hash}`;

    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.innerHTML = `
      <div class="modal">
        <h3>Share Your Progress</h3>
        <p>Copy this link to share your current position in the story:</p>
        <input type="text" readonly value="${shareUrl}" id="share-url">
        <div class="actions">
          <button class="btn" id="copy-btn">Copy Link</button>
          <button class="btn btn-secondary" id="close-modal">Close</button>
        </div>
      </div>
    `;

    document.body.appendChild(overlay);

    // Select input on focus
    const input = overlay.querySelector('#share-url') as HTMLInputElement;
    input.focus();
    input.select();

    // Copy button
    overlay.querySelector('#copy-btn')?.addEventListener('click', () => {
      navigator.clipboard.writeText(shareUrl);
      this.showToast('Link copied!');
      overlay.remove();
    });

    // Close button
    overlay.querySelector('#close-modal')?.addEventListener('click', () => {
      overlay.remove();
    });

    // Close on overlay click
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) {
        overlay.remove();
      }
    });
  }

  private showToast(message: string): void {
    const toast = document.createElement('div');
    toast.style.cssText = `
      position: fixed;
      bottom: 20px;
      left: 50%;
      transform: translateX(-50%);
      background: var(--color-accent);
      color: white;
      padding: 12px 24px;
      border-radius: 8px;
      font-size: 14px;
      z-index: 200;
      animation: fadeIn 0.3s ease;
    `;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transition = 'opacity 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 2000);
  }
}

// Initialize app
new App();
