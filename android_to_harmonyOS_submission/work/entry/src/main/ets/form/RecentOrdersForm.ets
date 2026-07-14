import { RECENT_ORDER_FORM_ITEMS } from './RecentOrdersFormData';
import type { RecentOrderFormItem } from './RecentOrdersFormData';

const recentOrdersStorage: LocalStorage = new LocalStorage();
const FORM_DIMENSION_MEDIUM: number = 3;
const FORM_DEFAULT_WIDTH: number = 360;
const FORM_DEFAULT_HEIGHT: number = 224;
const FORM_MEDIUM_MIN_WIDTH: number = 260;
const FORM_LARGE_MIN_WIDTH: number = 479;
const FORM_TITLE_MIN_HEIGHT: number = 180;
const FORM_TRAILING_MEDIUM_MIN_WIDTH: number = 340;
const FORM_TRAILING_MEDIUM_MAX_WIDTH: number = 479;
const FORM_TRAILING_LARGE_EXCLUSIVE_MIN_WIDTH: number = 620;

class CartRouteParams {
  targetRoute: string = 'home/cart';
  orderKey: string;

  constructor(orderKey: string) {
    this.orderKey = orderKey;
  }
}

class CartRouterAction {
  action: string = 'router';
  abilityName: string = 'EntryAbility';
  params: CartRouteParams;

  constructor(orderKey: string) {
    this.params = new CartRouteParams(orderKey);
  }
}

@Entry(recentOrdersStorage)
@Component
struct RecentOrdersForm {
  @LocalStorageProp('formDimension') formDimension: number = FORM_DIMENSION_MEDIUM;
  @LocalStorageProp('formWidth') formWidth: number = FORM_DEFAULT_WIDTH;
  @LocalStorageProp('formHeight') formHeight: number = FORM_DEFAULT_HEIGHT;

  private isSmall(): boolean {
    return this.formWidth < FORM_MEDIUM_MIN_WIDTH;
  }

  private isLarge(): boolean {
    return this.formWidth >= FORM_LARGE_MIN_WIDTH;
  }

  private showTitleBar(): boolean {
    return this.formHeight >= FORM_TITLE_MIN_HEIGHT;
  }

  private showTrailingCart(): boolean {
    const mediumTrailing: boolean = this.formWidth >= FORM_TRAILING_MEDIUM_MIN_WIDTH &&
      this.formWidth <= FORM_TRAILING_MEDIUM_MAX_WIDTH;
    return mediumTrailing || this.formWidth > FORM_TRAILING_LARGE_EXCLUSIVE_MIN_WIDTH;
  }

  private openCart(orderKey: string): void {
    postCardAction(this, new CartRouterAction(orderKey));
  }

  @Builder
  private titleBar() {
    Row() {
      Stack() {
        Image($r('app.media.widget_logo'))
          .width(24)
          .height(24)
          .fillColor($r('app.color.form_primary'))
          .accessibilityLevel('no')
      }
      .width(48)
      .height(48)
      .padding({ left: 2 })

      if (!this.isSmall()) {
        Text($r('app.string.recent_orders_form_title'))
          .fontSize(16)
          .fontWeight(FontWeight.Medium)
          .fontColor($r('app.color.form_on_surface'))
          .maxLines(1)
          .textOverflow({ overflow: TextOverflow.Ellipsis })
          .layoutWeight(1)
      } else {
        Blank()
          .layoutWeight(1)
      }

      Stack() {
        Image($r('app.media.shopping_cart'))
          .width(24)
          .height(24)
          .fillColor($r('app.color.form_secondary'))
          .accessibilityLevel('no')
      }
      .width(48)
      .height(48)
      .id('form.action.cart.title')
      .accessibilityText($r('app.string.recent_orders_form_cart'))
      .accessibilityRole(AccessibilityRoleType.BUTTON)
      .onClick(() => {
        this.openCart('');
      })
    }
    .width('100%')
    .height(48)
    .alignItems(VerticalAlign.Center)
    .padding({ left: 4, right: 4 })
  }

  @Builder
  private trailingCart(item: RecentOrderFormItem) {
    Stack() {
      Image($r('app.media.add_shopping_cart'))
        .width(24)
        .height(24)
        .fillColor($r('app.color.form_primary'))
        .accessibilityLevel('no')
    }
    .width(48)
    .height(48)
    .margin({ left: 16 })
    .id(`form.action.cart.${item.stableKey}`)
    .accessibilityText($r('app.string.recent_orders_form_add_to_cart'))
    .accessibilityRole(AccessibilityRoleType.BUTTON)
    .onClick(() => {
      this.openCart(item.orderKey);
    })
  }

  @Builder
  private recentOrder(item: RecentOrderFormItem) {
    Row() {
      if (!this.isSmall()) {
        Image(item.image)
          .width(68)
          .height(68)
          .borderRadius(12)
          .objectFit(ImageFit.Cover)
          .accessibilityLevel('no')
      }

      Column() {
        Text(item.title)
          .width('100%')
          .fontSize(this.isSmall() ? 14 : 16)
          .fontWeight(FontWeight.Medium)
          .fontColor($r('app.color.form_on_surface'))
          .maxLines(2)
          .textOverflow({ overflow: TextOverflow.Ellipsis })

        Text(item.supportingText)
          .width('100%')
          .fontSize(12)
          .fontColor($r('app.color.form_secondary'))
          .maxLines(2)
          .textOverflow({ overflow: TextOverflow.Ellipsis })
          .margin({ top: 4 })
      }
      .layoutWeight(1)
      .alignItems(HorizontalAlign.Start)
      .margin({ left: this.isSmall() ? 0 : 16 })

      if (this.showTrailingCart()) {
        this.trailingCart(item)
      }
    }
    .width('100%')
    .constraintSize({ minHeight: this.isSmall() ? 64 : 92 })
    .alignItems(VerticalAlign.Center)
    .padding(12)
    .borderRadius(16)
    .backgroundColor($r('app.color.form_secondary_container'))
    .accessibilityText(`${item.title}, ${item.supportingText}`)
  }

  build() {
    Column() {
      if (this.showTitleBar()) {
        this.titleBar()
      }

      List({ space: 4 }) {
        ForEach(RECENT_ORDER_FORM_ITEMS, (item: RecentOrderFormItem) => {
          ListItem() {
            this.recentOrder(item)
          }
        }, (item: RecentOrderFormItem): string => item.stableKey)
      }
      .width('100%')
      .layoutWeight(1)
      .lanes(this.isLarge() ? 2 : 1, this.isLarge() ? 4 : 0)
      .borderRadius(16)
      .clip(true)
      .scrollBar(BarState.Off)
    }
    .width('100%')
    .height('100%')
    .padding({ left: 12, right: 12, bottom: 12, top: this.showTitleBar() ? 0 : 12 })
    .backgroundColor($r('app.color.form_widget_background'))
    .id('form.recentOrders')
    .accessibilityText($r('app.string.recent_orders_form_title'))
  }
}
