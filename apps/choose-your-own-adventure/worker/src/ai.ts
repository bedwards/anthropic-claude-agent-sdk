/**
 * Workers AI integration for story generation
 */

import { SAFETY_SYSTEM_PROMPT, validateUserInput } from './safety';
import type { StoryNode, Env } from './types';

const MODEL = '@cf/meta/llama-3-8b-instruct';

/**
 * Generate two story continuation options based on current node
 */
export async function generateOptions(
  ai: Ai,
  nodeTitle: string,
  nodeContent: string
): Promise<{ options: string[]; error?: string }> {
  const prompt = `Based on this story scene, generate exactly 2 possible next actions the reader could take. Each option should be a short phrase (5-10 words) that would lead to an interesting story branch.

CURRENT SCENE:
Title: ${nodeTitle}

${nodeContent}

Respond with ONLY the two options, one per line, no numbers or bullets:`;

  try {
    const response = await ai.run(MODEL, {
      messages: [
        { role: 'system', content: SAFETY_SYSTEM_PROMPT },
        { role: 'user', content: prompt },
      ],
      max_tokens: 100,
    });

    const text = (response as { response: string }).response || '';

    // Check for error responses from AI
    if (text.startsWith('ERROR:')) {
      return { options: [], error: text };
    }

    // Parse options (one per line)
    const options = text
      .split('\n')
      .map((line) => line.trim())
      .filter((line) => line.length > 0 && line.length < 100)
      .slice(0, 2);

    if (options.length < 2) {
      // Generate fallback options
      return {
        options: ['Continue exploring', 'Look for another path'],
      };
    }

    return { options };
  } catch (error) {
    console.error('AI generation error:', error);
    return {
      options: ['Continue exploring', 'Look for another path'],
      error: 'AI generation failed, using fallback options',
    };
  }
}

/**
 * Generate the next story node based on chosen option
 */
export async function generateStoryNode(
  ai: Ai,
  parentTitle: string,
  parentContent: string,
  chosenOption: string,
  nodeId: string,
  parentNodeId: string
): Promise<{ node: StoryNode; error?: string }> {
  // Validate user input first
  const validation = validateUserInput(chosenOption);
  if (!validation.valid) {
    return {
      node: createEmptyNode(nodeId, parentNodeId),
      error: validation.error,
    };
  }

  const prompt = `Continue this adventure story based on the reader's choice.

PREVIOUS SCENE:
Title: ${parentTitle}

${parentContent}

THE READER CHOSE: "${chosenOption}"

Write the next scene (150-250 words). Include:
1. A short, evocative title (3-6 words)
2. A one-sentence tagline summarizing this scene
3. The story content with vivid details and atmosphere

Format your response EXACTLY like this:
TITLE: [Your title here]
TAGLINE: [Your one-sentence tagline]
CONTENT:
[Your story content here]`;

  try {
    const response = await ai.run(MODEL, {
      messages: [
        { role: 'system', content: SAFETY_SYSTEM_PROMPT },
        { role: 'user', content: prompt },
      ],
      max_tokens: 500,
    });

    const text = (response as { response: string }).response || '';

    // Check for error responses from AI
    if (text.startsWith('ERROR:')) {
      return {
        node: createEmptyNode(nodeId, parentNodeId),
        error: text,
      };
    }

    // Parse the response
    const titleMatch = text.match(/TITLE:\s*(.+)/i);
    const taglineMatch = text.match(/TAGLINE:\s*(.+)/i);
    const contentMatch = text.match(/CONTENT:\s*([\s\S]+)/i);

    const title = titleMatch?.[1]?.trim() || 'The Journey Continues';
    const tagline = taglineMatch?.[1]?.trim() || chosenOption;
    const content = contentMatch?.[1]?.trim() || text;

    const node: StoryNode = {
      id: nodeId,
      title,
      content,
      tagline,
      parentNodeId,
      childNodeIds: [],
      generatedOptions: [],
      chosenOption,
      createdAt: Date.now(),
    };

    return { node };
  } catch (error) {
    console.error('AI story generation error:', error);
    return {
      node: createEmptyNode(nodeId, parentNodeId),
      error: 'Failed to generate story. Please try again.',
    };
  }
}

function createEmptyNode(nodeId: string, parentNodeId: string): StoryNode {
  return {
    id: nodeId,
    title: 'Error',
    content: '',
    tagline: '',
    parentNodeId,
    childNodeIds: [],
    generatedOptions: [],
    chosenOption: null,
    createdAt: Date.now(),
  };
}
