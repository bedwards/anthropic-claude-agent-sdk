import { describe, it, expect, beforeEach, vi } from 'vitest';
import { StoryEngine } from './StoryEngine';
import type { Story, GameState } from './types';

// Create a simple test story
const createTestStory = (): Story => ({
  id: 'test-story',
  title: 'Test Story',
  description: 'A test story for unit tests',
  theme: 'fantasy',
  startNodeId: 'start',
  nodes: {
    start: {
      id: 'start',
      title: 'The Beginning',
      content: 'You are at the start.',
      choices: [
        { id: 'go-left', text: 'Go left', nextNodeId: 'left' },
        { id: 'go-right', text: 'Go right', nextNodeId: 'right' },
        {
          id: 'secret',
          text: 'Secret path',
          nextNodeId: 'secret',
          condition: (state) => state.variables['hasKey'] === true,
        },
      ],
    },
    left: {
      id: 'left',
      title: 'Left Path',
      content: 'You went left.',
      choices: [{ id: 'back', text: 'Go back', nextNodeId: 'start' }],
      effect: (state) => ({ ...state, variables: { ...state.variables, visited_left: true } }),
    },
    right: {
      id: 'right',
      title: 'Right Path',
      content: 'You found a key!',
      choices: [{ id: 'back', text: 'Go back', nextNodeId: 'start' }],
      effect: (state) => ({ ...state, variables: { ...state.variables, hasKey: true } }),
    },
    secret: {
      id: 'secret',
      title: 'Victory!',
      content: 'You found the treasure!',
      choices: [],
      isEnding: true,
      endingType: 'victory',
    },
  },
});

