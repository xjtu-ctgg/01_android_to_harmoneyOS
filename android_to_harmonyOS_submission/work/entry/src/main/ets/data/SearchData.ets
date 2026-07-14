import type { Snack } from '../model/Snack';
import { SNACKS } from './SnackData';

export interface SearchGroup {
  name: string;
  items: string[];
}

export interface SearchCategoryVisual {
  name: string;
  imageResource: Resource;
}

export const SEARCH_STATES: string[] = [
  'Categories',
  'Suggestions',
  'Results',
  'NoResults'
];

export const SEARCH_DELAY_MS: number = 200;
export const SEARCH_MATCH_RULE: string = 'case-insensitive contains';

export const SEARCH_CATEGORY_GROUPS: SearchGroup[] = [
  {
    name: 'Categories',
    items: ['Chips & crackers', 'Fruit snacks', 'Desserts', 'Nuts']
  },
  {
    name: 'Lifestyles',
    items: ['Organic', 'Gluten Free', 'Paleo', 'Vegan', 'Vegetarian', 'Whole30']
  }
];

export const SEARCH_SUGGESTION_GROUPS: SearchGroup[] = [
  {
    name: 'Recent searches',
    items: ['Cheese', 'Apple Sauce']
  },
  {
    name: 'Popular searches',
    items: ['Organic', 'Gluten Free', 'Paleo', 'Vegan', 'Vegitarian', 'Whole30']
  }
];

export const SEARCH_CATEGORY_VISUALS: SearchCategoryVisual[] = [
  { name: 'Chips & crackers', imageResource: $r('app.media.chips') },
  { name: 'Fruit snacks', imageResource: $r('app.media.fruit') },
  { name: 'Desserts', imageResource: $r('app.media.desserts') },
  { name: 'Nuts', imageResource: $r('app.media.nuts') },
  { name: 'Organic', imageResource: $r('app.media.organic') },
  { name: 'Gluten Free', imageResource: $r('app.media.gluten_free') },
  { name: 'Paleo', imageResource: $r('app.media.paleo') },
  { name: 'Vegan', imageResource: $r('app.media.vegan') },
  { name: 'Vegetarian', imageResource: $r('app.media.organic') },
  { name: 'Whole30', imageResource: $r('app.media.paleo') }
];

export function searchSnacks(query: string): Snack[] {
  const normalizedQuery: string = query.toLowerCase();
  return SNACKS.filter((snack: Snack): boolean =>
    snack.name.toLowerCase().includes(normalizedQuery));
}
