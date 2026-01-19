/**
 * API client for the CYOA Worker
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

export interface StoryData {
  meta: StoryMeta;
  nodes: StoryNode[];
}

// Worker API URL - update for production
const API_BASE = import.meta.env.DEV
  ? 'http://localhost:8787'
  : 'https://cyoa-worker.brian-mabry-edwards.workers.dev';

export class ApiClient {
  /**
   * Fetch full story data
   */
  async getStory(storyId: string): Promise<StoryData> {
    const response = await fetch(`${API_BASE}/api/story/${storyId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch story: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Get a specific node
   */
  async getNode(storyId: string, nodeId: string): Promise<StoryNode> {
    const response = await fetch(`${API_BASE}/api/node/${storyId}/${nodeId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch node: ${response.statusText}`);
    }
    const data = await response.json();
    return data.node;
  }

  /**
   * Generate AI options for a node
   */
  async generateOptions(
    storyId: string,
    nodeId: string
  ): Promise<{ options: string[]; error?: string }> {
    const response = await fetch(`${API_BASE}/api/generate-options`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ storyId, nodeId }),
    });
    if (!response.ok) {
      throw new Error(`Failed to generate options: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Continue story with chosen option
   */
  async continueStory(
    storyId: string,
    parentNodeId: string,
    chosenOption: string
  ): Promise<{ node: StoryNode; error?: string }> {
    const response = await fetch(`${API_BASE}/api/continue-story`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ storyId, parentNodeId, chosenOption }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || `Failed to continue story: ${response.statusText}`);
    }
    return response.json();
  }
}

export const api = new ApiClient();
