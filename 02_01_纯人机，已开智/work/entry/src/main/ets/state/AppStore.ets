import { SEARCH_DELAY_MS, searchSnacks } from '../data/SearchData';
import {
  createInitialCartLines,
  getSnackById,
  QUANTITY_FAILURE_INTERVAL,
  SHIPPING_CENTS
} from '../data/SnackData';
import { createOrderLine } from '../model/OrderLine';
import type { OrderLine } from '../model/OrderLine';
import type { Snack } from '../model/Snack';
import { isTabRoute, ROUTE_DETAIL, ROUTE_FEED, ROUTE_SEARCH } from './AppRoute';

const NO_DETAIL_ORIGIN: string = '';
const DEFAULT_FILTER_SORT: string = 'Android\'s favorite (default)';
const CART_SNACKBAR_DURATION_MS: number = 4000;

export enum SearchDisplay {
  CATEGORIES = 'Categories',
  SUGGESTIONS = 'Suggestions',
  RESULTS = 'Results',
  NO_RESULTS = 'NoResults'
}

@Observed
export class AppStore {
  currentRoute: string = ROUTE_FEED;
  selectedSnackId: number | undefined = undefined;
  detailOrigin: string = NO_DETAIL_ORIGIN;
  detailReturnRoute: string = ROUTE_FEED;
  filterVisible: boolean = false;
  searchQuery: string = '';
  searchFocused: boolean = false;
  searching: boolean = false;
  searchResults: Snack[] = [];
  private searchGeneration: number = 0;
  private searchCategoryActionCount: number = 0;
  private searchAddActionCount: number = 0;
  cartLines: OrderLine[] = createInitialCartLines();
  private cartRequestCount: number = 0;
  cartSnackbarMessage: Resource = $r('app.string.cart_increase_error');
  cartSnackbarVisible: boolean = false;
  private cartSnackbarGeneration: number = 0;
  private cartSnackbarQueue: Resource[] = [];
  hiddenCartIds: number[] = [];
  private checkoutActionCount: number = 0;
  detailQuantity: number = 1;
  detailExpanded: boolean = false;
  private detailAddActionCount: number = 0;
  private detailRelatedActionCount: number = 0;
  filterSort: string = DEFAULT_FILTER_SORT;
  filterMaxCalories: number = 0;
  filterSelections: string[] = [];
  quickFilterSelections: string[] = [];
  private filterResetActionCount: number = 0;
  private filterApplyActionCount: number = 0;

  selectTab(route: string): void {
    if (!isTabRoute(route)) {
      return;
    }
    if (this.currentRoute === route) {
      return;
    }
    if (this.currentRoute === ROUTE_SEARCH && route !== ROUTE_SEARCH) {
      this.resetSearchState();
    }
    this.currentRoute = route;
    this.selectedSnackId = undefined;
    this.filterVisible = false;
  }

  getSearchDisplay(): SearchDisplay {
    if (!this.searchFocused && this.searchQuery.length === 0) {
      return SearchDisplay.CATEGORIES;
    }
    if (this.searchFocused && this.searchQuery.length === 0) {
      return SearchDisplay.SUGGESTIONS;
    }
    if (this.searchResults.length === 0) {
      return SearchDisplay.NO_RESULTS;
    }
    return SearchDisplay.RESULTS;
  }

  resetSearchState(): void {
    this.searchGeneration += 1;
    this.searchQuery = '';
    this.searchFocused = false;
    this.searching = false;
    this.searchResults = [];
  }

  resetDetailTransientState(): void {
    this.detailQuantity = 1;
    this.detailExpanded = false;
  }

  setSearchFocused(focused: boolean): void {
    this.searchFocused = focused;
  }

  setSearchQuery(query: string): void {
    this.searchQuery = query;
    this.searchGeneration += 1;
    const generation: number = this.searchGeneration;
    this.searching = true;
    setTimeout(() => {
      if (generation !== this.searchGeneration) {
        return;
      }
      this.searchResults = searchSnacks(query);
      this.searching = false;
    }, SEARCH_DELAY_MS);
  }

  refreshSearchResults(): void {
    this.setSearchQuery(this.searchQuery);
  }

  clearSearchQuery(): void {
    this.setSearchQuery('');
  }

  selectSearchSuggestion(suggestion: string): void {
    this.setSearchQuery(suggestion);
  }

  acknowledgeSearchCategory(): void {
    this.searchCategoryActionCount += 1;
  }

  acknowledgeSearchResultAdd(): void {
    this.searchAddActionCount += 1;
  }

  private shouldCartRequestFail(): boolean {
    this.cartRequestCount += 1;
    return this.cartRequestCount % QUANTITY_FAILURE_INTERVAL === 0;
  }

  private showCartSnackbar(message: Resource): void {
    const pending: Resource[] = this.cartSnackbarQueue.slice();
    pending.push(message);
    this.cartSnackbarQueue = pending;
    if (!this.cartSnackbarVisible) {
      this.showNextCartSnackbar();
    }
  }

  private showNextCartSnackbar(): void {
    const message: Resource | undefined = this.cartSnackbarQueue[0];
    if (message === undefined) {
      return;
    }
    this.cartSnackbarQueue = this.cartSnackbarQueue.slice(1);
    this.cartSnackbarGeneration += 1;
    const generation: number = this.cartSnackbarGeneration;
    this.cartSnackbarMessage = message;
    this.cartSnackbarVisible = true;
    setTimeout(() => {
      if (generation !== this.cartSnackbarGeneration) {
        return;
      }
      this.cartSnackbarVisible = false;
      this.showNextCartSnackbar();
    }, CART_SNACKBAR_DURATION_MS);
  }

