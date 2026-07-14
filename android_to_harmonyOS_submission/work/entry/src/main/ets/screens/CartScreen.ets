import { i18n } from '@kit.LocalizationKit';
import { DestinationBar } from '../components/DestinationBar';
import { QuantitySelector } from '../components/QuantitySelector';
import { SnackCollection } from '../components/SnackCollection';
import { SnackImage } from '../components/SnackImage';
import {
  getSnackById,
  INSPIRED_BY_CART_COLLECTION,
  SHIPPING_CENTS,
  SNACKS
} from '../data/SnackData';
import type { OrderLine } from '../model/OrderLine';
import type { Snack } from '../model/Snack';
import { AppStore } from '../state/AppStore';
import {
  BACKGROUND_COLOR,
  BORDER_COLOR,
  BRAND_COLOR,
  ERROR_COLOR,
  KARLA_REGULAR,
  MONTSERRAT_SEMIBOLD,
  PRIMARY_TEXT_COLOR,
  SECONDARY_TEXT_COLOR
} from '../theme/JetsnackTheme';
import { formatPrice } from '../utils/CurrencyFormatter';

const CART_SWIPE_DISMISS_THRESHOLD: number = 56;
const CART_SWIPE_DISMISS_VELOCITY: number = 125;

@Component
export struct CartScreen {
  @ObjectLink appStore: AppStore;
  @State activeSwipeStableId: number = 0;
  @State activeSwipeOffset: number = 0;
  @State cartViewportWidth: number = 360;
  @State checkoutButtonHeight: number = 40;

  private checkoutTouchHeight(): number {
    return Math.max(48, this.checkoutButtonHeight);
  }

  private checkoutTouchTop(): number {
    return (this.checkoutButtonHeight - this.checkoutTouchHeight()) / 2;
  }

  private visibleCartLines(): OrderLine[] {
    return this.appStore.cartLines.filter((line: OrderLine): boolean =>
      !this.appStore.isCartItemHidden(line.snackStableId));
  }

  private cartSnack(line: OrderLine): Snack {
    const snack: Snack | undefined = getSnackById(line.snackStableId);
    if (snack !== undefined) {
      return snack;
    }
    return SNACKS[0];
  }

  private swipeOffsetFor(stableId: number): number {
    if (this.activeSwipeStableId === stableId) {
      return this.activeSwipeOffset;
    }
    return 0;
  }

  private swipeProgressFor(stableId: number): number {
    return Math.min(Math.abs(this.swipeOffsetFor(stableId)) / this.cartViewportWidth, 1);
  }

  private swipeBackgroundSize(stableId: number): number {
    return Math.min(Math.abs(this.swipeOffsetFor(stableId)), this.cartViewportWidth);
  }

  private swipeBackgroundPadding(stableId: number): number {
    return this.swipeProgressFor(stableId) < 0.5 ? 4 : 0;
  }

  private swipeBackgroundRadius(stableId: number): number {
    const progress: number = this.swipeProgressFor(stableId);
    return this.swipeBackgroundSize(stableId) * (1 - progress) / 2;
  }

  private swipeIconOpacity(stableId: number): number {
    const progress: number = this.swipeProgressFor(stableId);
    return progress > 0.4 ? 0.5 : 1;
  }

  private showSwipeIcon(stableId: number): boolean {
    const progress: number = this.swipeProgressFor(stableId);
    return progress >= 0.125 && progress <= 0.475;
  }

  private beginCartSwipe(stableId: number): void {
    this.activeSwipeStableId = stableId;
    this.activeSwipeOffset = 0;
  }

  private isRtlLayout(): boolean {
    const systemLanguage: string = i18n.System.getSystemLanguage();
    return i18n.isRTL(systemLanguage);
  }

  private updateCartSwipe(stableId: number, offsetX: number): void {
    if (this.activeSwipeStableId !== stableId) {
      this.activeSwipeStableId = stableId;
    }
    if (this.isRtlLayout()) {
      this.activeSwipeOffset = Math.min(this.cartViewportWidth, Math.max(0, offsetX));
    } else {
      this.activeSwipeOffset = Math.max(-this.cartViewportWidth, Math.min(0, offsetX));
    }
  }

