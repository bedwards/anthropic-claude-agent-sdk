/**
 * SaveManager - Handles saving and loading game progress to LocalStorage
 */

export interface SaveData {
  nodeId: string;
  history: string[];
  timestamp: number;
}

export class SaveManager {
  private static readonly SAVE_KEY_PREFIX = 'cyoa-save-';

  /**
   * Save game progress for a story
   */
  static save(storyId: string, nodeId: string, history: string[]): void {
    const saveData: SaveData = {
      nodeId,
      history: [...history], // Clone to avoid reference issues
      timestamp: Date.now(),
    };

    try {
      const key = this.getSaveKey(storyId);
      localStorage.setItem(key, JSON.stringify(saveData));
    } catch (error) {
      console.error('Failed to save game:', error);
      throw new Error('Failed to save game progress');
    }
  }

  /**
   * Load game progress for a story
   */
  static load(storyId: string): SaveData | null {
    try {
      const key = this.getSaveKey(storyId);
      const data = localStorage.getItem(key);

      if (!data) {
        return null;
      }

      const saveData = JSON.parse(data) as SaveData;

      // Validate the save data structure
      if (
        !saveData.nodeId ||
        !Array.isArray(saveData.history) ||
        typeof saveData.timestamp !== 'number'
      ) {
        console.warn('Invalid save data structure');
        return null;
      }

      return saveData;
    } catch (error) {
      console.error('Failed to load game:', error);
      return null;
    }
  }

  /**
   * Check if a save exists for a story
   */
  static hasSave(storyId: string): boolean {
    const key = this.getSaveKey(storyId);
    return localStorage.getItem(key) !== null;
  }

  /**
   * Delete save data for a story
   */
  static deleteSave(storyId: string): void {
    const key = this.getSaveKey(storyId);
    localStorage.removeItem(key);
  }

  /**
   * Get all saved games
   */
  static getAllSaves(): Map<string, SaveData> {
    const saves = new Map<string, SaveData>();

    try {
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith(this.SAVE_KEY_PREFIX)) {
          const storyId = key.substring(this.SAVE_KEY_PREFIX.length);
          const saveData = this.load(storyId);
          if (saveData) {
            saves.set(storyId, saveData);
          }
        }
      }
    } catch (error) {
      console.error('Failed to get all saves:', error);
    }

    return saves;
  }

  /**
   * Get the LocalStorage key for a story
   */
  private static getSaveKey(storyId: string): string {
    return `${this.SAVE_KEY_PREFIX}${storyId}`;
  }

  /**
   * Clear all saves (useful for testing)
   */
  static clearAllSaves(): void {
    const keys: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(this.SAVE_KEY_PREFIX)) {
        keys.push(key);
      }
    }
    keys.forEach((key) => localStorage.removeItem(key));
  }
}
