export interface Snack {
  stableId: number;
  name: string;
  imageResource: Resource;
  priceCents: number;
  tagline: string;
}

export enum CollectionType {
  NORMAL = 'Normal',
  HIGHLIGHT = 'Highlight'
}

export interface SnackCollection {
  stableId: number;
  name: string;
  type: CollectionType;
  snackStableIds: number[];
}
