/**
 * Choose Your Own Adventure - AI-Powered Edition
 */

import './styles/main.css';
import { api, type StoryNode, type StoryData } from './api/client';
import { SaveManager } from './utils/SaveManager';

const DEFAULT_STORY = 'dragon-adventure';

class App {
  private container: HTMLElement;
  private storyData: StoryData | null = null;
  private currentNodeId: string = 'start';
  private history: string[] = [];
  private nodesMap: Map<string, StoryNode> = new Map();
  private isLoading: boolean = false;
  private hashChangeListenerAdded: boolean = false;

  constructor() {
    this.container = document.getElementById('app')!;
    this.init();
  }

  private async init(): Promise<void> {
    // Check for story ID in URL query params
    const urlParams = new URLSearchParams(window.location.search);
    const storyId = urlParams.get('story');

    if (storyId) {
      // Load specific story
      await this.loadStory(storyId);
    } else {
      // Show home page
      this.showHomePage();
    }
  }

  private setupHashChangeListener(): void {
    // Only add the listener once
    if (this.hashChangeListenerAdded) {
      return;
    }

    window.addEventListener('hashchange', () => {
      const newHash = window.location.hash.slice(1);
      if (newHash && newHash !== this.currentNodeId) {
        this.currentNodeId = newHash;
        this.renderCurrentNode();
      }
    });

    this.hashChangeListenerAdded = true;
  }

  private showHomePage(): void {
    // Check for saved games
    const hasSave = SaveManager.hasSave(DEFAULT_STORY);

    this.container.innerHTML = `
      <div class="header">
        <h1>🐉 Choose Your Own Adventure</h1>
        <p>AI-Powered Interactive Stories</p>
      </div>

      <div class="story-select">
        <div class="story-option">
          <h3>Dragon's Cave</h3>
          <p>Venture into a mysterious dragon's lair and navigate through dangerous encounters using your wits and courage.</p>
          <span class="story-theme">Fantasy</span>
          <div class="actions" style="margin-top: 1rem;">
            ${hasSave ? `
              <button class="btn" id="continue-btn">Continue Adventure</button>
              <button class="btn btn-secondary" id="new-game-btn">New Adventure</button>
            ` : `
              <button class="btn" id="start-btn">Start Adventure</button>
            `}
          </div>
        </div>
      </div>
    `;

    // Bind event handlers
    const continueBtn = this.container.querySelector('#continue-btn');
    const newGameBtn = this.container.querySelector('#new-game-btn');
    const startBtn = this.container.querySelector('#start-btn');

    continueBtn?.addEventListener('click', () => {
      this.loadGameFromSave(DEFAULT_STORY);
    });

    newGameBtn?.addEventListener('click', () => {
      this.startNewGame(DEFAULT_STORY);
    });

    startBtn?.addEventListener('click', () => {
      this.startNewGame(DEFAULT_STORY);
    });
  }

  private async loadGameFromSave(storyId: string): Promise<void> {
    const saveData = SaveManager.load(storyId);
    if (!saveData) {
      this.showToast('No saved game found');
      this.startNewGame(storyId);
      return;
    }

    // Update URL without reloading
    const url = new URL(window.location.href);
    url.searchParams.set('story', storyId);
    url.hash = saveData.nodeId;
    history.replaceState(null, '', url);

    this.showLoading('Loading saved game...');

    try {
      this.storyData = await api.getStory(storyId);
      this.nodesMap.clear();

      for (const node of this.storyData.nodes) {
        this.nodesMap.set(node.id, node);
      }

      // Restore saved state
      this.history = saveData.history;
      this.currentNodeId = saveData.nodeId;

      // Setup hash change listener (only once)
      this.setupHashChangeListener();

      this.renderCurrentNode();
      this.showToast('Game loaded!');
    } catch (error) {
      console.error('Failed to load game:', error);
      this.showError('Failed to load saved game. Please try again.');
    }
  }

  private async startNewGame(storyId: string): Promise<void> {
    // Clear any existing save
    SaveManager.deleteSave(storyId);

    // Update URL without reloading
    const url = new URL(window.location.href);
    url.searchParams.set('story', storyId);
    url.hash = '';
    history.replaceState(null, '', url);

    await this.loadStory(storyId);
  }

  private async loadStory(storyId: string): Promise<void> {
    this.showLoading('Loading story...');

    try {
      this.storyData = await api.getStory(storyId);
      this.nodesMap.clear();

      for (const node of this.storyData.nodes) {
        this.nodesMap.set(node.id, node);
      }

      // Initialize history with start node
      if (!this.history.length) {
        this.history = [this.storyData.meta.startNodeId];
        this.currentNodeId = this.storyData.meta.startNodeId;
      }

      // Setup hash change listener (only once)
      this.setupHashChangeListener();

      this.renderCurrentNode();
    } catch (error) {
      console.error('Failed to load story:', error);
      this.showError('Failed to load story. Please try again.');
    }
  }

  private getCurrentNode(): StoryNode | undefined {
    return this.nodesMap.get(this.currentNodeId);
  }

