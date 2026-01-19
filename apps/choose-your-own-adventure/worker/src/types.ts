/**
 * Shared types for the CYOA Worker
 */

export interface StoryNode {
  id: string;
  title: string;
  content: string;
  tagline: string;
  parentNodeId: string | null;
  childNodeIds: string[];
  generatedOptions: string[];
  chosenOption: string | null;
  createdAt: number;
}

export interface StoryMeta {
  id: string;
  title: string;
  description: string;
  theme: string;
  startNodeId: string;
  createdAt: number;
}

export interface GenerateOptionsRequest {
  storyId: string;
  nodeId: string;
  nodeContent: string;
  nodeTitle: string;
}

export interface GenerateOptionsResponse {
  options: string[];
  error?: string;
}

export interface ContinueStoryRequest {
  storyId: string;
  parentNodeId: string;
  chosenOption: string;
  parentContent: string;
  parentTitle: string;
}

export interface ContinueStoryResponse {
  node: StoryNode;
  error?: string;
}

export interface Env {
  AI: Ai;
  GITHUB_TOKEN: string;
  GITHUB_REPO: string;
  STORIES_PATH: string;
}
