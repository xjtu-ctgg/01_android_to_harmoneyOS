import {
  SEARCH_CATEGORY_GROUPS,
  SEARCH_CATEGORY_VISUALS,
  SEARCH_SUGGESTION_GROUPS
} from '../data/SearchData';
import { SearchCategoryVisual } from '../data/SearchData';
import type { SearchGroup } from '../data/SearchData';
import { Snack } from '../model/Snack';
import { AppStore, SearchDisplay } from '../state/AppStore';
import {
  BACKGROUND_COLOR,
  BORDER_COLOR,
  BRAND_COLOR,
  FLOATED_COLOR,
  HELP_TEXT_COLOR,
  KARLA_REGULAR,
  MONTSERRAT_MEDIUM,
  MONTSERRAT_REGULAR,
  MONTSERRAT_SEMIBOLD,
  PRIMARY_TEXT_COLOR,
  SECONDARY_TEXT_COLOR
} from '../theme/JetsnackTheme';
import { formatPrice } from '../utils/CurrencyFormatter';
import { SnackImage } from '../components/SnackImage';

@Component
struct SearchCategoryCard {
  @Prop category: SearchCategoryVisual;
  @Prop groupIndex: number;
  @Prop itemIndex: number;
  @Prop gradientStart: ResourceColor;
  @Prop gradientEnd: ResourceColor;
  @Require
  onSelect: () => void;

  private actionId(): string {
    if (this.groupIndex === 0 && this.itemIndex === 0) {
      return 'action.search.category.select';
    }
    return `action.search.category.select.${this.groupIndex}.${this.itemIndex}`;
  }

  build() {
    Stack() {
      Row()
        .width('100%')
        .height('100%')
        .linearGradient({
          direction: GradientDirection.Right,
          colors: [
            [this.gradientStart, 0],
            [this.gradientEnd, 1]
          ]
        })

      Row() {
        Text(this.category.name)
          .fontFamily(MONTSERRAT_SEMIBOLD)
          .fontSize(16)
          .lineHeight(24)
          .letterSpacing(0.15)
          .fontColor(SECONDARY_TEXT_COLOR)
          .width('55%')
          .padding({ left: 12, right: 4 })

        Image(this.category.imageResource)
          .height('100%')
          .aspectRatio(1)
          .constraintSize({ minWidth: 134, minHeight: 134 })
          .borderRadius('50%')
          .objectFit(ImageFit.Cover)
          .accessibilityLevel('no')
      }
      .width('100%')
      .height('100%')
      .alignItems(VerticalAlign.Center)
    }
    .id(this.actionId())
    .accessibilityText(this.category.name)
    .accessibilityRole(AccessibilityRoleType.BUTTON)
    .width('100%')
    .aspectRatio(1.45)
    .borderRadius(10)
    .clip(true)
    .shadow(ShadowStyle.OUTER_DEFAULT_SM)
    .onClick(() => {
      this.onSelect();
    })
  }
}

@Component
struct SearchResultRow {
  @Prop snack: Snack;
  @Prop resultIndex: number;
  @Require
  onOpen: (stableId: number) => void;
  @Require
  onAdd: () => void;

  private addActionId(): string {
    if (this.resultIndex === 0) {
      return 'action.search.result.add';
    }
    return `action.search.result.add.${this.snack.stableId}`;
  }

