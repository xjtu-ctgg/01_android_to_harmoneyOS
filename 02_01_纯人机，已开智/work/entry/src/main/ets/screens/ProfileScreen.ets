import {
  BACKGROUND_COLOR,
  MONTSERRAT_MEDIUM,
  MONTSERRAT_SEMIBOLD,
  SECONDARY_TEXT_COLOR
} from '../theme/JetsnackTheme';

@Component
export struct ProfileScreen {
  build() {
    Column() {
      Image($r('app.media.empty_state_search'))
        .width('100%')
        .constraintSize({ maxWidth: 341 })
        .aspectRatio(341 / 179)
        .objectFit(ImageFit.Contain)
        .margin({ bottom: 24 })
        .accessibilityLevel('no')

      Text($r('app.string.work_in_progress'))
        .fontSize(16)
        .fontFamily(MONTSERRAT_SEMIBOLD)
        .lineHeight(24)
        .letterSpacing(0.15)
        .fontColor(SECONDARY_TEXT_COLOR)
        .textAlign(TextAlign.Center)
        .width('100%')
        .margin({ bottom: 16 })

      Text($r('app.string.grab_beverage'))
        .fontSize(14)
        .fontFamily(MONTSERRAT_MEDIUM)
        .lineHeight(20)
        .letterSpacing(0.25)
        .fontColor(SECONDARY_TEXT_COLOR)
        .textAlign(TextAlign.Center)
        .width('100%')
    }
    .id('screen.profile')
    .accessibilityText($r('app.string.home_profile_navigation'))
    .width('100%')
    .height('100%')
    .padding(24)
    .alignItems(HorizontalAlign.Center)
    .justifyContent(FlexAlign.Center)
    .backgroundColor(BACKGROUND_COLOR)
  }
}
