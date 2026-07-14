import {
  BORDER_COLOR,
  BRAND_COLOR,
  MONTSERRAT_SEMIBOLD,
  SECONDARY_TEXT_COLOR
} from '../theme/JetsnackTheme';

@Component
export struct DestinationBar {
  private deliveryActionCount: number = 0;

  private acknowledgeDeliveryAddressAction(): void {
    this.deliveryActionCount += 1;
  }

  build() {
    Column() {
      Row() {
        Text($r('app.string.delivery_address'))
          .fontFamily(MONTSERRAT_SEMIBOLD)
          .fontSize(16)
          .lineHeight(24)
          .letterSpacing(0.15)
          .fontColor(SECONDARY_TEXT_COLOR)
          .textAlign(TextAlign.Center)
          .maxLines(1)
          .textOverflow({ overflow: TextOverflow.Ellipsis })
          .layoutWeight(1)
          .accessibilityText($r('app.string.delivery_address'))

        Stack({ alignContent: Alignment.Center }) {
          Image($r('app.media.ic_expand_more'))
            .width(24)
            .height(24)
            .fillColor(BRAND_COLOR)
        }
        .width(48)
        .height(48)
        .margin({ left: 8 })
        .id('action.delivery.address.expand')
        .accessibilityText($r('app.string.label_select_delivery'))
        .accessibilityRole(AccessibilityRoleType.BUTTON)
        .onClick(() => {
          this.acknowledgeDeliveryAddressAction();
        })
      }
      .width('100%')
      .height(64)
      .padding({ left: 16, right: 4 })
      .alignItems(VerticalAlign.Center)
      .backgroundColor($r('app.color.destination_overlay'))

      Divider()
        .strokeWidth(1)
        .color(BORDER_COLOR)
    }
    .width('100%')
    .height(65)
  }
}
