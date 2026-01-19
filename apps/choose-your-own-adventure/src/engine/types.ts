/**
 * Core types for the story engine
 */

export interface Choice {
  id: string;
  text: string;
  nextNodeId: string;
  condition?: (state: GameState) => boolean;
}

export interface StoryNode {
  id: string;
  title: string;
  content: string;
  choices: Choice[];
  isEnding?: boolean;
  endingType?: 'victory' | 'defeat' | 'neutral';
  effect?: (state: GameState) => GameState;
  image?: string;
}

export interface Story {
  id: string;
  title: string;
  description: string;
  theme: 'fantasy' | 'sci-fi' | 'mystery' | 'horror';
  startNodeId: string;
  nodes: Record<string, StoryNode>;
}

export interface GameState {
  storyId: string;
  currentNodeId: string;
  history: string[];
  variables: Record<string, string | number | boolean>;
  startedAt: number;
  lastUpdated: number;
}

export interface SavedGame {
  state: GameState;
  storyTitle: string;
  savedAt: number;
}
