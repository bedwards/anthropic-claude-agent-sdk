/**
 * CYOA Worker - API for AI-generated story branches
 */

import { generateOptions, generateStoryNode } from './ai';
import {
  getStoryMeta,
  getStoryNode,
  saveStoryNode,
  getAllStoryNodes,
  initializeStory,
} from './github';
import type {
  Env,
  GenerateOptionsRequest,
  GenerateOptionsResponse,
  ContinueStoryRequest,
  ContinueStoryResponse,
  StoryNode,
} from './types';

// Simple rate limiting (in production, use Durable Objects or KV)
const requestCounts = new Map<string, { count: number; resetAt: number }>();
const RATE_LIMIT = 20; // requests per minute
const RATE_WINDOW = 60000; // 1 minute

function checkRateLimit(ip: string): boolean {
  const now = Date.now();
  const record = requestCounts.get(ip);

  if (!record || now > record.resetAt) {
    requestCounts.set(ip, { count: 1, resetAt: now + RATE_WINDOW });
    return true;
  }

  if (record.count >= RATE_LIMIT) {
    return false;
  }

  record.count++;
  return true;
}

function generateNodeId(): string {
  return `node-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function corsHeaders(): HeadersInit {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };
}

function jsonResponse(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json',
      ...corsHeaders(),
    },
  });
}

function errorResponse(message: string, status = 400): Response {
  return jsonResponse({ error: message }, status);
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders() });
    }

    const url = new URL(request.url);
    const path = url.pathname;

    // Rate limiting
    const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
    if (!checkRateLimit(ip)) {
      return errorResponse('Rate limit exceeded. Please wait a moment.', 429);
    }

    try {
      // Health check
      if (path === '/api/health') {
        return jsonResponse({ status: 'ok', timestamp: Date.now() });
      }

      // Get story metadata and all nodes
      if (path.startsWith('/api/story/') && request.method === 'GET') {
        const storyId = path.split('/')[3];
        if (!storyId) {
          return errorResponse('Story ID required');
        }

        const meta = await getStoryMeta(env, storyId);
        if (!meta) {
          return errorResponse('Story not found', 404);
        }

        const nodes = await getAllStoryNodes(env, storyId);

        return jsonResponse({ meta, nodes });
      }

      // Get specific node
      if (path.startsWith('/api/node/') && request.method === 'GET') {
        const parts = path.split('/');
        const storyId = parts[3];
        const nodeId = parts[4];

        if (!storyId || !nodeId) {
          return errorResponse('Story ID and Node ID required');
        }

        const node = await getStoryNode(env, storyId, nodeId);
        if (!node) {
          return errorResponse('Node not found', 404);
        }

        return jsonResponse({ node });
      }

      // Generate options for a node
      if (path === '/api/generate-options' && request.method === 'POST') {
        const body = (await request.json()) as GenerateOptionsRequest;

        if (!body.storyId || !body.nodeId) {
          return errorResponse('storyId and nodeId required');
        }

        // Get the node content if not provided
        let nodeContent = body.nodeContent;
        let nodeTitle = body.nodeTitle;

        if (!nodeContent || !nodeTitle) {
          const node = await getStoryNode(env, body.storyId, body.nodeId);
          if (!node) {
            return errorResponse('Node not found', 404);
          }
          nodeContent = node.content;
          nodeTitle = node.title;
        }

        const result = await generateOptions(env.AI, nodeTitle, nodeContent);

        // Cache the generated options on the node
        if (result.options.length > 0) {
          const node = await getStoryNode(env, body.storyId, body.nodeId);
          if (node && node.generatedOptions.length === 0) {
            node.generatedOptions = result.options;
            await saveStoryNode(env, body.storyId, node);
          }
        }

        const response: GenerateOptionsResponse = {
          options: result.options,
          error: result.error,
        };

        return jsonResponse(response);
      }

      // Continue story with chosen option
      if (path === '/api/continue-story' && request.method === 'POST') {
        const body = (await request.json()) as ContinueStoryRequest;

        if (!body.storyId || !body.parentNodeId || !body.chosenOption) {
          return errorResponse('storyId, parentNodeId, and chosenOption required');
        }

        // Get parent node if content not provided
        let parentContent = body.parentContent;
        let parentTitle = body.parentTitle;

        if (!parentContent || !parentTitle) {
          const parent = await getStoryNode(env, body.storyId, body.parentNodeId);
          if (!parent) {
            return errorResponse('Parent node not found', 404);
          }
          parentContent = parent.content;
          parentTitle = parent.title;
        }

        // Check if this choice already exists
        const parentNode = await getStoryNode(env, body.storyId, body.parentNodeId);
        if (parentNode) {
          for (const childId of parentNode.childNodeIds) {
            const child = await getStoryNode(env, body.storyId, childId);
            if (child && child.chosenOption === body.chosenOption) {
              // Return existing node
              const response: ContinueStoryResponse = { node: child };
              return jsonResponse(response);
            }
          }
        }

        // Generate new node
        const nodeId = generateNodeId();
        const result = await generateStoryNode(
          env.AI,
          parentTitle,
          parentContent,
          body.chosenOption,
          nodeId,
          body.parentNodeId
        );

        if (result.error && !result.node.content) {
          return errorResponse(result.error);
        }

        // Save to GitHub
        const saved = await saveStoryNode(env, body.storyId, result.node);
        if (!saved) {
          return errorResponse('Failed to save story node');
        }

        const response: ContinueStoryResponse = {
          node: result.node,
          error: result.error,
        };

        return jsonResponse(response);
      }

      // Initialize a new story (admin endpoint)
      if (path === '/api/init-story' && request.method === 'POST') {
        const body = (await request.json()) as {
          storyId: string;
          title: string;
          description: string;
          startingContent: string;
        };

        if (!body.storyId || !body.title || !body.startingContent) {
          return errorResponse('storyId, title, and startingContent required');
        }

        const success = await initializeStory(
          env,
          body.storyId,
          body.title,
          body.description || body.title,
          body.startingContent
        );

        if (!success) {
          return errorResponse('Failed to initialize story');
        }

        return jsonResponse({ success: true, storyId: body.storyId });
      }

      return errorResponse('Not found', 404);
    } catch (error) {
      console.error('Worker error:', error);
      return errorResponse('Internal server error', 500);
    }
  },
};
