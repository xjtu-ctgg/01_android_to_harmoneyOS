import { Snack } from '../model/Snack';
import {
  BACKGROUND_COLOR,
  BORDER_COLOR,
  HELP_TEXT_COLOR,
  KARLA_REGULAR,
  MONTSERRAT_SEMIBOLD,
  SECONDARY_TEXT_COLOR
} from '../theme/JetsnackTheme';
import { SnackImage } from './SnackImage';

const GRADIENT_CARD_SLOT: number = 186;
const GRADIENT_SPAN: number = 1116;

@Component
export struct SnackCard {
  @Prop snack: Snack;
  @Prop collectionId: number;
  @Prop cardIndex: number;
  @Prop gradientScrollOffset: number;
  @Prop gradientStart: ResourceColor;
  @Prop gradientBridge: ResourceColor;
  @Prop gradientMiddle: ResourceColor;
  @Require
  onOpen: (stableId: number, origin: string) => void;

  private gradientColors(): [ResourceColor, number][] {
    return [
      [this.gradientStart, 0],
      [this.gradientBridge, 0.25],
      [this.gradientMiddle, 0.5],
      [this.gradientBridge, 0.75],
      [this.gradientStart, 1]
    ];
  }

  build() {
    Column() {
      Stack({ alignContent: Alignment.Top }) {
        Column()
          .width(GRADIENT_SPAN)
          .height(100)
          .linearGradient({
            direction: GradientDirection.Right,
            colors: this.gradientColors()
          })
          .position({
            x: -this.cardIndex * GRADIENT_CARD_SLOT + this.gradientScrollOffset / 3,
            y: 0
          })

        SnackImage({
          imageResource: this.snack.imageResource,
          contentDescription: this.snack.name,
          stableId: this.snack.stableId,
          collectionId: this.collectionId,
          imageSize: 120
        })
          .position({ x: 25, y: 40 })
      }
      .width('100%')
      .height(160)

      Text(this.snack.name)
        .fontFamily(MONTSERRAT_SEMIBOLD)
        .fontSize(20)
        .lineHeight(24)
        .fontColor(SECONDARY_TEXT_COLOR)
        .maxLines(1)
        .textOverflow({ overflow: TextOverflow.Ellipsis })
        .margin({ left: 16, right: 16, top: 8 })
        .width(138)

      Text(this.snack.tagline)
        .fontFamily(KARLA_REGULAR)
        .fontSize(16)
        .lineHeight(28)
        .letterSpacing(0.15)
        .fontColor(HELP_TEXT_COLOR)
        .margin({ left: 16, right: 16, top: 4 })
        .width(138)
    }
    .width(170)
    .height(250)
    .backgroundColor(BACKGROUND_COLOR)
    .borderRadius(20)
    .border({ width: 1, color: BORDER_COLOR })
    .clip(true)
    .id(this.collectionId <= 2 ? `snack.card.${this.snack.stableId}` :
      `snack.card.${this.collectionId}.${this.snack.stableId}`)
    .accessibilityText(this.snack.name)
    .accessibilityRole(AccessibilityRoleType.BUTTON)
    .onClick(() => {
      this.onOpen(this.snack.stableId, this.collectionId.toString());
    })
  }
}
