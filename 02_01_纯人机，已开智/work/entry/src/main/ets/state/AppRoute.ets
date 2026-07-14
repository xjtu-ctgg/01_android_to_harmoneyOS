export const ROUTE_FEED: string = 'home/feed';
export const ROUTE_SEARCH: string = 'home/search';
export const ROUTE_CART: string = 'home/cart';
export const ROUTE_PROFILE: string = 'home/profile';
export const ROUTE_DETAIL: string = 'snack/{snackId}?origin={origin}';
export const ROUTE_FILTER: string = 'overlay/filter';

const TAB_ROUTES: string[] = [
  ROUTE_FEED,
  ROUTE_SEARCH,
  ROUTE_CART,
  ROUTE_PROFILE
];

export function isTabRoute(route: string): boolean {
  return TAB_ROUTES.includes(route);
}
