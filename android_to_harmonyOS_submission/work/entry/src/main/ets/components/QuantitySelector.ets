import {
  BACKGROUND_COLOR,
  BRAND_COLOR,
  KARLA_BOLD,
  MONTSERRAT_REGULAR,
  SECONDARY_TEXT_COLOR
} from '../theme/JetsnackTheme';

@Component
export struct QuantitySelector {
  @Prop count: number;
  @Prop stableIdPrefix: string;
  @Require
  onDecrease: () => void;
  @Require
  onIncrease: () => void;
  @State decreasePressed: boolean = false;
  @State increasePressed: boolean = false;

  private updateDecreasePressed(eventType: TouchType): void {
    if (eventType === TouchType.Down) {
      this.decreasePressed = true;
    } else if (eventType === TouchType.Up || eventType === TouchType.Cancel) {
      this.decreasePressed = false;
    }
  }

  private updateIncreasePressed(eventType: TouchType): void {
    if (eventType === TouchType.Down) {
      this.increasePressed = true;
    } else if (eventType === TouchType.Up || eventType === TouchType.Cancel) {
      this.increasePressed = false;
    }
  }

  private decreaseId(): string {
    if (this.stableIdPrefix.startsWith('cart.quantity.')) {
      return `cart.quantity.decrease.${this.stableIdPrefix.substring('cart.quantity.'.length)}`;
    }
    return `${this.stableIdPrefix}.decrease`;
  }

  private increaseId(): string {
    if (this.stableIdPrefix.startsWith('cart.quantity.')) {
      return `cart.quantity.increase.${this.stableIdPrefix.substring('cart.quantity.'.length)}`;
    }
    return `${this.stableIdPrefix}.increase`;
  }

  build() {
    Row() {
      Text($r('app.string.quantity'))
        .fontFamily(MONTSERRAT_REGULAR)
        .fontSize(16)
        .lineHeight(24)
        .letterSpacing(0.15)
        .fontColor(SECONDARY_TEXT_COLOR)
        .margin({ right: 18 })

      Stack({ alignContent: Alignment.Center }) {
        if (this.decreasePressed) {
          Image($r('app.media.ic_remove'))
            .width(24)
            .height(24)
            .fillColor(SECONDARY_TEXT_COLOR)
        } else {
          Image($r('app.media.ic_quantity_remove'))
            .width(24)
            .height(24)
        }
      }
      .id(this.decreaseId())
      .accessibilityText($r('app.string.label_decrease'))
      .accessibilityRole(AccessibilityRoleType.BUTTON)
      .width(24)
      .height(24)
      .responseRegion({ x: -12, y: -12, width: 48, height: 48 })
      .backgroundColor(BACKGROUND_COLOR)
      .linearGradient({
        direction: GradientDirection.Right,
        colors: [
          [this.decreasePressed ? $r('app.color.quantity_border_gradient_start') : BACKGROUND_COLOR, 0],
          [this.decreasePressed ? $r('app.color.quantity_border_gradient_end') : BACKGROUND_COLOR, 1]
        ]
      })
      .borderImage({
        source: {
          direction: GradientDirection.RightBottom,
          colors: [
            [$r('app.color.quantity_border_gradient_start'), 0],
            [$r('app.color.quantity_border_gradient_end'), 1]
          ]
        },
        slice: 1,
        width: 2
      })
      .borderRadius('50%')
      .onTouch((event: TouchEvent) => {
        this.updateDecreasePressed(event.type);
        event.stopPropagation();
      })
      .monopolizeEvents(true)
      .onClick(() => {
        this.onDecrease();
      })

      Text(this.count.toString())
        .fontFamily(KARLA_BOLD)
        .fontSize(18)
        .lineHeight(24)
        .fontColor(BRAND_COLOR)
        .textAlign(TextAlign.Center)
        .width(24)

      Stack({ alignContent: Alignment.Center }) {
        if (this.increasePressed) {
          Image($r('app.media.ic_add'))
            .width(24)
            .height(24)
            .fillColor(SECONDARY_TEXT_COLOR)
        } else {
          Image($r('app.media.ic_quantity_add'))
            .width(24)
            .height(24)
        }
      }
      .id(this.increaseId())
      .accessibilityText($r('app.string.label_increase'))
      .accessibilityRole(AccessibilityRoleType.BUTTON)
      .width(24)
      .height(24)
      .responseRegion({ x: -12, y: -12, width: 48, height: 48 })
      .backgroundColor(BACKGROUND_COLOR)
      .linearGradient({
        direction: GradientDirection.Right,
        colors: [
          [this.increasePressed ? $r('app.color.quantity_border_gradient_start') : BACKGROUND_COLOR, 0],
          [this.increasePressed ? $r('app.color.quantity_border_gradient_end') : BACKGROUND_COLOR, 1]
        ]
      })
      .borderImage({
        source: {
          direction: GradientDirection.RightBottom,
          colors: [
            [$r('app.color.quantity_border_gradient_start'), 0],
            [$r('app.color.quantity_border_gradient_end'), 1]
          ]
        },
        slice: 1,
        width: 2
      })
      .borderRadius('50%')
      .onTouch((event: TouchEvent) => {
        this.updateIncreasePressed(event.type);
        event.stopPropagation();
      })
      .monopolizeEvents(true)
      .onClick(() => {
        this.onIncrease();
      })
    }
    .alignItems(VerticalAlign.Center)
  }
}