  private async renderCurrentNode(): Promise<void> {
    const node = this.getCurrentNode();

    if (!node) {
      this.showError('Story node not found');
      return;
    }

    // Auto-save progress
    if (this.storyData) {
      try {
        SaveManager.save(this.storyData.meta.id, this.currentNodeId, this.history);
      } catch (error) {
        console.error('Failed to auto-save:', error);
        // Don't interrupt the user experience for save failures
      }
    }

    // Update URL
    window.location.hash = node.id;

    // Render the node
    this.container.innerHTML = `
      <nav class="nav">
        <div class="nav-left">
          <button class="btn btn-secondary" id="back-btn" ${this.history.length <= 1 ? 'disabled' : ''}>
            ← Back
          </button>
        </div>
        <div class="nav-right">
          <button class="btn btn-secondary" id="save-btn">💾 Save</button>
          <button class="btn btn-secondary" id="load-btn">📂 Load</button>
          <button class="btn btn-secondary" id="share-btn">Share</button>
          <button class="btn btn-secondary" id="home-btn">Home</button>
        </div>
      </nav>

      <div class="story-card">
        <h2 class="fire-effect">${node.title}</h2>
        <div class="story-content">
          ${this.formatContent(node.content)}
        </div>

        <div id="choices-container">
          ${this.renderLoadingChoices()}
        </div>

        ${this.renderBranches(node)}
      </div>
    `;

    this.bindEventHandlers();

    // Load AI options if not already generated
    if (node.generatedOptions.length === 0) {
      await this.loadOptions(node);
    } else {
      this.renderChoices(node.generatedOptions, node.childNodeIds);
    }
  }

  private async loadOptions(node: StoryNode): Promise<void> {
    const container = document.getElementById('choices-container');
    if (!container) return;

    try {
      const result = await api.generateOptions(
        this.storyData!.meta.id,
        node.id
      );

      if (result.error) {
        console.warn('Option generation warning:', result.error);
      }

      // Update local node data
      node.generatedOptions = result.options;

      this.renderChoices(result.options, node.childNodeIds);
    } catch (error) {
      console.error('Failed to generate options:', error);
      container.innerHTML = `
        <div class="error-message">
          <p>Failed to generate options. Please try again.</p>
          <button class="btn" id="retry-options">Retry</button>
        </div>
      `;
      container.querySelector('#retry-options')?.addEventListener('click', () => {
        container.innerHTML = this.renderLoadingChoices();
        this.loadOptions(node);
      });
    }
  }

  private renderLoadingChoices(): string {
    return `
      <div class="choices loading">
        <div class="choice-skeleton">
          <div class="skeleton-text"></div>
          <div class="skeleton-shimmer"></div>
        </div>
        <div class="choice-skeleton">
          <div class="skeleton-text"></div>
          <div class="skeleton-shimmer"></div>
        </div>
        <p class="loading-hint">The AI is crafting your choices...</p>
      </div>
    `;
  }

