/**
 * Story registry - all available stories
 */

import type { Story } from '../engine/types';
import { dragonsCave } from './dragonsCave';

export const stories: Record<string, Story> = {
  'dragons-cave': dragonsCave,
};

export const storyList = Object.values(stories);

export function getStory(id: string): Story | undefined {
  return stories[id];
}
