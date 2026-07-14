export class RecentOrderFormItem {
  stableKey: string;
  title: string;
  supportingText: string;
  image: Resource;
  orderKey: string;

  constructor(stableKey: string, title: string, supportingText: string, image: Resource, orderKey: string) {
    this.stableKey = stableKey;
    this.title = title;
    this.supportingText = supportingText;
    this.image = image;
    this.orderKey = orderKey;
  }
}

export const RECENT_ORDER_FORM_ITEMS: RecentOrderFormItem[] = [
  new RecentOrderFormItem('1', 'Cupcake', 'Cupcake, Apples', $r('app.media.cupcake'), '0 20'),
  new RecentOrderFormItem('2', 'Donut', 'Donut, Apple sauce', $r('app.media.donut'), '1 21'),
  new RecentOrderFormItem('3', 'Eclair', 'Eclair, Apple chips', $r('app.media.eclair'), '2 22'),
  new RecentOrderFormItem('4', 'Froyo', 'Froyo, Apple juice', $r('app.media.froyo'), '3 23'),
  new RecentOrderFormItem('5', 'Gingerbread', 'Gingerbread, Apple pie', $r('app.media.gingerbread'), '4 24')
];
