import type { Want } from '@kit.AbilityKit';
import { FormExtensionAbility, formBindingData, formInfo, formProvider } from '@kit.FormKit';
import { hilog } from '@kit.PerformanceAnalysisKit';

class RecentOrdersFormBinding {
  formId: string;
  formDimension: number;
  formWidth: number;
  formHeight: number;

  constructor(formId: string, formDimension: number, formWidth: number, formHeight: number) {
    this.formId = formId;
    this.formDimension = formDimension;
    this.formWidth = formWidth;
    this.formHeight = formHeight;
  }
}

export default class RecentOrdersFormAbility extends FormExtensionAbility {
  private stringParameter(want: Want, key: string): string {
    const value: Object | undefined = want.parameters?.[key];
    return typeof value === 'string' ? value : '';
  }

  private dimensionParameter(want: Want): formInfo.FormDimension {
    const value: Object | undefined = want.parameters?.[formInfo.FormParam.DIMENSION_KEY];
    if (value === formInfo.FormDimension.Dimension_2_2) {
      return formInfo.FormDimension.Dimension_2_2;
    }
    if (value === formInfo.FormDimension.Dimension_4_4) {
      return formInfo.FormDimension.Dimension_4_4;
    }
    return formInfo.FormDimension.Dimension_2_4;
  }

  private fallbackWidth(dimension: formInfo.FormDimension): number {
    if (dimension === formInfo.FormDimension.Dimension_2_2) {
      return 172;
    }
    if (dimension === formInfo.FormDimension.Dimension_4_4) {
      return 480;
    }
    return 360;
  }

  private fallbackHeight(dimension: formInfo.FormDimension): number {
    if (dimension === formInfo.FormDimension.Dimension_2_2) {
      return 224;
    }
    if (dimension === formInfo.FormDimension.Dimension_4_4) {
      return 359;
    }
    return 224;
  }

  private numberParameter(want: Want, key: string, fallback: number): number {
    const value: Object | undefined = want.parameters?.[key];
    return typeof value === 'number' && value > 0 ? value : fallback;
  }

  private positiveOrFallback(value: number, fallback: number): number {
    return value > 0 ? value : fallback;
  }

  onAddForm(want: Want): formBindingData.FormBindingData {
    const formId: string = this.stringParameter(want, formInfo.FormParam.IDENTITY_KEY);
    const dimension: formInfo.FormDimension = this.dimensionParameter(want);
    const formWidth: number = this.numberParameter(
      want,
      formInfo.FormParam.WIDTH_KEY,
      this.fallbackWidth(dimension)
    );
    const formHeight: number = this.numberParameter(
      want,
      formInfo.FormParam.HEIGHT_KEY,
      this.fallbackHeight(dimension)
    );
    return formBindingData.createFormBindingData(
      new RecentOrdersFormBinding(formId, dimension, formWidth, formHeight)
    );
  }

  onSizeChanged(formId: string, newDimension: formInfo.FormDimension, newRect: formInfo.Rect): void {
    const formWidth: number = this.positiveOrFallback(newRect.width, this.fallbackWidth(newDimension));
    const formHeight: number = this.positiveOrFallback(newRect.height, this.fallbackHeight(newDimension));
    const bindingData: formBindingData.FormBindingData = formBindingData.createFormBindingData(
      new RecentOrdersFormBinding(formId, newDimension, formWidth, formHeight)
    );
    formProvider.updateForm(formId, bindingData).catch((_error: Error): void => {
      hilog.error(0x0000, 'JetsnackForm', 'Failed to publish the resized recent orders form');
    });
  }

  onAcquireFormState(_want: Want): formInfo.FormState {
    return formInfo.FormState.READY;
  }
}
