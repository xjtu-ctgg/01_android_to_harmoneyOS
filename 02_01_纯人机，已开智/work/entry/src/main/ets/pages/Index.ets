import { BottomNav } from '../components/BottomNav';
import { FeedScreen } from '../screens/FeedScreen';
import { CartScreen } from '../screens/CartScreen';
import { DetailScreen } from '../screens/DetailScreen';
import { FilterOverlay } from '../screens/FilterOverlay';
import { ProfileScreen } from '../screens/ProfileScreen';
import { SearchScreen } from '../screens/SearchScreen';
import { ROUTE_CART, ROUTE_DETAIL, ROUTE_FEED, ROUTE_PROFILE, ROUTE_SEARCH } from '../state/AppRoute';
import { AppStore } from '../state/AppStore';
import {
  BACKGROUND_COLOR,
  MONTSERRAT_MEDIUM,
  SECONDARY_TEXT_COLOR,
  registerJetsnackFonts
} from '../theme/JetsnackTheme';

@Entry
@Component
struct Index {
  @State appStore: AppStore = new AppStore();
  @StorageProp('initialRoute') @Watch('onInitialRouteChanged') initialRoute: string = ROUTE_FEED;
  @StorageProp('navigationRequestId') @Watch('onNavigationRequestChanged') navigationRequestId: number = 0;
  @StorageProp('configurationRequestId') @Watch('onConfigurationRequestChanged')
  configurationRequestId: number = 0;
  @StorageProp('topInsetPx') topInsetPx: number = 0;
  @StorageProp('bottomInsetPx') bottomInsetPx: number = 0;
  @StorageProp('leftInsetPx') leftInsetPx: number = 0;
  @StorageProp('rightInsetPx') rightInsetPx: number = 0;

  private topInset(): number {
    return this.getUIContext().px2vp(this.topInsetPx);
  }

  private bottomInset(): number {
    return this.getUIContext().px2vp(this.bottomInsetPx);
  }

  private leftInset(): number {
    return this.getUIContext().px2vp(this.leftInsetPx);
  }

  private rightInset(): number {
    return this.getUIContext().px2vp(this.rightInsetPx);
  }

  private onInitialRouteChanged(): void {
    this.appStore.selectTab(this.initialRoute);
  }

  private onNavigationRequestChanged(): void {
    this.appStore.selectTab(this.initialRoute);
  }

  private onConfigurationRequestChanged(): void {
    this.appStore.resetSearchState();
    if (this.appStore.currentRoute === ROUTE_SEARCH) {
      this.appStore.refreshSearchResults();
    }
    this.appStore.resetDetailTransientState();
    this.appStore.hideFilters();
  }

  aboutToAppear(): void {
    registerJetsnackFonts(this.getUIContext());
    this.appStore.selectTab(this.initialRoute);
  }

  onBackPress(): boolean {
    if (this.appStore.filterVisible) {
      this.appStore.hideFilters();
      return true;
    }
    if (this.appStore.currentRoute === ROUTE_DETAIL) {
      this.appStore.goBack();
      return true;
    }
    if (this.appStore.currentRoute !== ROUTE_FEED) {
      this.appStore.selectTab(ROUTE_FEED);
      return true;
    }
    return false;
  }

  @Builder
  private currentTab() {
    Stack() {
      FeedScreen({ appStore: this.appStore })
        .visibility(this.appStore.currentRoute === ROUTE_FEED ? Visibility.Visible : Visibility.Hidden)

      SearchScreen({ appStore: this.appStore })
        .visibility(this.appStore.currentRoute === ROUTE_SEARCH ? Visibility.Visible : Visibility.Hidden)

      CartScreen({ appStore: this.appStore })
        .visibility(this.appStore.currentRoute === ROUTE_CART ? Visibility.Visible : Visibility.Hidden)

      ProfileScreen()
        .visibility(this.appStore.currentRoute === ROUTE_PROFILE ? Visibility.Visible : Visibility.Hidden)

      if (this.appStore.currentRoute === ROUTE_DETAIL) {
        DetailScreen({
          appStore: this.appStore,
          topInset: this.topInset(),
          leftInset: this.leftInset(),
          rightInset: this.rightInset()
        })
      }
    }
    .width('100%')
    .height('100%')
  }

  @Builder
  private snackbar() {
    if (this.appStore.currentRoute !== ROUTE_DETAIL && this.appStore.cartSnackbarVisible) {
      Text(this.appStore.cartSnackbarMessage)
        .id('cart.snackbar.error')
        .accessibilityText(this.appStore.cartSnackbarMessage)
        .fontFamily(MONTSERRAT_MEDIUM)
        .fontSize(14)
        .lineHeight(20)
        .letterSpacing(0.25)
        .fontColor(SECONDARY_TEXT_COLOR)
        .width('calc(100% - 24vp)')
        .constraintSize({ minHeight: 68 })
        .padding({ left: 16, right: 8, top: 6, bottom: 6 })
        .margin({ left: 12, right: 12, top: 12, bottom: 12 })
        .borderRadius('50%')
        .backgroundColor(BACKGROUND_COLOR)
        .shadow(ShadowStyle.OUTER_DEFAULT_MD)
        .align(Alignment.Bottom)
    }
  }

  build() {
    Column() {
      Stack() {
        this.currentTab()

        if (this.appStore.filterVisible) {
          FilterOverlay({ appStore: this.appStore })
        }

        this.snackbar()
      }
      .width('100%')
      .layoutWeight(1)
      .padding({
        top: this.appStore.currentRoute === ROUTE_DETAIL ? 0 : this.topInset(),
        bottom: this.appStore.currentRoute === ROUTE_DETAIL ? this.bottomInset() : 0,
        left: this.appStore.currentRoute === ROUTE_DETAIL ? 0 : this.leftInset(),
        right: this.appStore.currentRoute === ROUTE_DETAIL ? 0 : this.rightInset()
      })

      if (this.appStore.currentRoute !== ROUTE_DETAIL) {
        BottomNav({
          currentRoute: this.appStore.currentRoute,
          bottomInset: this.bottomInset(),
          onSelect: (route: string) => {
            this.appStore.selectTab(route);
          }
        })
      }
    }
    .id('screen.root')
    .accessibilityText($r('app.string.app_name'))
    .width('100%')
    .height('100%')
    .backgroundColor(BACKGROUND_COLOR)
  }
}