  private renderChoices(options: string[], _existingChildIds: string[]): void {
    const container = document.getElementById('choices-container');
    if (!container) return;

    container.innerHTML = `
      <div class="choices">
        <h3 class="choices-header">What will you do?</h3>

        ${options.map((option) => `
          <button class="choice-btn ai-choice" data-option="${this.escapeHtml(option)}">
            <span class="choice-badge">AI</span>
            ${this.escapeHtml(option)}
          </button>
        `).join('')}

        <div class="custom-choice">
          <input
            type="text"
            id="custom-option"
            placeholder="Or write your own adventure..."
            maxlength="200"
          />
          <button class="btn" id="submit-custom">Go</button>
        </div>
      </div>
    `;

    // Bind choice handlers
    container.querySelectorAll('.ai-choice').forEach(btn => {
      btn.addEventListener('click', () => {
        const option = (btn as HTMLElement).dataset.option!;
        this.chooseOption(option);
      });
    });

    // Custom option handler
    const customInput = container.querySelector('#custom-option') as HTMLInputElement;
    const submitBtn = container.querySelector('#submit-custom');

    submitBtn?.addEventListener('click', () => {
      const option = customInput.value.trim();
      if (option) {
        this.chooseOption(option);
      }
    });

    customInput?.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        const option = customInput.value.trim();
        if (option) {
          this.chooseOption(option);
        }
      }
    });
  }

  private async chooseOption(option: string): Promise<void> {
    if (this.isLoading) return;
    this.isLoading = true;

    const container = document.getElementById('choices-container');
    if (!container) return;

    // Show loading state
    container.innerHTML = `
      <div class="generating">
        <div class="loading-spinner"></div>
        <p>Continuing your adventure...</p>
        <p class="loading-hint">"${this.escapeHtml(option)}"</p>
      </div>
    `;

    try {
      const result = await api.continueStory(
        this.storyData!.meta.id,
        this.currentNodeId,
        option
      );

      if (result.error) {
        throw new Error(result.error);
      }

      // Add new node to our map
      this.nodesMap.set(result.node.id, result.node);

      // Update parent node's children
      const parentNode = this.getCurrentNode();
      if (parentNode && !parentNode.childNodeIds.includes(result.node.id)) {
        parentNode.childNodeIds.push(result.node.id);
      }

      // Navigate to new node
      this.history.push(result.node.id);
      this.currentNodeId = result.node.id;
      this.isLoading = false;

      await this.renderCurrentNode();
    } catch (error) {
      this.isLoading = false;
      console.error('Failed to continue story:', error);

      container.innerHTML = `
        <div class="error-message">
          <p>${error instanceof Error ? error.message : 'Failed to continue story'}</p>
          <button class="btn" id="retry-continue">Try Again</button>
        </div>
      `;

      container.querySelector('#retry-continue')?.addEventListener('click', () => {
        this.chooseOption(option);
      });
    }
  }

  private renderBranches(node: StoryNode): string {
    if (node.childNodeIds.length === 0) {
      return '';
    }

    const branches = node.childNodeIds
      .map(id => this.nodesMap.get(id))
      .filter((n): n is StoryNode => n !== undefined);

    if (branches.length === 0) {
      return '';
    }

    return `
      <div class="branches">
        <h3 class="branches-header">Other adventurers chose:</h3>
        <div class="branch-list">
          ${branches.map(branch => `
            <button class="branch-btn" data-node-id="${branch.id}">
              <span class="branch-tagline">${this.escapeHtml(branch.tagline || branch.chosenOption || 'Continue')}</span>
              <span class="branch-arrow">→</span>
            </button>
          `).join('')}
        </div>
      </div>
    `;
  }

  private bindEventHandlers(): void {
    // Back button
    this.container.querySelector('#back-btn')?.addEventListener('click', () => {
      if (this.history.length > 1) {
        this.history.pop();
        this.currentNodeId = this.history[this.history.length - 1];
        this.renderCurrentNode();
      }
    });

    // Save button
    this.container.querySelector('#save-btn')?.addEventListener('click', () => {
      this.saveGame();
    });

    // Load button
    this.container.querySelector('#load-btn')?.addEventListener('click', () => {
      this.loadGame();
    });

    // Share button
    this.container.querySelector('#share-btn')?.addEventListener('click', () => {
      this.showShareModal();
    });

    // Home/Restart button
    this.container.querySelector('#home-btn')?.addEventListener('click', () => {
      // Go back to home page
      window.location.search = '';
      window.location.hash = '';
      window.location.reload();
    });

    // Branch buttons
    this.container.querySelectorAll('.branch-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const nodeId = (btn as HTMLElement).dataset.nodeId!;
        this.history.push(nodeId);
        this.currentNodeId = nodeId;
        this.renderCurrentNode();
      });
    });
  }

  private saveGame(): void {
    if (!this.storyData) return;

    try {
      SaveManager.save(this.storyData.meta.id, this.currentNodeId, this.history);
      this.showToast('Game saved!');
    } catch (error) {
      console.error('Failed to save game:', error);
      this.showToast('Failed to save game');
    }
  }

  private loadGame(): void {
    if (!this.storyData) return;

    const saveData = SaveManager.load(this.storyData.meta.id);
    if (!saveData) {
      this.showToast('No saved game found');
      return;
    }

    // Restore saved state
    this.history = saveData.history;
    this.currentNodeId = saveData.nodeId;
    this.renderCurrentNode();
    this.showToast('Game loaded!');
  }

  private showShareModal(): void {
    const shareUrl = window.location.href;

    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.innerHTML = `
      <div class="modal">
        <h3>Share This Moment</h3>
        <p>Share this exact point in the story with others:</p>
        <input type="text" readonly value="${shareUrl}" id="share-url">
        <div class="actions">
          <button class="btn" id="copy-btn">Copy Link</button>
          <button class="btn btn-secondary" id="close-modal">Close</button>
        </div>
      </div>
    `;

    document.body.appendChild(overlay);

    const input = overlay.querySelector('#share-url') as HTMLInputElement;
    input.focus();
    input.select();

    overlay.querySelector('#copy-btn')?.addEventListener('click', () => {
      navigator.clipboard.writeText(shareUrl);
      this.showToast('Link copied!');
      overlay.remove();
    });

    overlay.querySelector('#close-modal')?.addEventListener('click', () => {
      overlay.remove();
    });

    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) {
        overlay.remove();
      }
    });
  }

  private showLoading(message: string): void {
    this.container.innerHTML = `
      <div class="loading-screen">
        <div class="loading-spinner"></div>
        <p>${message}</p>
      </div>
    `;
  }

  private showError(message: string): void {
    this.container.innerHTML = `
      <div class="error-screen">
        <h2>Oops!</h2>
        <p>${message}</p>
        <button class="btn" onclick="location.reload()">Reload</button>
      </div>
    `;
  }

  private showToast(message: string): void {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
      toast.classList.add('fade-out');
      setTimeout(() => toast.remove(), 300);
    }, 2000);
  }

  private formatContent(content: string): string {
    return content
      .split('\n\n')
      .map(p => `<p>${this.escapeHtml(p)}</p>`)
      .join('');
  }

  private escapeHtml(text: string): string {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

// Initialize app
new App();