  private resetCartSwipe(): void {
    this.activeSwipeStableId = 0;
    this.activeSwipeOffset = 0;
  }

  private finishCartSwipe(stableId: number, velocityX: number): void {
    const dismissedByDistance: boolean = this.isRtlLayout() ?
      this.activeSwipeOffset >= CART_SWIPE_DISMISS_THRESHOLD :
      this.activeSwipeOffset <= -CART_SWIPE_DISMISS_THRESHOLD;
    const dismissedByVelocity: boolean = this.isRtlLayout() ?
      velocityX >= CART_SWIPE_DISMISS_VELOCITY :
      velocityX <= -CART_SWIPE_DISMISS_VELOCITY;
    if (this.activeSwipeStableId === stableId &&
      (dismissedByDistance || dismissedByVelocity)) {
      this.appStore.hideCartItem(stableId);
    }
    this.resetCartSwipe();
  }

  @Builder
  private cartLine(line: OrderLine) {
    Stack({ alignContent: Alignment.End }) {
      Row() {
        if (this.swipeProgressFor(line.snackStableId) > 0.5) {
          Text($r('app.string.remove_item'))
            .fontFamily(MONTSERRAT_SEMIBOLD)
            .fontSize(16)
            .fontColor(BACKGROUND_COLOR)
            .textAlign(TextAlign.Center)
        } else if (this.showSwipeIcon(line.snackStableId)) {
          Image($r('app.media.ic_delete_forever'))
            .width(32)
            .height(32)
            .fillColor(BACKGROUND_COLOR)
            .opacity(this.swipeIconOpacity(line.snackStableId))
            .accessibilityLevel('no')
        }
      }
      .width(this.swipeBackgroundSize(line.snackStableId))
      .height(this.swipeBackgroundSize(line.snackStableId))
      .padding(this.swipeBackgroundPadding(line.snackStableId))
      .justifyContent(FlexAlign.Center)
      .alignItems(VerticalAlign.Center)
      .backgroundColor(ERROR_COLOR)
      .borderRadius(this.swipeBackgroundRadius(line.snackStableId))

      Row() {
        SnackImage({
          imageResource: this.cartSnack(line).imageResource,
          contentDescription: '',
          stableId: line.snackStableId,
          collectionId: 90,
          imageSize: 100
        })
          .margin({ top: 16, bottom: 16 })

        Column() {
          Row() {
            Text(this.cartSnack(line).name)
              .fontFamily(MONTSERRAT_SEMIBOLD)
              .fontSize(16)
              .lineHeight(24)
              .fontColor(SECONDARY_TEXT_COLOR)
              .layoutWeight(1)
              .margin({ top: 16, right: 16 })

            Stack({ alignContent: Alignment.Center }) {
              Image($r('app.media.ic_close'))
                .width(24)
                .height(24)
                .fillColor($r('app.color.icon_secondary'))
            }
            .id(`action.cart.remove.${line.snackStableId}`)
            .accessibilityText($r('app.string.label_remove'))
            .accessibilityRole(AccessibilityRoleType.BUTTON)
            .width(48)
            .height(48)
            .margin({ top: 12 })
            .onTouch((event: TouchEvent) => {
              event.stopPropagation();
            })
            .monopolizeEvents(true)
            .onClick(() => {
              this.appStore.removeCartItem(line.snackStableId);
            })
          }
          .width('100%')

          Text(this.cartSnack(line).tagline)
            .fontFamily(KARLA_REGULAR)
            .fontSize(16)
            .lineHeight(28)
            .fontColor($r('app.color.text_help'))
            .padding({ right: 16 })

          Row() {
            Text(formatPrice(this.cartSnack(line).priceCents))
              .fontFamily(MONTSERRAT_SEMIBOLD)
              .fontSize(16)
              .lineHeight(24)
              .fontColor(PRIMARY_TEXT_COLOR)
              .layoutWeight(1)
              .margin({ right: 16 })

            QuantitySelector({
              count: line.quantity,
              stableIdPrefix: `cart.quantity.${line.snackStableId}`,
              onDecrease: () => {
                this.appStore.decreaseCartItem(line.snackStableId);
              },
              onIncrease: () => {
                this.appStore.increaseCartItem(line.snackStableId);
              }
            })
          }
          .width('100%')
          .alignItems(VerticalAlign.Center)
          .margin({ top: 8 })
        }
        .layoutWeight(1)
        .alignItems(HorizontalAlign.Start)
        .margin({ left: 16 })
      }
      .width('100%')
      .constraintSize({ minHeight: 132 })
      .padding({ left: 24, right: 24 })
      .alignItems(VerticalAlign.Top)
      .backgroundColor(BACKGROUND_COLOR)
      .translate({ x: this.swipeOffsetFor(line.snackStableId) })
    }
    .id(`action.cart.swipeDismiss.persistence.${line.snackStableId}`)
    .accessibilityText(this.cartSnack(line).name)
    .width('100%')
    .constraintSize({ minHeight: 132 })
    .backgroundColor(BACKGROUND_COLOR)
    .gesture(
      PanGesture({ direction: PanDirection.Horizontal, distance: 8 })
        .onActionStart(() => {
          this.beginCartSwipe(line.snackStableId);
        })
        .onActionUpdate((event: GestureEvent) => {
          this.updateCartSwipe(line.snackStableId, event.offsetX);
        })
        .onActionEnd((event: GestureEvent) => {
          this.finishCartSwipe(line.snackStableId, event.velocityX);
        })
        .onActionCancel(() => {
          this.resetCartSwipe();
        })
    )
    .onClick(() => {
      this.appStore.openDetail(line.snackStableId, 'cart');
    })

    Divider()
      .strokeWidth(1)
      .color(BORDER_COLOR)
      .margin({ left: 24, right: 24 })
  }

