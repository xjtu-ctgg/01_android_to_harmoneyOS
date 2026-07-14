import { SNACK_COLLECTIONS } from '../data/SnackData';
import type { SnackCollection as SnackCollectionModel } from '../model/Snack';
import { AppStore } from '../state/AppStore';
import { BACKGROUND_COLOR, BORDER_COLOR } from '../theme/JetsnackTheme';
import { DestinationBar } from '../components/DestinationBar';
import { FilterBar } from '../components/FilterBar';
import { SnackCollection } from '../components/SnackCollection';

@Component
export struct FeedScreen {
  @ObjectLink appStore: AppStore;

  build() {
    Stack({ alignContent: Alignment.Top }) {
      List() {
        ListItem() {
          Column() {
            Blank()
              .height(56)

            FilterBar({
              appStore: this.appStore,
              onOpenFilters: () => {
                this.appStore.showFilters();
              }
            })
          }
        }

        ForEach(SNACK_COLLECTIONS, (collection: SnackCollectionModel, index: number) => {
          ListItem() {
            Column() {
              if (index > 0) {
                Divider()
                  .strokeWidth(2)
                  .color(BORDER_COLOR)
              }
              SnackCollection({
                collection: collection,
                onOpen: (stableId: number, origin: string) => {
                  this.appStore.openDetail(stableId, origin);
                }
              })
            }
          }
        }, (collection: SnackCollectionModel): string => collection.stableId.toString())
      }
      .width('100%')
      .height('100%')
      .scrollBar(BarState.Off)
      .edgeEffect(EdgeEffect.Spring)

      DestinationBar()
        .align(Alignment.Top)
    }
    .id('screen.feed')
    .accessibilityText($r('app.string.home_feed_navigation'))
    .width('100%')
    .height('100%')
    .backgroundColor(BACKGROUND_COLOR)
  }
}
