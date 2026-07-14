import { i18n } from '@kit.LocalizationKit';
import { QuantitySelector } from '../components/QuantitySelector';
import { SnackCollection } from '../components/SnackCollection';
import { RELATED_COLLECTIONS, SNACKS, getSnackById } from '../data/SnackData';
import type { Snack, SnackCollection as SnackCollectionModel } from '../model/Snack';
import { AppStore } from '../state/AppStore';
import {
  BACKGROUND_COLOR,
  BORDER_COLOR,
  BRAND_COLOR,
  HELP_TEXT_COLOR,
  KARLA_BOLD,
  KARLA_REGULAR,
  MONTSERRAT_SEMIBOLD,
  PRIMARY_TEXT_COLOR,
  SECONDARY_TEXT_COLOR
} from '../theme/JetsnackTheme';
import { formatPrice } from '../utils/CurrencyFormatter';

@Component
export struct DetailScreen {
  @ObjectLink appStore: AppStore;
  @Prop topInset: number;
  @Prop leftInset: number;
  @Prop rightInset: number;
  @State detailScrollOffset: number = 0;
  @State detailViewportWidth: number = 360;
  @State expansionControlHeight: number = 31;
  @State addButtonHeight: number = 40;
  private detailScroller: Scroller = new Scroller();

  private expansionTouchHeight(): number {
    return Math.max(48, this.expansionControlHeight);
  }

  private expansionTouchTop(): number {
    return (this.expansionControlHeight - this.expansionTouchHeight()) / 2;
  }

  private addButtonTouchHeight(): number {
    return Math.max(48, this.addButtonHeight);
  }

  private addButtonTouchTop(): number {
    return (this.addButtonHeight - this.addButtonTouchHeight()) / 2;
  }

  private collapseFraction(): number {
    return Math.min(Math.max(this.detailScrollOffset / 295, 0), 1);
  }

  private detailSafeWidth(): number {
    return Math.max(0, this.detailViewportWidth - this.leftInset - this.rightInset);
  }

  private detailImageSize(): number {
    const expandedSize: number = Math.max(0, Math.min(300, this.detailSafeWidth() - 48));
    const collapsedSize: number = Math.min(150, expandedSize);
    return expandedSize - (expandedSize - collapsedSize) * this.collapseFraction();
  }

  private detailImageOffsetY(): number {
    return this.topInset + 56 - 44 * this.collapseFraction();
  }

  private isRtlLayout(): boolean {
    const systemLanguage: string = i18n.System.getSystemLanguage();
    return i18n.isRTL(systemLanguage);
  }

  private detailImageOffsetX(): number {
    const imageSize: number = this.detailImageSize();
    const expandedX: number = this.leftInset + (this.detailSafeWidth() - imageSize) / 2;
    const collapsedX: number = this.isRtlLayout() ? this.leftInset + 24 :
      this.detailViewportWidth - this.rightInset - 24 - imageSize;
    return expandedX + (collapsedX - expandedX) * this.collapseFraction();
  }

  private detailTitleOffsetY(): number {
    return this.topInset + Math.max(56, 351 - this.detailScrollOffset);
  }

  private selectedSnack(): Snack {
    if (this.appStore.selectedSnackId !== undefined) {
      const selected: Snack | undefined = getSnackById(this.appStore.selectedSnackId);
      if (selected !== undefined) {
        return selected;
      }
    }
    return SNACKS[0];
  }

  private expansionLabel(): Resource {
    if (this.appStore.detailExpanded) {
      return $r('app.string.see_less');
    }
    return $r('app.string.see_more');
  }

  private relatedActionId(index: number): string {
    if (index === 0) {
      return 'action.detail.related.select';
    }
    return `action.detail.related.select.${index}`;
  }

  @Builder
  private detailGradient() {
    Column()
      .width('100%')
      .height(280)
      .linearGradient({
        angle: 135,
        colors: [
          [$r('app.color.detail_gradient_start'), 0],
          [$r('app.color.detail_gradient_end'), 1]
        ]
      })
      .blur(40)
      .align(Alignment.Top)
  }

  @Builder
  private detailImage(snack: Snack) {
    Image(snack.imageResource)
      .id(`snack.image.${snack.stableId}`)
      .accessibilityText('')
      .accessibilityLevel('no')
      .width(this.detailImageSize())
      .height(this.detailImageSize())
      .borderRadius(this.detailImageSize() / 2)
      .objectFit(ImageFit.Cover)
      .position({ x: this.detailImageOffsetX(), y: this.detailImageOffsetY() })
    .align(Alignment.Top)
  }