  @Builder
  private summaryRow(label: Resource, value: string, emphasized: boolean = false,
    verticalPadding: number = 0) {
    Row() {
      Text(label)
        .fontFamily(KARLA_REGULAR)
        .fontSize(16)
        .lineHeight(28)
        .fontColor(SECONDARY_TEXT_COLOR)
        .textAlign(emphasized ? TextAlign.End : TextAlign.Start)
        .layoutWeight(1)
        .margin({ right: emphasized ? 16 : 0 })

      Text(value)
        .fontFamily(emphasized ? MONTSERRAT_SEMIBOLD : KARLA_REGULAR)
        .fontSize(16)
        .lineHeight(28)
        .fontColor(emphasized ? PRIMARY_TEXT_COLOR : SECONDARY_TEXT_COLOR)
    }
    .width('100%')
    .constraintSize({ minHeight: 28 + verticalPadding * 2 })
    .padding({ left: 24, right: 24, top: verticalPadding, bottom: verticalPadding })
  }

  @Builder
  private orderSummary() {
    Column() {
      Row() {
        Text($r('app.string.cart_summary_header'))
          .fontFamily(MONTSERRAT_SEMIBOLD)
          .fontSize(20)
          .lineHeight(24)
          .fontColor(BRAND_COLOR)
          .maxLines(1)
          .textOverflow({ overflow: TextOverflow.Ellipsis })
          .layoutWeight(1)
      }
      .width('100%')
      .constraintSize({ minHeight: 56 })
      .padding({ left: 24, right: 24 })
      .alignItems(VerticalAlign.Center)

      this.summaryRow($r('app.string.cart_subtotal_label'),
        formatPrice(this.appStore.cartSubtotalCents()))
      this.summaryRow($r('app.string.cart_shipping_label'), formatPrice(SHIPPING_CENTS), false, 8)

      Blank()
        .height(8)

      Divider()
        .strokeWidth(1)
        .color(BORDER_COLOR)

      this.summaryRow($r('app.string.cart_total_label'),
        formatPrice(this.appStore.cartTotalCents()), true, 8)

      Divider()
        .strokeWidth(1)
        .color(BORDER_COLOR)
    }
    .id('cart.summary')
    .width('100%')
    .backgroundColor(BACKGROUND_COLOR)
  }