  build() {
    Column() {
      if (this.resultIndex > 0) {
        Divider()
          .strokeWidth(1)
          .color(BORDER_COLOR)
      }

      Row() {
        SnackImage({
          imageResource: this.snack.imageResource,
          contentDescription: this.snack.name,
          stableId: this.snack.stableId,
          collectionId: 0,
          imageSize: 100
        })

        Column() {
          Text(this.snack.name)
            .fontFamily(MONTSERRAT_SEMIBOLD)
            .fontSize(16)
            .lineHeight(24)
            .letterSpacing(0.15)
            .fontColor(SECONDARY_TEXT_COLOR)

          Text(this.snack.tagline)
            .fontFamily(KARLA_REGULAR)
            .fontSize(16)
            .lineHeight(28)
            .letterSpacing(0.15)
            .fontColor(HELP_TEXT_COLOR)

          Text(formatPrice(this.snack.priceCents))
            .fontFamily(MONTSERRAT_SEMIBOLD)
            .fontSize(16)
            .lineHeight(24)
            .fontColor(PRIMARY_TEXT_COLOR)
            .margin({ top: 8 })
        }
        .layoutWeight(1)
        .padding({ left: 16, right: 16 })

        Stack({ alignContent: Alignment.Center }) {
          Image($r('app.media.ic_add'))
            .width(24)
            .height(24)
            .fillColor($r('app.color.text_interactive'))
        }
        .id(this.addActionId())
        .accessibilityText($r('app.string.label_add'))
        .accessibilityRole(AccessibilityRoleType.BUTTON)
        .width(36)
        .height(36)
        .responseRegion({ x: -6, y: -6, width: 48, height: 48 })
        .borderRadius(18)
        .linearGradient({
          direction: GradientDirection.Right,
          colors: [
            [$r('app.color.button_gradient_start'), 0],
            [$r('app.color.button_gradient_end'), 1]
          ]
        })
        .onTouch((event: TouchEvent) => {
          event.stopPropagation();
        })
        .monopolizeEvents(true)
        .onClick(() => {
          this.onAdd();
        })
      }
      .width('100%')
      .padding({ top: 16, bottom: 16 })
      .alignItems(VerticalAlign.Center)
    }
    .id(`search.result.${this.snack.stableId}`)
    .accessibilityText(this.snack.name)
    .width('100%')
    .padding({ left: 24, right: 24 })
    .onClick(() => {
      this.onOpen(this.snack.stableId);
    })
  }
}

@Component
export struct SearchScreen {
  @ObjectLink appStore: AppStore;
  @State searchViewportWidth: number = 360;

  aboutToAppear(): void {
    if (this.appStore.searchResults.length === 0) {
      this.appStore.refreshSearchResults();
    }
  }

  private categoryVisual(name: string): SearchCategoryVisual {
    const visual: SearchCategoryVisual | undefined = SEARCH_CATEGORY_VISUALS.find(
      (candidate: SearchCategoryVisual): boolean => candidate.name === name);
    if (visual !== undefined) {
      return visual;
    }
    const fallback: SearchCategoryVisual = {
      name: name,
      imageResource: $r('app.media.placeholder')
    };
    return fallback;
  }

  private gradientStart(groupIndex: number): ResourceColor {
    if (groupIndex === 0) {
      return $r('app.color.search_gradient_one_start');
    }
    return $r('app.color.search_gradient_two_start');
  }

  private gradientEnd(groupIndex: number): ResourceColor {
    if (groupIndex === 0) {
      return $r('app.color.search_gradient_one_end');
    }
    return $r('app.color.search_gradient_two_end');
  }

  private categoryGridHeight(itemCount: number): number {
    const rowCount: number = Math.ceil(itemCount / 2);
    const cardWidth: number = Math.max(0, this.searchViewportWidth / 2 - 32);
    return rowCount * (cardWidth / 1.45 + 16);
  }

  @Builder
  private searchHint() {
    Row() {
      Image($r('app.media.ic_search'))
        .width(24)
        .height(24)
        .fillColor(HELP_TEXT_COLOR)
        .accessibilityLevel('no')

      Blank()
        .width(8)

      Text($r('app.string.search_jetsnack'))
        .fontFamily(MONTSERRAT_REGULAR)
        .fontSize(16)
        .fontColor(HELP_TEXT_COLOR)
    }
    .height('100%')
    .alignItems(VerticalAlign.Center)
  }