  private updateCartQuantity(stableId: number, quantity: number): void {
    this.cartLines = this.cartLines.map((line: OrderLine): OrderLine => {
      if (line.snackStableId === stableId) {
        return createOrderLine(stableId, quantity);
      }
      return createOrderLine(line.snackStableId, line.quantity);
    });
  }

  increaseCartItem(stableId: number): void {
    if (this.shouldCartRequestFail()) {
      this.showCartSnackbar($r('app.string.cart_increase_error'));
      return;
    }
    const line: OrderLine | undefined = this.cartLines.find(
      (candidate: OrderLine): boolean => candidate.snackStableId === stableId);
    if (line !== undefined) {
      this.updateCartQuantity(stableId, line.quantity + 1);
    }
  }

  decreaseCartItem(stableId: number): void {
    if (this.shouldCartRequestFail()) {
      this.showCartSnackbar($r('app.string.cart_decrease_error'));
      return;
    }
    const line: OrderLine | undefined = this.cartLines.find(
      (candidate: OrderLine): boolean => candidate.snackStableId === stableId);
    if (line !== undefined) {
      if (line.quantity === 1) {
        this.removeCartItem(stableId);
      } else {
        this.updateCartQuantity(stableId, line.quantity - 1);
      }
    }
  }

  removeCartItem(stableId: number): void {
    this.cartLines = this.cartLines
      .filter((line: OrderLine): boolean => line.snackStableId !== stableId)
      .map((line: OrderLine): OrderLine => createOrderLine(line.snackStableId, line.quantity));
  }

  hideCartItem(stableId: number): void {
    if (!this.hiddenCartIds.includes(stableId)) {
      const hidden: number[] = this.hiddenCartIds.slice();
      hidden.push(stableId);
      this.hiddenCartIds = hidden;
    }
  }

  acknowledgeCheckout(): void {
    this.checkoutActionCount += 1;
  }

  isCartItemHidden(stableId: number): boolean {
    return this.hiddenCartIds.includes(stableId);
  }

  cartSubtotalCents(): number {
    let subtotal: number = 0;
    this.cartLines.forEach((line: OrderLine): void => {
      const snack: Snack | undefined = getSnackById(line.snackStableId);
      if (snack !== undefined) {
        subtotal += snack.priceCents * line.quantity;
      }
    });
    return subtotal;
  }

  cartTotalCents(): number {
    return this.cartSubtotalCents() + SHIPPING_CENTS;
  }

  openDetail(stableId: number, origin: string): void {
    if (this.currentRoute === ROUTE_DETAIL) {
      return;
    }
    if (getSnackById(stableId) === undefined) {
      return;
    }
    this.cartSnackbarGeneration += 1;
    this.cartSnackbarVisible = false;
    if (this.currentRoute === ROUTE_SEARCH) {
      this.resetSearchState();
    }
    this.selectedSnackId = stableId;
    this.detailReturnRoute = this.currentRoute;
    this.detailOrigin = origin;
    this.detailQuantity = 1;
    this.detailExpanded = false;
    this.currentRoute = ROUTE_DETAIL;
  }

  incrementDetailQuantity(): void {
    this.detailQuantity += 1;
  }

  decrementDetailQuantity(): void {
    if (this.detailQuantity > 0) {
      this.detailQuantity -= 1;
    }
  }

  toggleDetailExpanded(): void {
    this.detailExpanded = !this.detailExpanded;
  }

  acknowledgeDetailAddToCart(): void {
    this.detailAddActionCount += 1;
  }

  acknowledgeDetailRelated(): void {
    this.detailRelatedActionCount += 1;
  }

  goBack(): void {
    this.currentRoute = this.detailReturnRoute;
    this.selectedSnackId = undefined;
    this.detailOrigin = NO_DETAIL_ORIGIN;
    if (!this.cartSnackbarVisible) {
      this.showNextCartSnackbar();
    }
  }

  showFilters(): void {
    this.filterSort = DEFAULT_FILTER_SORT;
    this.filterMaxCalories = 0;
    this.filterVisible = true;
  }

  toggleQuickFilterSelection(name: string): void {
    if (this.quickFilterSelections.includes(name)) {
      this.quickFilterSelections = this.quickFilterSelections.filter(
        (existing: string): boolean => existing !== name);
    } else {
      this.quickFilterSelections = this.quickFilterSelections.concat(name);
    }
  }

  isQuickFilterSelected(name: string): boolean {
    return this.quickFilterSelections.includes(name);
  }

  hideFilters(): void {
    this.filterVisible = false;
  }

  selectFilterSort(sort: string): void {
    this.filterSort = sort;
  }

  setFilterMaxCalories(value: number): void {
    if (value < 0) {
      this.filterMaxCalories = 0;
    } else if (value > 300) {
      this.filterMaxCalories = 300;
    } else {
      this.filterMaxCalories = value;
    }
  }

  toggleFilterSelection(name: string): void {
    if (this.filterSelections.includes(name)) {
      this.filterSelections = this.filterSelections.filter(
        (existing: string): boolean => existing !== name);
    } else {
      this.filterSelections = this.filterSelections.concat(name);
    }
  }

  isFilterSelected(name: string): boolean {
    return this.filterSelections.includes(name);
  }

  acknowledgeFilterReset(): void {
    this.filterResetActionCount += 1;
  }

  acknowledgeFilterApplyToFeed(): void {
    this.filterApplyActionCount += 1;
  }
}