  @Builder
  private checkoutBar() {
    Column() {
      Divider()
        .strokeWidth(1)
        .color(BORDER_COLOR)

      Row() {
        Blank()
          .layoutWeight(1)

        Text($r('app.string.cart_checkout'))
          .id('action.cart.checkout')
          .accessibilityText($r('app.string.cart_checkout'))
          .accessibilityRole(AccessibilityRoleType.BUTTON)
          .fontFamily(MONTSERRAT_SEMIBOLD)
          .fontSize(14)
          .lineHeight(16)
          .letterSpacing(1.25)
          .fontColor($r('app.color.text_interactive'))
          .direction(Direction.Ltr)
          .textAlign(TextAlign.Start)
          .maxLines(1)
          .layoutWeight(1)
          .constraintSize({ minHeight: 40 })
          .padding({ left: 24, right: 24, top: 8, bottom: 8 })
          .linearGradient({
            direction: GradientDirection.Right,
            colors: [
              [$r('app.color.button_gradient_start'), 0],
              [$r('app.color.button_gradient_end'), 1]
            ]
          })
          .margin({ left: 12, right: 12, top: 8, bottom: 8 })
          .responseRegion({
            x: 0,
            y: this.checkoutTouchTop(),
            width: '100%',
            height: this.checkoutTouchHeight()
          })
          .onAreaChange((_oldValue: Area, newValue: Area) => {
            const height: number = Number(newValue.height);
            if (height > 0 && height !== this.checkoutButtonHeight) {
              this.checkoutButtonHeight = height;
            }
          })
          .onClick(() => {
            this.appStore.acknowledgeCheckout();
          })
      }
      .width('100%')
      .constraintSize({ minHeight: 56 })
    }
    .width('100%')
    .backgroundColor(BACKGROUND_COLOR)
  }

  build() {
    Stack({ alignContent: Alignment.Bottom }) {
      Scroll() {
        Column() {
          Blank()
            .height(56)

          Row() {
            Text($r('app.plural.cart_order_header', this.appStore.cartLines.length))
              .fontFamily(MONTSERRAT_SEMIBOLD)
              .fontSize(20)
              .lineHeight(24)
              .fontColor(BRAND_COLOR)
              .maxLines(1)
              .textOverflow({ overflow: TextOverflow.Ellipsis })
              .layoutWeight(1)
          }
          .id('cart.order.header')
          .width('100%')
          .constraintSize({ minHeight: 56 })
          .padding({ left: 24, right: 24 })
          .alignItems(VerticalAlign.Center)

          ForEach(this.visibleCartLines(), (line: OrderLine) => {
            this.cartLine(line)
          }, (line: OrderLine): string => line.snackStableId.toString())

          this.orderSummary()

          SnackCollection({
            collection: INSPIRED_BY_CART_COLLECTION,
            onOpen: (stableId: number, origin: string) => {
              this.appStore.openDetail(stableId, origin);
            }
          })

          Blank()
            .height(56)
        }
        .width('100%')
      }
      .width('100%')
      .height('100%')
      .scrollBar(BarState.Off)

      DestinationBar()
        .align(Alignment.Top)

      this.checkoutBar()
    }
    .id('screen.cart')
    .accessibilityText($r('app.string.home_cart_navigation'))
    .width('100%')
    .height('100%')
    .backgroundColor(BACKGROUND_COLOR)
    .onAreaChange((_oldValue: Area, newValue: Area) => {
      const width: number = Number(newValue.width);
      if (width > 0) {
        this.cartViewportWidth = width;
      }
    })
  }
}