  @Builder
  private detailTitle(snack: Snack) {
    Column() {
        Blank()
          .height(16)

        Text(snack.name)
          .fontFamily(MONTSERRAT_SEMIBOLD)
          .fontSize(30)
          .lineHeight(37)
          .fontStyle(FontStyle.Italic)
          .fontColor(SECONDARY_TEXT_COLOR)
          .width('100%')
          .padding({ left: this.leftInset + 24, right: this.rightInset + 24 })

        Text(snack.tagline)
          .fontFamily(KARLA_BOLD)
          .fontSize(20)
          .lineHeight(24)
          .fontStyle(FontStyle.Italic)
          .fontColor(HELP_TEXT_COLOR)
          .width('100%')
          .padding({ left: this.leftInset + 24, right: this.rightInset + 24 })

        Text(formatPrice(snack.priceCents))
          .fontFamily(MONTSERRAT_SEMIBOLD)
          .fontSize(20)
          .lineHeight(24)
          .fontColor(PRIMARY_TEXT_COLOR)
          .width('100%')
          .padding({ left: this.leftInset + 24, right: this.rightInset + 24 })
          .margin({ top: 4, bottom: 8 })

        Divider()
          .strokeWidth(1)
          .color(BORDER_COLOR)
      }
      .width('100%')
      .constraintSize({ minHeight: 128 })
      .position({ y: this.detailTitleOffsetY() })
      .backgroundColor(BACKGROUND_COLOR)
      .align(Alignment.Top)
  }

  @Builder
  private detailBackButton() {
    Stack({ alignContent: Alignment.Center }) {
      Image($r('app.media.ic_arrow_back'))
        .width(24)
        .height(24)
        .fillColor($r('app.color.icon_interactive'))
    }
    .id('detail.back')
    .accessibilityText($r('app.string.label_back'))
    .accessibilityRole(AccessibilityRoleType.BUTTON)
    .width(36)
    .height(36)
    .responseRegion({ x: -6, y: -6, width: 48, height: 48 })
    .margin({ left: this.leftInset + 16, top: this.topInset + 10 })
    .borderRadius(18)
    .backgroundColor($r('app.color.button_scrim'))
    .align(Alignment.TopStart)
    .onClick(() => {
      this.appStore.goBack();
    })
  }

  @Builder
  private detailBody() {
    Column() {
      Text($r('app.string.detail_header'))
        .fontFamily(MONTSERRAT_SEMIBOLD)
        .fontSize(12)
        .lineHeight(16)
        .letterSpacing(1)
        .fontColor(HELP_TEXT_COLOR)
        .width('100%')

      Text($r('app.string.detail_placeholder'))
        .fontFamily(KARLA_REGULAR)
        .fontSize(16)
        .lineHeight(28)
        .letterSpacing(0.15)
        .fontColor(HELP_TEXT_COLOR)
        .maxLines(this.appStore.detailExpanded ? 100 : 5)
        .textOverflow({ overflow: TextOverflow.Ellipsis })
        .width('100%')
        .margin({ top: 16 })

      Text(this.expansionLabel())
        .id('detail.seeMore')
        .accessibilityText(this.expansionLabel())
        .accessibilityRole(AccessibilityRoleType.BUTTON)
        .fontFamily(MONTSERRAT_SEMIBOLD)
        .fontSize(14)
        .lineHeight(16)
        .letterSpacing(1.25)
        .fontColor($r('app.color.text_link'))
        .textAlign(TextAlign.Center)
        .width('100%')
        .constraintSize({ minHeight: 20 })
        .padding({ top: 15 })
        .responseRegion({
          x: 0,
          y: this.expansionTouchTop(),
          width: '100%',
          height: this.expansionTouchHeight()
        })
        .onAreaChange((_oldValue: Area, newValue: Area) => {
          const height: number = Number(newValue.height);
          if (height > 0 && height !== this.expansionControlHeight) {
            this.expansionControlHeight = height;
          }
        })
        .onClick(() => {
          this.appStore.toggleDetailExpanded();
        })

      Text($r('app.string.ingredients'))
        .fontFamily(MONTSERRAT_SEMIBOLD)
        .fontSize(12)
        .lineHeight(16)
        .letterSpacing(1)
        .fontColor(HELP_TEXT_COLOR)
        .width('100%')
        .margin({ top: 40 })

      Text($r('app.string.ingredients_list'))
        .fontFamily(KARLA_REGULAR)
        .fontSize(16)
        .lineHeight(28)
        .letterSpacing(0.15)
        .fontColor(HELP_TEXT_COLOR)
        .width('100%')
        .margin({ top: 4, bottom: 16 })
    }
    .width('100%')
    .padding({ left: 24, right: 24, top: 16 })
    .backgroundColor(BACKGROUND_COLOR)
  }

