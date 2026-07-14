import type { UIContext } from '@kit.ArkUI';

export const BRAND_COLOR: ResourceColor = $r('app.color.brand_primary');
export const SECONDARY_COLOR: ResourceColor = $r('app.color.brand_secondary');
export const BACKGROUND_COLOR: ResourceColor = $r('app.color.page_background');
export const PRIMARY_TEXT_COLOR: ResourceColor = $r('app.color.text_primary');
export const SECONDARY_TEXT_COLOR: ResourceColor = $r('app.color.text_secondary');
export const HELP_TEXT_COLOR: ResourceColor = $r('app.color.text_help');
export const BORDER_COLOR: ResourceColor = $r('app.color.ui_border');
export const FLOATED_COLOR: ResourceColor = $r('app.color.ui_floated');
export const ERROR_COLOR: ResourceColor = $r('app.color.functional_error');

export const MONTSERRAT_LIGHT: string = 'Montserrat Light';
export const MONTSERRAT_REGULAR: string = 'Montserrat Regular';
export const MONTSERRAT_MEDIUM: string = 'Montserrat Medium';
export const MONTSERRAT_SEMIBOLD: string = 'Montserrat SemiBold';
export const KARLA_REGULAR: string = 'Karla Regular';
export const KARLA_BOLD: string = 'Karla Bold';

let fontsRegistered: boolean = false;

export function registerJetsnackFonts(uiContext: UIContext): void {
  if (fontsRegistered) {
    return;
  }
  uiContext.getFont().registerFont({
    familyName: MONTSERRAT_LIGHT,
    familySrc: $rawfile('fonts/montserrat_light.ttf')
  });
  uiContext.getFont().registerFont({
    familyName: MONTSERRAT_REGULAR,
    familySrc: $rawfile('fonts/montserrat_regular.ttf')
  });
  uiContext.getFont().registerFont({
    familyName: MONTSERRAT_MEDIUM,
    familySrc: $rawfile('fonts/montserrat_medium.ttf')
  });
  uiContext.getFont().registerFont({
    familyName: MONTSERRAT_SEMIBOLD,
    familySrc: $rawfile('fonts/montserrat_semibold.ttf')
  });
  uiContext.getFont().registerFont({
    familyName: KARLA_REGULAR,
    familySrc: $rawfile('fonts/karla_regular.ttf')
  });
  uiContext.getFont().registerFont({
    familyName: KARLA_BOLD,
    familySrc: $rawfile('fonts/karla_bold.ttf')
  });
  fontsRegistered = true;
}
