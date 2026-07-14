import {
  BACKGROUND_COLOR,
  BRAND_COLOR,
  KARLA_BOLD,
  SECONDARY_TEXT_COLOR
} from '../theme/JetsnackTheme';
import { AppStore } from '../state/AppStore';

interface FeedFilterItem {
  label: Resource;
  stableId: string;
  value: string;
}

const FEED_FILTERS: FeedFilterItem[] = [
  { label: $r('app.string.filter_organic'), stableId: 'filter.quick.organic', value: 'Organic' },
  { label: $r('app.string.filter_gluten_free'), stableId: 'filter.quick.glutenFree', value: 'Gluten-free' },
  { label: $r('app.string.filter_dairy_free'), stableId: 'filter.quick.dairyFree', value: 'Dairy-free' },
  { label: $r('app.string.filter_sweet'), stableId: 'filter.quick.sweet', value: 'Sweet' },
  { label: $r('app.string.filter_savory'), stableId: 'filter.quick.savory', value: 'Savory' }
];

@Component
struct FeedFilterChip {
  @ObjectLink appStore: AppStore;
  @Prop label: Resource;
  @Prop stableId: string;
  @Prop value: string;
  @State renderedHeight: number = 28;
  @State pressed: boolean = false;

  private touchHeight(): number {
    return Math.max(48, this.renderedHeight);
  }

  private touchTop(): number {
    return (this.renderedHeight - this.touchHeight()) / 2;
  }

  build() {
    Stack({ alignContent: Alignment.Center }) {
      Text(this.label)
        .fontFamily(KARLA_BOLD)
        .fontSize(12)
        .lineHeight(16)
        .letterSpacing(0.4)
        .fontColor(this.appStore.isQuickFilterSelected(this.value) ?
          $r('app.color.text_on_secondary') : SECONDARY_TEXT_COLOR)
        .maxLines(1)
        .padding({ left: 20, right: 20, top: 6, bottom: 6 })
    }
      .id(this.stableId)
      .backgroundColor(this.appStore.isQuickFilterSelected(this.value) ?
        $r('app.color.filter_elevated_selected') : $r('app.color.filter_elevated_background'))
      .linearGradient({
        direction: GradientDirection.Right,
        colors: [
          [this.pressed ? $r('app.color.filter_border_gradient_start') :
            (this.appStore.isQuickFilterSelected(this.value) ?
              $r('app.color.filter_elevated_selected') : $r('app.color.filter_elevated_background')), 0],
          [this.pressed ? $r('app.color.filter_border_gradient_end') :
            (this.appStore.isQuickFilterSelected(this.value) ?
              $r('app.color.filter_elevated_selected') : $r('app.color.filter_elevated_background')), 1]
        ]
      })
      .borderImage({
        source: {
          direction: GradientDirection.RightBottom,
          colors: [
            [$r('app.color.filter_border_gradient_start'), 0],
            [$r('app.color.filter_border_gradient_end'), 1]
          ]
        },
        slice: 1,
        width: this.appStore.isQuickFilterSelected(this.value) ? 0 : 2
      })
      .borderRadius('50%')
      .shadow(ShadowStyle.OUTER_DEFAULT_XS)
      .accessibilityText(this.label)
      .accessibilityRole(AccessibilityRoleType.CHECKBOX)
      .accessibilityChecked(this.appStore.isQuickFilterSelected(this.value))
      .responseRegion({
        x: 0,
        y: this.touchTop(),
        width: '100%',
        height: this.touchHeight()
      })
      .onAreaChange((_oldValue: Area, newValue: Area) => {
        const height: number = Number(newValue.height);
        if (height > 0 && height !== this.renderedHeight) {
          this.renderedHeight = height;
        }
      })
      .onTouch((event: TouchEvent) => {
        if (event.type === TouchType.Down) {
          this.pressed = true;
        } else if (event.type === TouchType.Up || event.type === TouchType.Cancel) {
          this.pressed = false;
        }
      })
      .onClick(() => {
        this.appStore.toggleQuickFilterSelection(this.value);
      })
  }
}

@Component
export struct FilterBar {
  @ObjectLink appStore: AppStore;
  @Require
  onOpenFilters: () => void;

  build() {
    List({ space: 8 }) {
      if (!this.appStore.filterVisible) {
        ListItem() {
          Stack({ alignContent: Alignment.Center }) {
            Stack({ alignContent: Alignment.Center }) {
              Image($r('app.media.ic_filter_list'))
                .width(24)
                .height(24)
                .fillColor(BRAND_COLOR)
            }
            .width(24)
            .height(24)
            .borderImage({
              source: {
                direction: GradientDirection.RightBottom,
                colors: [
                  [$r('app.color.filter_border_gradient_start'), 0],
                  [$r('app.color.filter_border_gradient_end'), 1]
                ]
              },
              slice: 1,
              width: 2
            })
            .borderRadius('50%')
          }
          .width(48)
          .height(48)
          .id('feed.filters.open')
          .accessibilityText($r('app.string.label_filters'))
          .accessibilityRole(AccessibilityRoleType.BUTTON)
          .onClick(() => {
            this.onOpenFilters();
          })
        }
        .margin({ left: 12 })
      }

      ForEach(FEED_FILTERS, (filter: FeedFilterItem, index: number) => {
        ListItem() {
          FeedFilterChip({
            appStore: this.appStore,
            label: filter.label,
            stableId: filter.stableId,
            value: filter.value
          })
        }
        .margin({ right: index === FEED_FILTERS.length - 1 ? 8 : 0 })
      }, (filter: FeedFilterItem): string => filter.stableId)
    }
    .listDirection(Axis.Horizontal)
    .scrollBar(BarState.Off)
    .alignListItem(ListItemAlign.Center)
    .width('100%')
    .constraintSize({ minHeight: 56 })
    .backgroundColor(BACKGROUND_COLOR)
  }
}
