/**
 * Story Engine - handles story state, navigation, and persistence
 */

import type { Story, StoryNode, Choice, GameState, SavedGame } from './types';

const STORAGE_KEY = 'cyoa_saved_games';

export class StoryEngine {
  private story: Story;
  private state: GameState;
  private onStateChange: ((state: GameState, node: StoryNode) => void) | null = null;

  constructor(story: Story, initialState?: GameState) {
    this.story = story;
    this.state = initialState || this.createInitialState();
  }

  private createInitialState(): GameState {
    return {
      storyId: this.story.id,
      currentNodeId: this.story.startNodeId,
      history: [this.story.startNodeId],
      variables: {},
      startedAt: Date.now(),
      lastUpdated: Date.now(),
    };
  }

  /**
   * Get the current story node
   */
  getCurrentNode(): StoryNode {
    const node = this.story.nodes[this.state.currentNodeId];
    if (!node) {
      throw new Error(`Node not found: ${this.state.currentNodeId}`);
    }
    return node;
  }

  /**
   * Get available choices for the current node
   */
  getAvailableChoices(): Choice[] {
    const node = this.getCurrentNode();
    return node.choices.filter(choice => {
      if (choice.condition) {
        return choice.condition(this.state);
      }
      return true;
    });
  }

  /**
   * Make a choice and advance the story
   */
  makeChoice(choiceId: string): StoryNode {
    const node = this.getCurrentNode();
    const choice = node.choices.find(c => c.id === choiceId);

    if (!choice) {
      throw new Error(`Choice not found: ${choiceId}`);
    }

    // Check if choice is available
    if (choice.condition && !choice.condition(this.state)) {
      throw new Error(`Choice condition not met: ${choiceId}`);
    }

    // Apply node effect if any
    if (node.effect) {
      this.state = node.effect(this.state);
    }

    // Navigate to next node
    this.state.currentNodeId = choice.nextNodeId;
    this.state.history.push(choice.nextNodeId);
    this.state.lastUpdated = Date.now();

    const nextNode = this.getCurrentNode();

    // Notify listeners
    if (this.onStateChange) {
      this.onStateChange(this.state, nextNode);
    }

    return nextNode;
  }

  /**
   * Go back one step in history
   */
  goBack(): StoryNode | null {
    if (this.state.history.length <= 1) {
      return null;
    }

    this.state.history.pop();
    this.state.currentNodeId = this.state.history[this.state.history.length - 1];
    this.state.lastUpdated = Date.now();

    const node = this.getCurrentNode();

    if (this.onStateChange) {
      this.onStateChange(this.state, node);
    }

    return node;
  }

  /**
   * Restart the story
   */
  restart(): StoryNode {
    this.state = this.createInitialState();
    const node = this.getCurrentNode();

    if (this.onStateChange) {
      this.onStateChange(this.state, node);
    }

    return node;
  }

  /**
   * Get current game state
   */
  getState(): GameState {
    return { ...this.state };
  }

  /**
   * Set a variable in the game state
   */
  setVariable(key: string, value: string | number | boolean): void {
    this.state.variables[key] = value;
    this.state.lastUpdated = Date.now();
  }

  /**
   * Get a variable from the game state
   */
  getVariable<T extends string | number | boolean>(key: string): T | undefined {
    return this.state.variables[key] as T | undefined;
  }

  /**
   * Check if current node is an ending
   */
  isEnding(): boolean {
    return this.getCurrentNode().isEnding === true;
  }

  /**
   * Subscribe to state changes
   */
  subscribe(callback: (state: GameState, node: StoryNode) => void): () => void {
    this.onStateChange = callback;
    return () => {
      this.onStateChange = null;
    };
  }

  /**
   * Save game to localStorage
   */
  save(slotName: string = 'autosave'): void {
    const savedGames = this.loadAllSaves();
    savedGames[slotName] = {
      state: this.state,
      storyTitle: this.story.title,
      savedAt: Date.now(),
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(savedGames));
  }

  /**
   * Load all saved games
   */
  static loadAllSaves(): Record<string, SavedGame> {
    try {
      const data = localStorage.getItem(STORAGE_KEY);
      return data ? JSON.parse(data) : {};
    } catch {
      return {};
    }
  }

  private loadAllSaves(): Record<string, SavedGame> {
    return StoryEngine.loadAllSaves();
  }

  /**
   * Load a saved game
   */
  load(slotName: string): boolean {
    const savedGames = this.loadAllSaves();
    const saved = savedGames[slotName];

    if (!saved || saved.state.storyId !== this.story.id) {
      return false;
    }

    this.state = saved.state;

    if (this.onStateChange) {
      this.onStateChange(this.state, this.getCurrentNode());
    }

    return true;
  }

  /**
   * Export state to shareable URL hash
   */
  exportToHash(): string {
    const data = {
      s: this.state.storyId,
      n: this.state.currentNodeId,
      h: this.state.history,
      v: this.state.variables,
    };
    return btoa(JSON.stringify(data));
  }

  /**
   * Import state from URL hash
   */
  importFromHash(hash: string): boolean {
    try {
      const data = JSON.parse(atob(hash));
      if (data.s !== this.story.id) {
        return false;
      }

      this.state = {
        storyId: data.s,
        currentNodeId: data.n,
        history: data.h,
        variables: data.v || {},
        startedAt: Date.now(),
        lastUpdated: Date.now(),
      };

      if (this.onStateChange) {
        this.onStateChange(this.state, this.getCurrentNode());
      }

      return true;
    } catch {
      return false;
    }
  }

  /**
   * Get story metadata
   */
  getStoryInfo(): { id: string; title: string; description: string; theme: string } {
    return {
      id: this.story.id,
      title: this.story.title,
      description: this.story.description,
      theme: this.story.theme,
    };
  }

  /**
   * Get progress percentage
   */
  getProgress(): number {
    const totalNodes = Object.keys(this.story.nodes).length;
    const visitedNodes = new Set(this.state.history).size;
    return Math.round((visitedNodes / totalNodes) * 100);
  }
}
