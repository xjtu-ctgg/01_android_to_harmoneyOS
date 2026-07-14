import { createOrderLine } from '../model/OrderLine';
import type { OrderLine } from '../model/OrderLine';
import { CollectionType } from '../model/Snack';
import type { Snack, SnackCollection } from '../model/Snack';

export const SNACKS: Snack[] = [
  {
    stableId: 1,
    name: 'Cupcake',
    imageResource: $r('app.media.cupcake'),
    priceCents: 299,
    tagline: 'A tag line'
  },
  {
    stableId: 2,
    name: 'Donut',
    imageResource: $r('app.media.donut'),
    priceCents: 299,
    tagline: 'A tag line'
  },
  {
    stableId: 3,
    name: 'Eclair',
    imageResource: $r('app.media.eclair'),
    priceCents: 299,
    tagline: 'A tag line'
  },
  {
    stableId: 4,
    name: 'Froyo',
    imageResource: $r('app.media.froyo'),
    priceCents: 299,
    tagline: 'A tag line'
  },
  {
    stableId: 5,
    name: 'Gingerbread',
    imageResource: $r('app.media.gingerbread'),
    priceCents: 499,
    tagline: 'A tag line'
  },
  {
    stableId: 6,
    name: 'Honeycomb',
    imageResource: $r('app.media.honeycomb'),
    priceCents: 299,
    tagline: 'A tag line'
  },
  {
    stableId: 7,
    name: 'Ice Cream Sandwich',
    imageResource: $r('app.media.ice_cream_sandwich'),
    priceCents: 1299,
    tagline: 'A tag line'
  },
  {
    stableId: 8,
    name: 'Jellybean',
    imageResource: $r('app.media.jelly_bean'),
    priceCents: 299,
    tagline: 'A tag line'
  },
  {
    stableId: 9,
    name: 'KitKat',
    imageResource: $r('app.media.kitkat'),
    priceCents: 549,
    tagline: 'A tag line'
  },
  {
    stableId: 10,
    name: 'Lollipop',
    imageResource: $r('app.media.lollipop'),
    priceCents: 299,
    tagline: 'A tag line'
  },
  {
    stableId: 11,
    name: 'Marshmallow',
    imageResource: $r('app.media.marshmallow'),
    priceCents: 299,
    tagline: 'A tag line'
  },
  {
    stableId: 12,
    name: 'Nougat',
    imageResource: $r('app.media.nougat'),
    priceCents: 299,
    tagline: 'A tag line'
  },
  {
    stableId: 13,
    name: 'Oreo',
    imageResource: $r('app.media.oreo'),
    priceCents: 299,
    tagline: 'A tag line'
  },
  {
    stableId: 14,
    name: 'Pie',
    imageResource: $r('app.media.pie'),
    priceCents: 299,
    tagline: 'A tag line'
  },
  {
    stableId: 15,
    name: 'Chips',
    imageResource: $r('app.media.chips'),
    priceCents: 299,
    tagline: ''
  },
  {
    stableId: 16,
    name: 'Pretzels',
    imageResource: $r('app.media.pretzels'),
    priceCents: 299,
    tagline: ''
  },
  {
    stableId: 17,
    name: 'Smoothies',
    imageResource: $r('app.media.smoothies'),
    priceCents: 299,
    tagline: ''
  },
  {
    stableId: 18,
    name: 'Popcorn',
    imageResource: $r('app.media.popcorn'),
    priceCents: 299,
    tagline: ''
  },
  {
    stableId: 19,
    name: 'Almonds',
    imageResource: $r('app.media.almonds'),
    priceCents: 299,
    tagline: ''
  },
  {
    stableId: 20,
    name: 'Cheese',
    imageResource: $r('app.media.cheese'),
    priceCents: 299,
    tagline: ''
  },
  {
    stableId: 21,
    name: 'Apples',
    imageResource: $r('app.media.apples'),
    priceCents: 299,
    tagline: 'A tag line'
  },
  {
    stableId: 22,
    name: 'Apple sauce',
    imageResource: $r('app.media.apple_sauce'),
    priceCents: 299,
    tagline: 'A tag line'
  },
  {
    stableId: 23,
    name: 'Apple chips',
    imageResource: $r('app.media.apple_chips'),
    priceCents: 299,
    tagline: 'A tag line'
  },
  {
    stableId: 24,
    name: 'Apple juice',
    imageResource: $r('app.media.apple_juice'),
    priceCents: 299,
    tagline: 'A tag line'
  },
  {
    stableId: 25,
    name: 'Apple pie',
    imageResource: $r('app.media.apple_pie'),
    priceCents: 299,
    tagline: 'A tag line'
  },
  {
    stableId: 26,
    name: 'Grapes',
    imageResource: $r('app.media.grapes'),
    priceCents: 299,
    tagline: 'A tag line'
  },
  {
    stableId: 27,
    name: 'Kiwi',
    imageResource: $r('app.media.kiwi'),
    priceCents: 299,
    tagline: 'A tag line'
  },
  {
    stableId: 28,
    name: 'Mango',
    imageResource: $r('app.media.mango'),
    priceCents: 299,
    tagline: 'A tag line'
  }
];

