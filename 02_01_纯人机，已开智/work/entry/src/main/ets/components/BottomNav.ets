import { i18n } from '@kit.LocalizationKit';
import { ROUTE_CART, ROUTE_FEED, ROUTE_PROFILE, ROUTE_SEARCH } from '../state/AppRoute';
import { BRAND_COLOR, MONTSERRAT_SEMIBOLD } from '../theme/JetsnackTheme';

export interface BottomNavItem {
  route: string;
  label: Resource;
  fallbackLabel: string;
  stableId: string;
  iconResource: Resource;
}

export const BOTTOM_NAV_ITEMS: BottomNavItem[] = [
  {
    route: ROUTE_FEED,
    label: $r('app.string.home_feed_navigation'),
    fallbackLabel: 'Home',
    stableId: 'nav.feed',
    iconResource: $r('app.media.ic_home')
  },
  {
    route: ROUTE_SEARCH,
    label: $r('app.string.home_search_navigation'),
    fallbackLabel: 'Search',
    stableId: 'nav.search',
    iconResource: $r('app.media.ic_search')
  },
  {
    route: ROUTE_CART,
    label: $r('app.string.home_cart_navigation'),
    fallbackLabel: 'My Cart',
    stableId: 'nav.cart',
    iconResource: $r('app.media.ic_shopping_cart')
  },
  {
    route: ROUTE_PROFILE,
    label: $r('app.string.home_profile_navigation'),
    fallbackLabel: 'Profile',
    stableId: 'nav.profile',
    iconResource: $r('app.media.ic_account_circle')
  }
];

@Component
export struct BottomNav {
  @Prop currentRoute: string;
  @Prop bottomInset: number;
  @Require
  onSelect: (route: string) => void;

  private localizedLabel(item: BottomNavItem): string {
    const localeTag: string = i18n.System.getSystemLocaleInstance().toString();
    let label: string = item.fallbackLabel;
    const hostContext = this.getUIContext().getHostContext();
    if (hostContext !== undefined) {
      try {
        label = hostContext.resourceManager.getStringSync(item.label.id);
      } catch {
        label = item.fallbackLabel;
      }
    }
    return label.toLocaleUpperCase(localeTag);
  }

  @Builder
  private navItem(item: BottomNavItem) {
    Column() {
      Row() {
        Image(item.iconResource)
          .width(24)
          .height(24)
          .fillColor(this.currentRoute === item.route ? $r('app.color.icon_interactive') :
            $r('app.color.icon_interactive_inactive'))

        if (this.currentRoute === item.route) {
          Text(this.localizedLabel(item))
            .fontFamily(MONTSERRAT_SEMIBOLD)
            .fontSize(14)
            .lineHeight(16)
            .letterSpacing(1.25)
            .fontColor($r('app.color.text_interactive'))
            .maxLines(1)
            .margin({ left: 4 })
        }
      }
      .width('100%')
      .height(40)
      .justifyContent(FlexAlign.Center)
      .alignItems(VerticalAlign.Center)
      .border({
        width: this.currentRoute === item.route ? 2 : 0,
        color: $r('app.color.icon_interactive')
      })
      .borderRadius(20)
    }
    .height(56)
    .padding({
      left: this.currentRoute === item.route ? 16 : 0,
      right: this.currentRoute === item.route ? 16 : 0,
      top: 8,
      bottom: 8
    })
    .layoutWeight(this.currentRoute === item.route ? 2 : 1)
    .id(item.stableId)
    .accessibilityText(this.localizedLabel(item))
    .accessibilityRole(AccessibilityRoleType.BUTTON)
    .accessibilitySelected(this.currentRoute === item.route)
    .onClick(() => {
      this.onSelect(item.route);
    })
  }

  build() {
    Row() {
      ForEach(BOTTOM_NAV_ITEMS, (item: BottomNavItem) => {
        this.navItem(item)
      }, (item: BottomNavItem): string => item.route)
    }
    .width('100%')
    .height(56 + this.bottomInset)
    .padding({ bottom: this.bottomInset })
    .alignItems(VerticalAlign.Center)
    .backgroundColor(BRAND_COLOR)
  }
}
