import { AppStore } from '../state/AppStore';
import {
  BACKGROUND_COLOR,
  BRAND_COLOR,
  FLOATED_COLOR,
  KARLA_BOLD,
  MONTSERRAT_MEDIUM,
  MONTSERRAT_SEMIBOLD,
  PRIMARY_TEXT_COLOR,
  SECONDARY_TEXT_COLOR
} from '../theme/JetsnackTheme';

const DEFAULT_FILTER_SORT: string = 'Android\'s favorite (default)';

interface FilterChoice {
  label: Resource;
  value: string;
  stableId: string;
}

interface SortChoice {
  label: Resource;
  value: string;
  stableId: string;
  iconResource: Resource;
}

const SORT_CHOICES: SortChoice[] = [
  {
    label: $r('app.string.android_favorites'),
    value: 'Android\'s favorite (default)',
    stableId: 'filter.sort.androidFavorite',
    iconResource: $r('app.media.ic_android')
  },
  {
    label: $r('app.string.rating'), value: 'Rating', stableId: 'filter.sort.rating',
    iconResource: $r('app.media.ic_star')
  },
  {
    label: $r('app.string.alphabetical'), value: 'Alphabetical', stableId: 'filter.sort.alphabetical',
    iconResource: $r('app.media.ic_sort_by_alpha')
  }
];

const PRICE_CHOICES: FilterChoice[] = [
  { label: $r('app.string.price_one'), value: '$', stableId: 'filter.price.one' },
  { label: $r('app.string.price_two'), value: '$$', stableId: 'filter.price.two' },
  { label: $r('app.string.price_three'), value: '$$$', stableId: 'filter.price.three' },
  { label: $r('app.string.price_four'), value: '$$$$', stableId: 'filter.price.four' }
];

const CATEGORY_CHOICES: FilterChoice[] = [
  { label: $r('app.string.category_chips'), value: 'Chips & crackers', stableId: 'filter.category.chips' },
  { label: $r('app.string.category_fruit'), value: 'Fruit snacks', stableId: 'filter.category.fruit' },
  { label: $r('app.string.category_desserts'), value: 'Desserts', stableId: 'filter.category.desserts' },
  { label: $r('app.string.category_nuts'), value: 'Nuts', stableId: 'filter.category.nuts' }
];

const LIFESTYLE_CHOICES: FilterChoice[] = [
  { label: $r('app.string.filter_organic'), value: 'Organic', stableId: 'filter.lifestyle.organic' },
  { label: $r('app.string.filter_gluten_free'), value: 'Gluten-free', stableId: 'filter.lifestyle.glutenFree' },
  { label: $r('app.string.filter_dairy_free'), value: 'Dairy-free', stableId: 'filter.lifestyle.dairyFree' },
  { label: $r('app.string.filter_sweet'), value: 'Sweet', stableId: 'filter.lifestyle.sweet' },
  { label: $r('app.string.filter_savory'), value: 'Savory', stableId: 'filter.lifestyle.savory' }
];

@Component
export struct FilterOverlay {
  @ObjectLink appStore: AppStore;
  @State filterChipHeight: number = 28;
  @State filterSortHeights: number[] = [38, 38, 38];
  @State pressedFilterId: string = '';

  private filterChipTouchHeight(): number {
    return Math.max(48, this.filterChipHeight);
  }

  private filterChipTouchTop(): number {
    return (this.filterChipHeight - this.filterChipTouchHeight()) / 2;
  }

  private filterSortHeight(index: number): number {
    return this.filterSortHeights[index] ?? 38;
  }

  private filterSortTouchHeight(index: number): number {
    return Math.max(48, this.filterSortHeight(index));
  }

  private filterSortTouchTop(index: number): number {
    return (this.filterSortHeight(index) - this.filterSortTouchHeight(index)) / 2;
  }

  private updateFilterPressed(stableId: string, eventType: TouchType): void {
    if (eventType === TouchType.Down) {
      this.pressedFilterId = stableId;
    } else if (eventType === TouchType.Up || eventType === TouchType.Cancel) {
      this.pressedFilterId = '';
    }
  }

  @Builder
  private sectionTitle(label: Resource) {
    Text(label)
      .fontFamily(MONTSERRAT_SEMIBOLD)
      .fontSize(20)
      .lineHeight(24)
      .fontColor(BRAND_COLOR)
      .width('100%')
      .margin({ bottom: 8 })
  }

