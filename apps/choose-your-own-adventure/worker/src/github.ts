/**
 * GitHub API integration for storing story nodes
 */

import type { StoryNode, StoryMeta, Env } from './types';

const GITHUB_API = 'https://api.github.com';

interface GitHubFile {
  content: string;
  sha?: string;
}

/**
 * Get a file from the repository
 */
export async function getFile(
  env: Env,
  path: string
): Promise<GitHubFile | null> {
  const url = `${GITHUB_API}/repos/${env.GITHUB_REPO}/contents/${path}`;

  try {
    const response = await fetch(url, {
      headers: {
        Authorization: `Bearer ${env.GITHUB_TOKEN}`,
        Accept: 'application/vnd.github.v3+json',
        'User-Agent': 'CYOA-Worker',
      },
    });

    if (response.status === 404) {
      return null;
    }

    if (!response.ok) {
      throw new Error(`GitHub API error: ${response.status}`);
    }

    const data = (await response.json()) as { content: string; sha: string };
    const content = atob(data.content.replace(/\n/g, ''));

    return { content, sha: data.sha };
  } catch (error) {
    console.error('GitHub getFile error:', error);
    return null;
  }
}

/**
 * Create or update a file in the repository
 */
export async function putFile(
  env: Env,
  path: string,
  content: string,
  message: string,
  sha?: string
): Promise<boolean> {
  const url = `${GITHUB_API}/repos/${env.GITHUB_REPO}/contents/${path}`;

  const body: Record<string, string> = {
    message,
    content: btoa(content),
    branch: 'main',
  };

  if (sha) {
    body.sha = sha;
  }

  try {
    const response = await fetch(url, {
      method: 'PUT',
      headers: {
        Authorization: `Bearer ${env.GITHUB_TOKEN}`,
        Accept: 'application/vnd.github.v3+json',
        'User-Agent': 'CYOA-Worker',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response.text();
      console.error('GitHub putFile error:', error);
      return false;
    }

    return true;
  } catch (error) {
    console.error('GitHub putFile error:', error);
    return false;
  }
}

/**
 * Get story metadata
 */
export async function getStoryMeta(
  env: Env,
  storyId: string
): Promise<StoryMeta | null> {
  const path = `${env.STORIES_PATH}/${storyId}/meta.json`;
  const file = await getFile(env, path);

  if (!file) {
    return null;
  }

  try {
    return JSON.parse(file.content) as StoryMeta;
  } catch {
    return null;
  }
}

/**
 * Get a story node
 */
export async function getStoryNode(
  env: Env,
  storyId: string,
  nodeId: string
): Promise<StoryNode | null> {
  const path = `${env.STORIES_PATH}/${storyId}/nodes/${nodeId}.json`;
  const file = await getFile(env, path);

  if (!file) {
    return null;
  }

  try {
    return JSON.parse(file.content) as StoryNode;
  } catch {
    return null;
  }
}

/**
 * Save a story node and update parent's childNodeIds
 */
export async function saveStoryNode(
  env: Env,
  storyId: string,
  node: StoryNode
): Promise<boolean> {
  const nodePath = `${env.STORIES_PATH}/${storyId}/nodes/${node.id}.json`;

  // Save the new node
  const nodeContent = JSON.stringify(node, null, 2);
  const saved = await putFile(
    env,
    nodePath,
    nodeContent,
    `Add story node: ${node.title}`
  );

  if (!saved) {
    return false;
  }

  // Update parent node's childNodeIds
  if (node.parentNodeId) {
    const parentPath = `${env.STORIES_PATH}/${storyId}/nodes/${node.parentNodeId}.json`;
    const parentFile = await getFile(env, parentPath);

    if (parentFile) {
      try {
        const parent = JSON.parse(parentFile.content) as StoryNode;
        if (!parent.childNodeIds.includes(node.id)) {
          parent.childNodeIds.push(node.id);
          const parentContent = JSON.stringify(parent, null, 2);
          await putFile(
            env,
            parentPath,
            parentContent,
            `Update parent node: add child ${node.id}`,
            parentFile.sha
          );
        }
      } catch (error) {
        console.error('Error updating parent node:', error);
      }
    }
  }

  return true;
}

/**
 * Get all nodes for a story
 */
export async function getAllStoryNodes(
  env: Env,
  storyId: string
): Promise<StoryNode[]> {
  const path = `${env.STORIES_PATH}/${storyId}/nodes`;
  const url = `${GITHUB_API}/repos/${env.GITHUB_REPO}/contents/${path}`;

  try {
    const response = await fetch(url, {
      headers: {
        Authorization: `Bearer ${env.GITHUB_TOKEN}`,
        Accept: 'application/vnd.github.v3+json',
        'User-Agent': 'CYOA-Worker',
      },
    });

    if (!response.ok) {
      return [];
    }

    const files = (await response.json()) as Array<{ name: string }>;
    const nodes: StoryNode[] = [];

    for (const file of files) {
      if (file.name.endsWith('.json')) {
        const nodeId = file.name.replace('.json', '');
        const node = await getStoryNode(env, storyId, nodeId);
        if (node) {
          nodes.push(node);
        }
      }
    }

    return nodes;
  } catch (error) {
    console.error('Error getting all nodes:', error);
    return [];
  }
}

/**
 * Initialize a new story with a starting node
 */
export async function initializeStory(
  env: Env,
  storyId: string,
  title: string,
  description: string,
  startingContent: string
): Promise<boolean> {
  const meta: StoryMeta = {
    id: storyId,
    title,
    description,
    theme: 'fantasy',
    startNodeId: 'start',
    createdAt: Date.now(),
  };

  const startNode: StoryNode = {
    id: 'start',
    title,
    content: startingContent,
    tagline: description,
    parentNodeId: null,
    childNodeIds: [],
    generatedOptions: [],
    chosenOption: null,
    createdAt: Date.now(),
  };

  // Save meta
  const metaPath = `${env.STORIES_PATH}/${storyId}/meta.json`;
  const metaSaved = await putFile(
    env,
    metaPath,
    JSON.stringify(meta, null, 2),
    `Initialize story: ${title}`
  );

  if (!metaSaved) {
    return false;
  }

  // Save start node
  const nodePath = `${env.STORIES_PATH}/${storyId}/nodes/start.json`;
  const nodeSaved = await putFile(
    env,
    nodePath,
    JSON.stringify(startNode, null, 2),
    `Add starting node for: ${title}`
  );

  return nodeSaved;
}
