import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { ApiClient } from './client';

describe('ApiClient', () => {
  let client: ApiClient;
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    client = new ApiClient();
    fetchMock = vi.fn();
    global.fetch = fetchMock;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('getStories', () => {
    it('should fetch all available stories', async () => {
      const mockStories = [
        {
          id: 'dragon-adventure',
          title: 'The Dragon\'s Cave',
          description: 'A brave adventurer seeks treasure',
          theme: 'fantasy',
          startNodeId: 'start',
          createdAt: 1737312000000,
        },
        {
          id: 'space-odyssey',
          title: 'Space Odyssey',
          description: 'Navigate deep space dangers',
          theme: 'sci-fi',
          startNodeId: 'start',
          createdAt: 1737312100000,
        },
      ];

      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ stories: mockStories }),
      });

      const stories = await client.getStories();

      expect(stories).toEqual(mockStories);
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/api/stories')
      );
    });

    it('should throw error when fetch fails', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: false,
        statusText: 'Not Found',
      });

      await expect(client.getStories()).rejects.toThrow(
        'Failed to fetch stories: Not Found'
      );
    });
  });

  describe('getStory', () => {
    it('should fetch a specific story with all nodes', async () => {
      const mockStoryData = {
        meta: {
          id: 'dragon-adventure',
          title: 'The Dragon\'s Cave',
          description: 'A brave adventurer seeks treasure',
          theme: 'fantasy',
          startNodeId: 'start',
          createdAt: 1737312000000,
        },
        nodes: [
          {
            id: 'start',
            title: 'The Cave Entrance',
            content: 'You stand before a dark cave...',
            tagline: 'Your adventure begins',
            parentNodeId: null,
            childNodeIds: [],
            generatedOptions: [],
            chosenOption: null,
            createdAt: 1737312000000,
          },
        ],
      };

      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => mockStoryData,
      });

      const story = await client.getStory('dragon-adventure');

      expect(story).toEqual(mockStoryData);
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/api/story/dragon-adventure')
      );
    });
  });

  describe('generateOptions', () => {
    it('should generate AI options for a node', async () => {
      const mockResponse = {
        options: [
          'Enter the cave cautiously',
          'Call out to see if anyone is inside',
          'Look for another entrance',
        ],
      };

      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await client.generateOptions('dragon-adventure', 'start');

      expect(result.options).toHaveLength(3);
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/api/generate-options'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ storyId: 'dragon-adventure', nodeId: 'start' }),
        })
      );
    });
  });

  describe('continueStory', () => {
    it('should create a new story node based on choice', async () => {
      const mockResponse = {
        node: {
          id: 'node-123',
          title: 'Inside the Cave',
          content: 'You step into the darkness...',
          tagline: 'A brave choice',
          parentNodeId: 'start',
          childNodeIds: [],
          generatedOptions: [],
          chosenOption: 'Enter the cave cautiously',
          createdAt: 1737312100000,
        },
      };

      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await client.continueStory(
        'dragon-adventure',
        'start',
        'Enter the cave cautiously'
      );

      expect(result.node.title).toBe('Inside the Cave');
      expect(result.node.chosenOption).toBe('Enter the cave cautiously');
    });

    it('should throw error with message from server', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: false,
        json: async () => ({ error: 'Safety check failed' }),
      });

      await expect(
        client.continueStory('dragon-adventure', 'start', 'Burn everything')
      ).rejects.toThrow('Safety check failed');
    });
  });
});
