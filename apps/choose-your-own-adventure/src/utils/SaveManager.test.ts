import { describe, it, expect, beforeEach, vi } from 'vitest';
import { SaveManager, type SaveData } from './SaveManager';

describe('SaveManager', () => {
  let store: Record<string, string>;

  beforeEach(() => {
    // Mock localStorage
    store = {};
    vi.stubGlobal('localStorage', {
      getItem: vi.fn((key: string) => store[key] || null),
      setItem: vi.fn((key: string, value: string) => {
        store[key] = value;
      }),
      removeItem: vi.fn((key: string) => {
        delete store[key];
      }),
      clear: vi.fn(() => {
        Object.keys(store).forEach((key) => delete store[key]);
      }),
      get length() {
        return Object.keys(store).length;
      },
      key: vi.fn((index: number) => {
        const keys = Object.keys(store);
        return keys[index] || null;
      }),
    });
  });

  describe('save', () => {
    it('should save game progress', () => {
      const storyId = 'test-story';
      const nodeId = 'node-1';
      const history = ['start', 'node-1'];

      SaveManager.save(storyId, nodeId, history);

      expect(localStorage.setItem).toHaveBeenCalledWith(
        'cyoa-save-test-story',
        expect.any(String)
      );

      const savedData = JSON.parse(store['cyoa-save-test-story']);
      expect(savedData.nodeId).toBe(nodeId);
      expect(savedData.history).toEqual(history);
      expect(savedData.timestamp).toBeGreaterThan(0);
    });

    it('should clone history array to avoid reference issues', () => {
      const storyId = 'test-story';
      const history = ['start', 'node-1'];

      SaveManager.save(storyId, 'node-1', history);

      // Modify original array
      history.push('node-2');

      const loaded = SaveManager.load(storyId);
      expect(loaded?.history).toEqual(['start', 'node-1']);
      expect(loaded?.history).not.toEqual(history);
    });

    it('should throw error on localStorage failure', () => {
      const originalSetItem = localStorage.setItem;
      vi.spyOn(localStorage, 'setItem').mockImplementation(() => {
        throw new Error('Storage full');
      });

      expect(() => {
        SaveManager.save('test-story', 'node-1', ['start']);
      }).toThrow('Failed to save game progress');

      localStorage.setItem = originalSetItem;
    });
  });

  describe('load', () => {
    it('should load saved game progress', () => {
      const storyId = 'test-story';
      const saveData: SaveData = {
        nodeId: 'node-1',
        history: ['start', 'node-1'],
        timestamp: Date.now(),
      };

      store['cyoa-save-test-story'] = JSON.stringify(saveData);

      const loaded = SaveManager.load(storyId);

      expect(loaded).not.toBeNull();
      expect(loaded?.nodeId).toBe(saveData.nodeId);
      expect(loaded?.history).toEqual(saveData.history);
      expect(loaded?.timestamp).toBe(saveData.timestamp);
    });

    it('should return null if no save exists', () => {
      const loaded = SaveManager.load('non-existent-story');
      expect(loaded).toBeNull();
    });

    it('should return null for invalid save data', () => {
      store['cyoa-save-test-story'] = 'invalid json';
      const loaded = SaveManager.load('test-story');
      expect(loaded).toBeNull();
    });

    it('should return null for malformed save data', () => {
      store['cyoa-save-test-story'] = JSON.stringify({ invalid: 'data' });
      const loaded = SaveManager.load('test-story');
      expect(loaded).toBeNull();
    });
  });

  describe('hasSave', () => {
    it('should return true if save exists', () => {
      const saveData: SaveData = {
        nodeId: 'node-1',
        history: ['start', 'node-1'],
        timestamp: Date.now(),
      };

      store['cyoa-save-test-story'] = JSON.stringify(saveData);

      expect(SaveManager.hasSave('test-story')).toBe(true);
    });

    it('should return false if save does not exist', () => {
      expect(SaveManager.hasSave('non-existent-story')).toBe(false);
    });
  });

  describe('deleteSave', () => {
    it('should delete save data', () => {
      const saveData: SaveData = {
        nodeId: 'node-1',
        history: ['start', 'node-1'],
        timestamp: Date.now(),
      };

      store['cyoa-save-test-story'] = JSON.stringify(saveData);

      SaveManager.deleteSave('test-story');

      expect(localStorage.removeItem).toHaveBeenCalledWith('cyoa-save-test-story');
      expect(SaveManager.hasSave('test-story')).toBe(false);
    });
  });

  describe('getAllSaves', () => {
    it('should get all saved games', () => {
      const save1: SaveData = {
        nodeId: 'node-1',
        history: ['start', 'node-1'],
        timestamp: Date.now(),
      };

      const save2: SaveData = {
        nodeId: 'node-2',
        history: ['start', 'node-2'],
        timestamp: Date.now(),
      };

      store['cyoa-save-story-1'] = JSON.stringify(save1);
      store['cyoa-save-story-2'] = JSON.stringify(save2);
      store['other-key'] = 'should be ignored';

      const saves = SaveManager.getAllSaves();

      expect(saves.size).toBe(2);
      expect(saves.get('story-1')).toEqual(save1);
      expect(saves.get('story-2')).toEqual(save2);
    });

    it('should return empty map if no saves exist', () => {
      const saves = SaveManager.getAllSaves();
      expect(saves.size).toBe(0);
    });

    it('should skip invalid save data', () => {
      store['cyoa-save-story-1'] = 'invalid';
      store['cyoa-save-story-2'] = JSON.stringify({
        nodeId: 'node-1',
        history: ['start'],
        timestamp: Date.now(),
      });

      const saves = SaveManager.getAllSaves();
      expect(saves.size).toBe(1);
      expect(saves.has('story-1')).toBe(false);
      expect(saves.has('story-2')).toBe(true);
    });
  });

  describe('clearAllSaves', () => {
    it('should clear all saves', () => {
      store['cyoa-save-story-1'] = JSON.stringify({
        nodeId: 'node-1',
        history: ['start'],
        timestamp: Date.now(),
      });
      store['cyoa-save-story-2'] = JSON.stringify({
        nodeId: 'node-2',
        history: ['start'],
        timestamp: Date.now(),
      });
      store['other-key'] = 'should not be removed';

      SaveManager.clearAllSaves();

      expect(store['cyoa-save-story-1']).toBeUndefined();
      expect(store['cyoa-save-story-2']).toBeUndefined();
      expect(store['other-key']).toBe('should not be removed');
    });
  });
});