  @Builder
  private searchBar() {
    Row() {
      Stack({ alignContent: Alignment.Center }) {
        if (this.appStore.searchQuery.length === 0) {
          this.searchHint()
        }

        Row() {
          if (this.appStore.searchFocused) {
            Stack({ alignContent: Alignment.Center }) {
              Image($r('app.media.ic_arrow_back'))
                .width(24)
                .height(24)
                .fillColor(BRAND_COLOR)
            }
            .id('search.clear')
            .accessibilityText($r('app.string.label_back'))
            .accessibilityRole(AccessibilityRoleType.BUTTON)
            .width(48)
            .height(40)
            .responseRegion({ x: 0, y: -4, width: 48, height: 48 })
            .onClick(() => {
              this.appStore.clearSearchQuery();
            })
          }

          TextInput({
            text: this.appStore.searchQuery,
            placeholder: ''
          })
            .id('search.input')
            .accessibilityText($r('app.string.label_search'))
            .layoutWeight(1)
            .height(40)
            .fontFamily(MONTSERRAT_REGULAR)
            .fontSize(16)
            .fontColor(SECONDARY_TEXT_COLOR)
            .caretColor(BRAND_COLOR)
            .backgroundColor(Color.Transparent)
            .onFocus(() => {
              this.appStore.setSearchFocused(true);
            })
            .onBlur(() => {
              this.appStore.setSearchFocused(false);
            })
            .onChange((value: string) => {
              this.appStore.setSearchQuery(value);
            })

          if (this.appStore.searching) {
            LoadingProgress()
              .width(36)
              .height(36)
              .color(BRAND_COLOR)
              .margin({ left: 6, right: 6 })
          } else {
            Blank()
              .width(48)
          }
        }
        .width('100%')
        .height(40)
        .alignItems(VerticalAlign.Center)
      }
      .width('100%')
      .height(40)
      .borderRadius(20)
      .backgroundColor(FLOATED_COLOR)
    }
    .width('100%')
    .height(56)
    .padding({ left: 24, right: 24, top: 8, bottom: 8 })
    .backgroundColor(BACKGROUND_COLOR)
  }

  @Builder
  private searchCategories() {
    List() {
      ForEach(SEARCH_CATEGORY_GROUPS, (group: SearchGroup, groupIndex: number) => {
        ListItem() {
          Column() {
            Row() {
              Text(group.name)
                .fontFamily(MONTSERRAT_SEMIBOLD)
                .fontSize(20)
                .lineHeight(24)
                .fontColor(PRIMARY_TEXT_COLOR)
                .width('100%')
            }
            .width('100%')
            .constraintSize({ minHeight: 56 })
            .padding({ left: 24, right: 24, top: 4, bottom: 4 })
            .alignItems(VerticalAlign.Center)

            Grid() {
              ForEach(group.items, (name: string, itemIndex: number) => {
                GridItem() {
                  SearchCategoryCard({
                    category: this.categoryVisual(name),
                    groupIndex: groupIndex,
                    itemIndex: itemIndex,
                    gradientStart: this.gradientStart(groupIndex),
                    gradientEnd: this.gradientEnd(groupIndex),
                    onSelect: () => {
                      this.appStore.acknowledgeSearchCategory();
                    }
                  })
                    .margin(8)
                }
              }, (name: string): string => `${group.name}.${name}`)
            }
            .columnsTemplate('1fr 1fr')
            .columnsGap(0)
            .rowsGap(0)
            .width('100%')
            .height(this.categoryGridHeight(group.items.length))
            .padding({ left: 16, right: 16 })
            .scrollBar(BarState.Off)

            Blank()
              .height(4)
          }
        }
      }, (group: SearchGroup): string => group.name)
    }
    .width('100%')
    .layoutWeight(1)
    .scrollBar(BarState.Off)
  }