  @Builder
  private sortChoice(choice: SortChoice, index: number) {
    Row() {
      Image(choice.iconResource)
        .width(24)
        .height(24)
        .fillColor(SECONDARY_TEXT_COLOR)

      Text(choice.label)
        .fontFamily(MONTSERRAT_SEMIBOLD)
        .fontSize(16)
        .lineHeight(24)
        .fontColor(SECONDARY_TEXT_COLOR)
        .margin({ left: 10 })
        .layoutWeight(1)

      if (this.appStore.filterSort === choice.value) {
        Image($r('app.media.ic_check'))
          .width(24)
          .height(24)
          .fillColor(BRAND_COLOR)
      }
    }
    .id(choice.stableId)
    .accessibilityText(choice.label)
    .accessibilityRole(AccessibilityRoleType.BUTTON)
    .accessibilitySelected(this.appStore.filterSort === choice.value)
    .width('100%')
    .constraintSize({ minHeight: 38 })
    .padding({ top: 14 })
    .responseRegion({
      x: 0,
      y: this.filterSortTouchTop(index),
      width: '100%',
      height: this.filterSortTouchHeight(index)
    })
    .onAreaChange((_oldValue: Area, newValue: Area) => {
      const height: number = Number(newValue.height);
      if (height > 0 && height !== this.filterSortHeight(index)) {
        const heights: number[] = this.filterSortHeights.slice();
        heights[index] = height;
        this.filterSortHeights = heights;
      }
    })
    .onClick(() => {
      this.appStore.selectFilterSort(choice.value);
      this.appStore.acknowledgeFilterApplyToFeed();
    })
  }