export const SNACK_COLLECTIONS: SnackCollection[] = [
  {
    stableId: 1,
    name: 'Android\'s picks',
    type: CollectionType.HIGHLIGHT,
    snackStableIds: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
  },
  {
    stableId: 2,
    name: 'Popular on Jetsnack',
    type: CollectionType.NORMAL,
    snackStableIds: [15, 16, 17, 18, 19]
  },
  {
    stableId: 3,
    name: 'WFH favourites',
    type: CollectionType.HIGHLIGHT,
    snackStableIds: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
  },
  {
    stableId: 4,
    name: 'Newly Added',
    type: CollectionType.NORMAL,
    snackStableIds: [15, 16, 17, 18, 19]
  },
  {
    stableId: 5,
    name: 'Only on Jetsnack',
    type: CollectionType.HIGHLIGHT,
    snackStableIds: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
  }
];

export const RELATED_COLLECTIONS: SnackCollection[] = [
  {
    stableId: 6,
    name: 'Customers also bought',
    type: CollectionType.NORMAL,
    snackStableIds: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
  },
  {
    stableId: 7,
    name: 'Popular on Jetsnack',
    type: CollectionType.NORMAL,
    snackStableIds: [15, 16, 17, 18, 19]
  }
];

export const INSPIRED_BY_CART_COLLECTION: SnackCollection = {
  stableId: 8,
  name: 'Inspired by your cart',
  type: CollectionType.NORMAL,
  snackStableIds: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
};

export const INITIAL_CART_LINES: OrderLine[] = [
  {
    snackStableId: 5,
    quantity: 2
  },
  {
    snackStableId: 7,
    quantity: 3
  },
  {
    snackStableId: 9,
    quantity: 1
  }
];

export const SHIPPING_CENTS: number = 369;
export const QUANTITY_FAILURE_INTERVAL: number = 5;
export const DECREMENT_AT_ONE_REMOVES: boolean = true;
export const ORDER_HEADER_COUNTS_LINES_NOT_UNITS: boolean = true;

export function createInitialCartLines(): OrderLine[] {
  return INITIAL_CART_LINES.map((line: OrderLine): OrderLine =>
    createOrderLine(line.snackStableId, line.quantity));
}

export function getSnackById(stableId: number): Snack | undefined {
  return SNACKS.find((snack: Snack): boolean => snack.stableId === stableId);
}

export function getSnacksByStableIds(stableIds: number[]): Snack[] {
  const selected: Snack[] = [];
  stableIds.forEach((stableId: number): void => {
    const snack: Snack | undefined = getSnackById(stableId);
    if (snack !== undefined) {
      selected.push(snack);
    }
  });
  return selected;
}