  @Builder
  private relatedCollections() {
    ForEach(RELATED_COLLECTIONS, (collection: SnackCollectionModel, index: number) => {
      Column() {
        SnackCollection({
          collection: collection,
          onOpen: () => {
            this.appStore.acknowledgeDetailRelated();
          }
        })
      }
      .id(this.relatedActionId(index))
      .accessibilityText(collection.name)
      .accessibilityRole(AccessibilityRoleType.BUTTON)
      .onClick(() => {
        this.appStore.acknowledgeDetailRelated();
      })
    }, (collection: SnackCollectionModel): string => collection.stableId.toString())
  }

  @Builder
  private cartBottomBar() {
    Column() {
      Divider()
        .strokeWidth(1)
        .color(BORDER_COLOR)

      Row() {
        QuantitySelector({
          count: this.appStore.detailQuantity,
          stableIdPrefix: 'detail.quantity',
          onDecrease: () => {
            this.appStore.decrementDetailQuantity();
          },
          onIncrease: () => {
            this.appStore.incrementDetailQuantity();
          }
        })

        Text($r('app.string.add_to_cart'))
          .id('action.detail.addToCart')
          .accessibilityText($r('app.string.add_to_cart'))
          .accessibilityRole(AccessibilityRoleType.BUTTON)
          .fontFamily(MONTSERRAT_SEMIBOLD)
          .fontSize(14)
          .lineHeight(16)
          .letterSpacing(1.25)
          .fontColor($r('app.color.text_interactive'))
          .textAlign(TextAlign.Center)
          .maxLines(1)
          .layoutWeight(1)
          .constraintSize({ minHeight: 40 })
          .padding({ left: 24, right: 24, top: 8, bottom: 8 })
          .borderRadius('50%')
          .linearGradient({
            direction: GradientDirection.Right,
            colors: [
              [$r('app.color.button_gradient_start'), 0],
              [$r('app.color.button_gradient_end'), 1]
            ]
          })
          .margin({ left: 16 })
          .responseRegion({
            x: 0,
            y: this.addButtonTouchTop(),
            width: '100%',
            height: this.addButtonTouchHeight()
          })
          .onAreaChange((_oldValue: Area, newValue: Area) => {
            const height: number = Number(newValue.height);
            if (height > 0 && height !== this.addButtonHeight) {
              this.addButtonHeight = height;
            }
          })
          .onClick(() => {
            this.appStore.acknowledgeDetailAddToCart();
          })
      }
      .width('100%')
      .constraintSize({ minHeight: 56 })
      .padding({ left: 24, right: 24 })
      .alignItems(VerticalAlign.Center)
      .backgroundColor(BACKGROUND_COLOR)
    }
    .width('100%')
  }

  build() {
    Stack({ alignContent: Alignment.Bottom }) {
      this.detailGradient()

      Scroll(this.detailScroller) {
        Column() {
          Blank()
            .height(this.topInset + 495)

          this.detailBody()

          Divider()
            .strokeWidth(1)
            .color(BORDER_COLOR)

          this.relatedCollections()

          Blank()
            .height(64)
        }
        .width('100%')
      }
      .id('nav.detail')
      .width('100%')
      .height('100%')
      .scrollBar(BarState.Off)
      .onDidScroll((_scrollOffset: number, _scrollState: ScrollState) => {
        this.detailScrollOffset = Math.max(0, this.detailScroller.currentOffset().yOffset);
      })

      this.detailTitle(this.selectedSnack())
      this.detailImage(this.selectedSnack())
      this.detailBackButton()

      this.cartBottomBar()
    }
    .id('screen.detail')
    .accessibilityText($r('app.string.detail_header'))
    .width('100%')
    .height('100%')
    .backgroundColor(BACKGROUND_COLOR)
    .onAreaChange((_oldArea: Area, newArea: Area) => {
      const width: number = Number(newArea.width);
      if (width > 0) {
        this.detailViewportWidth = width;
      }
    })
  }
}