  @Builder
  private searchSuggestions() {
    List() {
      ForEach(SEARCH_SUGGESTION_GROUPS, (group: SearchGroup) => {
        ListItem() {
          Column() {
            Row() {
              Text(group.name)
                .fontFamily(MONTSERRAT_SEMIBOLD)
                .fontSize(20)
                .lineHeight(24)
                .fontColor(PRIMARY_TEXT_COLOR)
                .width('100%')
            }
            .width('100%')
            .constraintSize({ minHeight: 56 })
            .padding({ left: 24, right: 24, top: 4, bottom: 4 })
            .alignItems(VerticalAlign.Center)

            ForEach(group.items, (suggestion: string) => {
              Row() {
                Text(suggestion)
                  .fontFamily(MONTSERRAT_SEMIBOLD)
                  .fontSize(16)
                  .lineHeight(24)
                  .letterSpacing(0.15)
                  .fontColor(SECONDARY_TEXT_COLOR)
                  .width('100%')
              }
              .id(`search.suggestion.${suggestion}`)
              .accessibilityText(suggestion)
              .accessibilityRole(AccessibilityRoleType.BUTTON)
              .width('100%')
              .constraintSize({ minHeight: 48 })
              .padding({ left: 24, right: 24 })
              .alignItems(VerticalAlign.Center)
              .onClick(() => {
                this.appStore.selectSearchSuggestion(suggestion);
              })
            }, (suggestion: string): string => suggestion)

            Blank()
              .height(4)
          }
        }
      }, (group: SearchGroup): string => group.name)
    }
    .width('100%')
    .layoutWeight(1)
    .scrollBar(BarState.Off)
  }

  @Builder
  private searchResults() {
    List() {
      ListItem() {
        Text($r('app.string.search_count', this.appStore.searchResults.length))
          .fontFamily(MONTSERRAT_SEMIBOLD)
          .fontSize(20)
          .lineHeight(24)
          .fontColor(PRIMARY_TEXT_COLOR)
          .width('100%')
          .padding({ left: 24, right: 24, top: 4, bottom: 4 })
      }

      ForEach(this.appStore.searchResults, (snack: Snack, index: number) => {
        ListItem() {
          SearchResultRow({
            snack: snack,
            resultIndex: index,
            onOpen: (stableId: number) => {
              this.appStore.openDetail(stableId, 'search');
            },
            onAdd: () => {
              this.appStore.acknowledgeSearchResultAdd();
            }
          })
        }
      }, (snack: Snack): string => snack.stableId.toString())
    }
    .width('100%')
    .layoutWeight(1)
    .scrollBar(BarState.Off)
  }

  @Builder
  private noResults() {
    Column() {
      Image($r('app.media.empty_state_search'))
        .width('100%')
        .constraintSize({ maxWidth: 341 })
        .aspectRatio(341 / 179)
        .objectFit(ImageFit.Contain)
        .margin({ bottom: 24 })
        .accessibilityLevel('no')

      Text($r('app.string.search_no_matches', this.appStore.searchQuery))
        .fontFamily(MONTSERRAT_SEMIBOLD)
        .fontSize(16)
        .lineHeight(24)
        .letterSpacing(0.15)
        .fontColor(SECONDARY_TEXT_COLOR)
        .textAlign(TextAlign.Center)
        .width('100%')
        .margin({ bottom: 16 })

      Text($r('app.string.search_no_matches_retry'))
        .fontFamily(MONTSERRAT_MEDIUM)
        .fontSize(14)
        .lineHeight(20)
        .letterSpacing(0.25)
        .fontColor(SECONDARY_TEXT_COLOR)
        .textAlign(TextAlign.Center)
        .width('100%')
    }
    .width('100%')
    .layoutWeight(1)
    .padding(24)
    .alignItems(HorizontalAlign.Center)
    .justifyContent(FlexAlign.Center)
  }

  build() {
    Column() {
      this.searchBar()

      Divider()
        .strokeWidth(1)
        .color(BORDER_COLOR)

      if (this.appStore.getSearchDisplay() === SearchDisplay.CATEGORIES) {
        this.searchCategories()
      } else if (this.appStore.getSearchDisplay() === SearchDisplay.SUGGESTIONS) {
        this.searchSuggestions()
      } else if (this.appStore.getSearchDisplay() === SearchDisplay.RESULTS) {
        this.searchResults()
      } else if (this.appStore.getSearchDisplay() === SearchDisplay.NO_RESULTS) {
        this.noResults()
      }
    }
    .id('screen.search')
    .accessibilityText($r('app.string.home_search_navigation'))
    .width('100%')
    .height('100%')
    .backgroundColor(BACKGROUND_COLOR)
    .onAreaChange((_oldArea: Area, newArea: Area) => {
      const width: number = Number(newArea.width);
      if (width > 0) {
        this.searchViewportWidth = width;
      }
    })
  }
}
