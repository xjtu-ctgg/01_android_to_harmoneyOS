import { getSnacksByStableIds } from '../data/SnackData';
import { CollectionType, SnackCollection as SnackCollectionModel } from '../model/Snack';
import type { Snack } from '../model/Snack';
import {
  BACKGROUND_COLOR,
  MONTSERRAT_SEMIBOLD,
  SECONDARY_TEXT_COLOR
} from '../theme/JetsnackTheme';
import { SnackCard } from './SnackCard';
import { SnackImage } from './SnackImage';

@Component
export struct SnackCollection {
  @Prop collection: SnackCollectionModel;
  @Require
  onOpen: (stableId: number, origin: string) => void;
  @State highlightScrollOffset: number = 0;
  private highlightScroller: Scroller = new Scroller();
  private collectionActionCount: number = 0;

  private acknowledgeCollectionAction(): void {
    this.collectionActionCount += 1;
  }

  private collectionSnacks(): Snack[] {
    return getSnacksByStableIds(this.collection.snackStableIds);
  }

  private usesAlternateGradient(): boolean {
    return this.collection.stableId === 3 || this.collection.stableId === 4;
  }

  private gradientStart(): ResourceColor {
    if (this.usesAlternateGradient()) {
      return $r('app.color.gradient_rose_start');
    }
    return $r('app.color.gradient_shadow_start');
  }

  private gradientMiddle(): ResourceColor {
    if (this.usesAlternateGradient()) {
      return $r('app.color.gradient_rose_middle');
    }
    return $r('app.color.gradient_shadow_middle');
  }

  private gradientBridge(): ResourceColor {
    if (this.usesAlternateGradient()) {
      return $r('app.color.gradient_lavender_middle');
    }
    return $r('app.color.gradient_ocean_middle');
  }

  private collectionActionId(): string {
    if (this.collection.stableId === 1) {
      return 'action.feed.collection';
    }
    return `action.feed.collection.${this.collection.stableId}`;
  }

  @Builder
  private normalSnack(snack: Snack) {
    Column() {
      SnackImage({
        imageResource: snack.imageResource,
        contentDescription: snack.name,
        stableId: snack.stableId,
        collectionId: this.collection.stableId,
        imageSize: 120,
        hasMiniShadow: true
      })

      Text(snack.name)
        .fontFamily(MONTSERRAT_SEMIBOLD)
        .fontSize(16)
        .lineHeight(24)
        .letterSpacing(0.15)
        .fontColor(SECONDARY_TEXT_COLOR)
        .margin({ top: 8 })
    }
    .padding(8)
    .backgroundColor(BACKGROUND_COLOR)
    .borderRadius(20)
    .id(this.collection.stableId <= 2 ? `snack.card.${snack.stableId}` :
      `snack.card.${this.collection.stableId}.${snack.stableId}`)
    .accessibilityText(snack.name)
    .accessibilityRole(AccessibilityRoleType.BUTTON)
    .onClick(() => {
      this.onOpen(snack.stableId, this.collection.stableId.toString());
    })
  }

  build() {
    Column() {
      Row() {
        Text(this.collection.name)
          .fontFamily(MONTSERRAT_SEMIBOLD)
          .fontSize(20)
          .lineHeight(24)
          .fontColor($r('app.color.brand_primary'))
          .maxLines(1)
          .textOverflow({ overflow: TextOverflow.Ellipsis })
          .layoutWeight(1)

        Stack({ alignContent: Alignment.Center }) {
          Image($r('app.media.ic_arrow_back'))
            .width(24)
            .height(24)
            .fillColor($r('app.color.brand_primary'))
        }
        .width(48)
        .height(48)
        .id(this.collectionActionId())
        .accessibilityText($r('app.string.view_collection', this.collection.name))
        .accessibilityRole(AccessibilityRoleType.BUTTON)
        .onClick(() => {
          this.acknowledgeCollectionAction();
        })
      }
      .width('100%')
      .constraintSize({ minHeight: 56 })
      .padding({ left: 24 })
      .alignItems(VerticalAlign.Center)

      if (this.collection.type === CollectionType.HIGHLIGHT) {
        List({ space: 16, scroller: this.highlightScroller }) {
          ForEach(this.collectionSnacks(), (snack: Snack, index: number) => {
            ListItem() {
              SnackCard({
                snack: snack,
                collectionId: this.collection.stableId,
                cardIndex: index,
                gradientScrollOffset: this.highlightScrollOffset,
                gradientStart: this.gradientStart(),
                gradientBridge: this.gradientBridge(),
                gradientMiddle: this.gradientMiddle(),
                onOpen: this.onOpen
              })
                .margin({
                  left: index === 0 ? 24 : 0,
                  right: index === this.collection.snackStableIds.length - 1 ? 24 : 0,
                  bottom: 16
                })
            }
          }, (snack: Snack): string => snack.stableId.toString())
        }
        .listDirection(Axis.Horizontal)
        .scrollBar(BarState.Off)
        .width('100%')
        .height(266)
        .onDidScroll((_scrollOffset: number, _scrollState: ScrollState) => {
          this.highlightScrollOffset = Math.max(0, this.highlightScroller.currentOffset().xOffset);
        })
      } else {
        List({ space: 0 }) {
          ForEach(this.collectionSnacks(), (snack: Snack, index: number) => {
            ListItem() {
              this.normalSnack(snack)
            }
            .margin({
              left: index === 0 ? 12 : 4,
              right: index === this.collection.snackStableIds.length - 1 ? 12 : 4,
              bottom: 8
            })
          }, (snack: Snack): string => snack.stableId.toString())
        }
        .listDirection(Axis.Horizontal)
        .scrollBar(BarState.Off)
        .width('100%')
        .constraintSize({ minHeight: 176 })
      }
    }
    .width('100%')
    .backgroundColor(BACKGROUND_COLOR)
    .id(`feed.collection.${this.collection.stableId}`)
    .accessibilityText(this.collection.name)
  }
}