describe('StoryEngine', () => {
  let engine: StoryEngine;
  let story: Story;

  beforeEach(() => {
    story = createTestStory();
    engine = new StoryEngine(story);
    // Mock localStorage
    const store: Record<string, string> = {};
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
    });
  });

  describe('initialization', () => {
    it('should start at the correct node', () => {
      const node = engine.getCurrentNode();
      expect(node.id).toBe('start');
      expect(node.title).toBe('The Beginning');
    });

    it('should have initial state', () => {
      const state = engine.getState();
      expect(state.storyId).toBe('test-story');
      expect(state.currentNodeId).toBe('start');
      expect(state.history).toEqual(['start']);
      expect(state.variables).toEqual({});
    });

    it('should accept initial state', () => {
      const initialState: GameState = {
        storyId: 'test-story',
        currentNodeId: 'left',
        history: ['start', 'left'],
        variables: { test: true },
        startedAt: Date.now(),
        lastUpdated: Date.now(),
      };
      const customEngine = new StoryEngine(story, initialState);
      expect(customEngine.getCurrentNode().id).toBe('left');
      expect(customEngine.getState().variables).toEqual({ test: true });
    });
  });

  describe('navigation', () => {
    it('should make a choice and navigate to next node', () => {
      const node = engine.makeChoice('go-left');
      expect(node.id).toBe('left');
      expect(engine.getState().currentNodeId).toBe('left');
    });

    it('should update history when making choices', () => {
      engine.makeChoice('go-left');
      expect(engine.getState().history).toEqual(['start', 'left']);
    });

    it('should throw error for invalid choice', () => {
      expect(() => engine.makeChoice('invalid')).toThrow('Choice not found: invalid');
    });

    it('should go back in history', () => {
      engine.makeChoice('go-left');
      expect(engine.getCurrentNode().id).toBe('left');

      const prevNode = engine.goBack();
      expect(prevNode?.id).toBe('start');
      expect(engine.getState().history).toEqual(['start']);
    });

    it('should return null when cannot go back', () => {
      const result = engine.goBack();
      expect(result).toBeNull();
    });

    it('should restart the story', () => {
      engine.makeChoice('go-left');
      engine.makeChoice('back');
      engine.makeChoice('go-right');

      engine.restart();
      expect(engine.getCurrentNode().id).toBe('start');
      expect(engine.getState().history).toEqual(['start']);
      expect(engine.getState().variables).toEqual({});
    });
  });

  describe('choices and conditions', () => {
    it('should return available choices', () => {
      const choices = engine.getAvailableChoices();
      expect(choices).toHaveLength(2); // secret path not available
      expect(choices.map((c) => c.id)).toEqual(['go-left', 'go-right']);
    });

    it('should include conditional choice when condition is met', () => {
      engine.makeChoice('go-right'); // Get the key
      engine.makeChoice('back'); // Go back to start

      const choices = engine.getAvailableChoices();
      expect(choices).toHaveLength(3);
      expect(choices.map((c) => c.id)).toContain('secret');
    });

    it('should throw error when trying to make unavailable choice', () => {
      expect(() => engine.makeChoice('secret')).toThrow('Choice condition not met: secret');
    });
  });

  describe('effects and variables', () => {
    it('should apply node effects when leaving a node', () => {
      // Effects are applied when LEAVING a node, not when entering
      engine.makeChoice('go-right');
      // hasKey is not set yet - it's defined on the 'right' node's effect
      expect(engine.getState().variables['hasKey']).toBeUndefined();

      // When we leave the 'right' node, its effect is applied
      engine.makeChoice('back');
      expect(engine.getState().variables['hasKey']).toBe(true);
    });

    it('should set and get variables', () => {
      engine.setVariable('score', 100);
      expect(engine.getVariable<number>('score')).toBe(100);

      engine.setVariable('playerName', 'Hero');
      expect(engine.getVariable<string>('playerName')).toBe('Hero');

      engine.setVariable('isAlive', true);
      expect(engine.getVariable<boolean>('isAlive')).toBe(true);
    });

    it('should return undefined for missing variables', () => {
      expect(engine.getVariable('missing')).toBeUndefined();
    });
  });

  describe('endings', () => {
    it('should detect ending nodes', () => {
      engine.makeChoice('go-right'); // Get key
      engine.makeChoice('back');
      engine.makeChoice('secret'); // Go to victory ending

      expect(engine.isEnding()).toBe(true);
      expect(engine.getCurrentNode().endingType).toBe('victory');
    });

    it('should not be ending on regular nodes', () => {
      expect(engine.isEnding()).toBe(false);
    });
  });

  describe('subscription', () => {
    it('should notify subscribers on state change', () => {
      const callback = vi.fn();
      engine.subscribe(callback);

      engine.makeChoice('go-left');

      expect(callback).toHaveBeenCalledTimes(1);
      expect(callback).toHaveBeenCalledWith(expect.any(Object), expect.objectContaining({ id: 'left' }));
    });

    it('should allow unsubscribing', () => {
      const callback = vi.fn();
      const unsubscribe = engine.subscribe(callback);

      unsubscribe();
      engine.makeChoice('go-left');

      expect(callback).not.toHaveBeenCalled();
    });

    it('should notify on goBack', () => {
      engine.makeChoice('go-left');

      const callback = vi.fn();
      engine.subscribe(callback);

      engine.goBack();

      expect(callback).toHaveBeenCalledWith(expect.any(Object), expect.objectContaining({ id: 'start' }));
    });

    it('should notify on restart', () => {
      engine.makeChoice('go-left');

      const callback = vi.fn();
      engine.subscribe(callback);

      engine.restart();

      expect(callback).toHaveBeenCalledWith(expect.any(Object), expect.objectContaining({ id: 'start' }));
    });
  });

  describe('save and load', () => {
    it('should save game to localStorage', () => {
      engine.makeChoice('go-left');
      engine.save('test-slot');

      expect(localStorage.setItem).toHaveBeenCalled();
    });

    it('should load saved game', () => {
      engine.makeChoice('go-left');
      engine.makeChoice('back'); // This triggers left node's effect
      engine.save('test-slot');

      // Create new engine and load
      const newEngine = new StoryEngine(story);
      const loaded = newEngine.load('test-slot');

      expect(loaded).toBe(true);
      expect(newEngine.getCurrentNode().id).toBe('start');
      expect(newEngine.getState().variables['visited_left']).toBe(true);
    });

    it('should return false when loading non-existent save', () => {
      const loaded = engine.load('non-existent');
      expect(loaded).toBe(false);
    });

    it('should return false when loading save from different story', () => {
      engine.save('test-slot');

      const differentStory = { ...story, id: 'different-story' };
      const differentEngine = new StoryEngine(differentStory);
      const loaded = differentEngine.load('test-slot');

      expect(loaded).toBe(false);
    });
  });

  describe('hash export/import', () => {
    it('should export state to hash', () => {
      engine.makeChoice('go-left');
      const hash = engine.exportToHash();

      expect(hash).toBeTruthy();
      expect(typeof hash).toBe('string');
    });

    it('should import state from hash', () => {
      engine.makeChoice('go-right');
      const hash = engine.exportToHash();

      const newEngine = new StoryEngine(story);
      const imported = newEngine.importFromHash(hash);

      expect(imported).toBe(true);
      expect(newEngine.getCurrentNode().id).toBe('right');
      expect(newEngine.getState().history).toEqual(['start', 'right']);
    });

    it('should return false for invalid hash', () => {
      const imported = engine.importFromHash('invalid-hash');
      expect(imported).toBe(false);
    });

    it('should return false for hash from different story', () => {
      engine.makeChoice('go-left');
      const hash = engine.exportToHash();

      const differentStory = { ...story, id: 'different-story' };
      const differentEngine = new StoryEngine(differentStory);
      const imported = differentEngine.importFromHash(hash);

      expect(imported).toBe(false);
    });
  });

  describe('story info and progress', () => {
    it('should return story info', () => {
      const info = engine.getStoryInfo();
      expect(info).toEqual({
        id: 'test-story',
        title: 'Test Story',
        description: 'A test story for unit tests',
        theme: 'fantasy',
      });
    });

    it('should calculate progress', () => {
      // Initially visited 1 of 4 nodes
      expect(engine.getProgress()).toBe(25);

      // Visit another node
      engine.makeChoice('go-left');
      expect(engine.getProgress()).toBe(50);
    });
  });
});