  @Builder
  private filterChip(choice: FilterChoice) {
    Stack({ alignContent: Alignment.Center }) {
      Text(choice.label)
        .fontFamily(KARLA_BOLD)
        .fontSize(12)
        .lineHeight(16)
        .letterSpacing(0.4)
        .fontColor(this.appStore.isFilterSelected(choice.value) ?
          $r('app.color.text_on_secondary') : SECONDARY_TEXT_COLOR)
        .padding({ left: 20, right: 20, top: 6, bottom: 6 })
    }
      .id(choice.stableId)
      .accessibilityText(choice.label)
      .accessibilityRole(AccessibilityRoleType.CHECKBOX)
      .accessibilityChecked(this.appStore.isFilterSelected(choice.value))
      .backgroundColor(this.appStore.isFilterSelected(choice.value) ?
        $r('app.color.filter_elevated_selected') : $r('app.color.filter_elevated_background'))
      .linearGradient({
        direction: GradientDirection.Right,
        colors: [
          [this.pressedFilterId === choice.stableId ? $r('app.color.filter_border_gradient_start') :
            (this.appStore.isFilterSelected(choice.value) ?
              $r('app.color.filter_elevated_selected') : $r('app.color.filter_elevated_background')), 0],
          [this.pressedFilterId === choice.stableId ? $r('app.color.filter_border_gradient_end') :
            (this.appStore.isFilterSelected(choice.value) ?
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
        width: this.appStore.isFilterSelected(choice.value) ? 0 : 2
      })
      .borderRadius('50%')
      .shadow(ShadowStyle.OUTER_DEFAULT_XS)
      .margin({ right: 4, bottom: 8 })
      .responseRegion({
        x: 0,
        y: this.filterChipTouchTop(),
        width: '100%',
        height: this.filterChipTouchHeight()
      })
      .onAreaChange((_oldValue: Area, newValue: Area) => {
        const height: number = Number(newValue.height);
        if (height > 0 && height !== this.filterChipHeight) {
          this.filterChipHeight = height;
        }
      })
      .onTouch((event: TouchEvent) => {
        this.updateFilterPressed(choice.stableId, event.type);
      })
      .onClick(() => {
        this.appStore.toggleFilterSelection(choice.value);
        this.appStore.acknowledgeFilterApplyToFeed();
      })
  }

  @Builder
  private chipGroup(choices: FilterChoice[]) {
    Flex({ wrap: FlexWrap.Wrap }) {
      ForEach(choices, (choice: FilterChoice) => {
        this.filterChip(choice)
      }, (choice: FilterChoice): string => choice.stableId)
    }
    .width('100%')
    .padding({ left: 4, right: 4, top: 12, bottom: 16 })
  }

  @Builder
  private panel() {
    Scroll() {
      Column() {
        Row() {
          Stack({ alignContent: Alignment.Center }) {
            Image($r('app.media.ic_close'))
              .width(24)
              .height(24)
              .fillColor(PRIMARY_TEXT_COLOR)
          }
          .id('filter.close')
          .accessibilityText($r('app.string.close'))
          .accessibilityRole(AccessibilityRoleType.BUTTON)
          .constraintSize({ minWidth: 48, minHeight: 48 })
          .onClick(() => {
            this.appStore.hideFilters();
          })

          Text($r('app.string.filters_title'))
            .fontFamily(MONTSERRAT_SEMIBOLD)
            .fontSize(20)
            .lineHeight(24)
            .fontColor(PRIMARY_TEXT_COLOR)
            .textAlign(TextAlign.Center)
            .layoutWeight(1)
            .constraintSize({ minHeight: 48 })
            .padding({ top: 8, right: 48 })

          Text($r('app.string.reset'))
            .id('action.filter.reset')
            .accessibilityText($r('app.string.reset'))
            .accessibilityRole(AccessibilityRoleType.BUTTON)
            .fontFamily(this.appStore.filterSort === DEFAULT_FILTER_SORT ?
              MONTSERRAT_MEDIUM : MONTSERRAT_SEMIBOLD)
            .fontSize(14)
            .lineHeight(20)
            .letterSpacing(0.25)
            .fontColor(BACKGROUND_COLOR)
            .opacity(this.appStore.filterSort === DEFAULT_FILTER_SORT ? 0.38 : 1)
            .constraintSize({ minWidth: 48, minHeight: 48 })
            .padding({ top: 14 })
            .enabled(this.appStore.filterSort !== DEFAULT_FILTER_SORT)
            .onClick(() => {
              this.appStore.acknowledgeFilterReset();
            })
        }
        .width('100%')
        .constraintSize({ minHeight: 48 })
        .alignItems(VerticalAlign.Center)

        this.sectionTitle($r('app.string.sort'))
        ForEach(SORT_CHOICES, (choice: SortChoice, index: number) => {
          this.sortChoice(choice, index)
        }, (choice: SortChoice): string => choice.stableId)
        Blank()
          .height(24)

        this.sectionTitle($r('app.string.price'))
        this.chipGroup(PRICE_CHOICES)

        this.sectionTitle($r('app.string.category'))
        this.chipGroup(CATEGORY_CHOICES)

        Row() {
          Text($r('app.string.max_calories'))
            .fontFamily(MONTSERRAT_SEMIBOLD)
            .fontSize(20)
            .lineHeight(24)
            .fontColor(BRAND_COLOR)
            .margin({ bottom: 8 })

          Text($r('app.string.per_serving'))
            .fontFamily(MONTSERRAT_MEDIUM)
            .fontSize(14)
            .lineHeight(20)
            .letterSpacing(0.25)
            .fontColor(BRAND_COLOR)
            .margin({ left: 10, top: 5 })
        }
        .width('100%')

        Slider({
          value: this.appStore.filterMaxCalories,
          min: 0,
          max: 300,
          step: 50,
          style: SliderStyle.OutSet
        })
          .id('filter.slider.maxCalories')
          .accessibilityText($r('app.string.max_calories'))
          .selectedColor(BRAND_COLOR)
          .blockColor(BRAND_COLOR)
          .trackColor($r('app.color.icon_interactive'))
          .trackThickness(16)
          .blockSize({ width: 4, height: 44 })
          .showSteps(true)
          .stepSize(4)
          .onChange((value: number) => {
            this.appStore.setFilterMaxCalories(value);
            this.appStore.acknowledgeFilterApplyToFeed();
          })

        this.sectionTitle($r('app.string.lifestyle'))
        this.chipGroup(LIFESTYLE_CHOICES)

      }
      .id('action.filter.applyToFeed')
      .accessibilityText($r('app.string.filters_title'))
      .width('100%')
      .padding({ left: 24, right: 24, top: 16, bottom: 16 })
      .onClick(() => {
        this.appStore.acknowledgeFilterApplyToFeed();
      })
    }
    .id('nav.filter')
    .width('calc(100% - 32vp)')
    .height('calc(100% - 32vp)')
    .constraintSize({ maxHeight: 450 })
    .backgroundColor(FLOATED_COLOR)
    .borderRadius(20)
    .scrollBar(BarState.Off)
  }

  build() {
    Stack({ alignContent: Alignment.Center }) {
      Column()
        .id('filter.scrim')
        .accessibilityText($r('app.string.close'))
        .width('100%')
        .height('100%')
        .backgroundColor($r('app.color.overlay_scrim'))
        .onClick(() => {
          this.appStore.hideFilters();
        })

      this.panel()
    }
    .id('overlay.filter')
    .accessibilityText($r('app.string.filters_title'))
    .width('100%')
    .height('100%')
  }
}
