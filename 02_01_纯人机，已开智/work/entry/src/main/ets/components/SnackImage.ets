@Component
export struct SnackImage {
  @Prop imageResource: Resource;
  @Prop contentDescription: string;
  @Prop stableId: number;
  @Prop collectionId: number = 0;
  @Prop imageSize: number = 120;
  @Prop hasMiniShadow: boolean = false;

  private imageShadow(): ShadowOptions | ShadowStyle {
    if (this.hasMiniShadow) {
      return ShadowStyle.OUTER_DEFAULT_XS;
    }
    return { radius: 0 };
  }

  build() {
    Image(this.imageResource)
      .width(this.imageSize)
      .height(this.imageSize)
      .borderRadius(this.imageSize / 2)
      .objectFit(ImageFit.Cover)
      .shadow(this.imageShadow())
      .id(this.collectionId <= 2 ? `snack.image.${this.stableId}` :
        `snack.image.${this.collectionId}.${this.stableId}`)
      .accessibilityText(this.contentDescription)
      .accessibilityLevel('no')
  }
}
