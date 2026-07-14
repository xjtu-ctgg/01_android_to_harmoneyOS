import { ConfigurationConstant, UIAbility } from '@kit.AbilityKit';
import type { AbilityConstant, Configuration, Want } from '@kit.AbilityKit';
import { KeyboardAvoidMode, window } from '@kit.ArkUI';
import { hilog } from '@kit.PerformanceAnalysisKit';
import { ROUTE_CART, ROUTE_FEED } from '../state/AppRoute';

const CART_DEEP_LINK: string = 'https://jetsnack.example.com/home/cart';

export default class EntryAbility extends UIAbility {
  private mainWindow: window.Window | undefined = undefined;
  private systemTopInsetPx: number = 0;
  private systemBottomInsetPx: number = 0;
  private systemLeftInsetPx: number = 0;
  private systemRightInsetPx: number = 0;
  private cutoutTopInsetPx: number = 0;
  private cutoutBottomInsetPx: number = 0;
  private cutoutLeftInsetPx: number = 0;
  private cutoutRightInsetPx: number = 0;
  private navigationBottomInsetPx: number = 0;
  private onAvoidAreaChange: (options: window.AvoidAreaOptions) => void =
    (options: window.AvoidAreaOptions): void => {
      this.publishAvoidArea(options.type, options.area);
    };

  private publishAvoidArea(type: window.AvoidAreaType, area: window.AvoidArea): void {
    if (type === window.AvoidAreaType.TYPE_SYSTEM) {
      this.systemTopInsetPx = area.topRect.height;
      this.systemBottomInsetPx = area.bottomRect.height;
      this.systemLeftInsetPx = area.leftRect.width;
      this.systemRightInsetPx = area.rightRect.width;
    } else if (type === window.AvoidAreaType.TYPE_CUTOUT) {
      this.cutoutTopInsetPx = area.topRect.height;
      this.cutoutBottomInsetPx = area.bottomRect.height;
      this.cutoutLeftInsetPx = area.leftRect.width;
      this.cutoutRightInsetPx = area.rightRect.width;
    } else if (type === window.AvoidAreaType.TYPE_NAVIGATION_INDICATOR) {
      this.navigationBottomInsetPx = area.bottomRect.height;
    }
    AppStorage.setOrCreate<number>('topInsetPx',
      Math.max(this.systemTopInsetPx, this.cutoutTopInsetPx));
    AppStorage.setOrCreate<number>('bottomInsetPx',
      Math.max(this.systemBottomInsetPx, this.cutoutBottomInsetPx, this.navigationBottomInsetPx));
    AppStorage.setOrCreate<number>('leftInsetPx',
      Math.max(this.systemLeftInsetPx, this.cutoutLeftInsetPx));
    AppStorage.setOrCreate<number>('rightInsetPx',
      Math.max(this.systemRightInsetPx, this.cutoutRightInsetPx));
  }

  private observeAvoidAreas(): void {
    if (this.mainWindow === undefined) {
      return;
    }
    try {
      const systemArea: window.AvoidArea =
        this.mainWindow.getWindowAvoidArea(window.AvoidAreaType.TYPE_SYSTEM);
      const cutoutArea: window.AvoidArea =
        this.mainWindow.getWindowAvoidArea(window.AvoidAreaType.TYPE_CUTOUT);
      const navigationArea: window.AvoidArea =
        this.mainWindow.getWindowAvoidArea(window.AvoidAreaType.TYPE_NAVIGATION_INDICATOR);
      this.publishAvoidArea(window.AvoidAreaType.TYPE_SYSTEM, systemArea);
      this.publishAvoidArea(window.AvoidAreaType.TYPE_CUTOUT, cutoutArea);
      this.publishAvoidArea(window.AvoidAreaType.TYPE_NAVIGATION_INDICATOR, navigationArea);
      this.mainWindow.on('avoidAreaChange', this.onAvoidAreaChange);
    } catch {
      AppStorage.setOrCreate<number>('topInsetPx', 0);
      AppStorage.setOrCreate<number>('bottomInsetPx', 0);
      AppStorage.setOrCreate<number>('leftInsetPx', 0);
      AppStorage.setOrCreate<number>('rightInsetPx', 0);
      hilog.error(0x0000, 'Jetsnack', 'Failed to observe Jetsnack avoid areas');
    }
  }

  private applySystemBars(colorMode: number | undefined): void {
    if (this.mainWindow === undefined) {
      return;
    }
    const isDark: boolean = colorMode === ConfigurationConstant.ColorMode.COLOR_MODE_DARK;
    const contentColor: string = isDark ? '#FFFFFF' : '#000000';
    const navigationColor: string = isDark ? '#121212' : '#FFFFFF';
    try {
      this.mainWindow.setWindowSystemBarProperties({
        statusBarColor: '#00000000',
        statusBarContentColor: contentColor,
        navigationBarColor: navigationColor,
        navigationBarContentColor: contentColor
      });
    } catch {
      hilog.error(0x0000, 'Jetsnack', 'Failed to update Jetsnack system bars');
    }
  }

  private directFormRoute(want: Want): string {
    const targetRoute: Object | undefined = want.parameters?.['targetRoute'];
    return targetRoute === ROUTE_CART ? ROUTE_CART : ROUTE_FEED;
  }

  private serializedFormRoute(want: Want): string {
    const serializedParams: Object | undefined = want.parameters?.['params'];
    if (typeof serializedParams !== 'string' || serializedParams.length === 0) {
      return ROUTE_FEED;
    }
    try {
      const params: Record<string, Object> = JSON.parse(serializedParams);
      const targetRoute: Object | undefined = params['targetRoute'];
      return targetRoute === ROUTE_CART ? ROUTE_CART : ROUTE_FEED;
    } catch {
      return ROUTE_FEED;
    }
  }

  private routeForWant(want: Want): string {
    const uri: string = want.uri ?? '';
    let routeEnd: number = uri.length;
    const queryIndex: number = uri.indexOf('?');
    if (queryIndex >= 0 && queryIndex < routeEnd) {
      routeEnd = queryIndex;
    }
    const fragmentIndex: number = uri.indexOf('#');
    if (fragmentIndex >= 0 && fragmentIndex < routeEnd) {
      routeEnd = fragmentIndex;
    }
    if (uri.substring(0, routeEnd) === CART_DEEP_LINK) {
      return ROUTE_CART;
    }
    if (this.directFormRoute(want) === ROUTE_CART || this.serializedFormRoute(want) === ROUTE_CART) {
      return ROUTE_CART;
    }
    return ROUTE_FEED;
  }

  private publishRoute(want: Want): void {
    AppStorage.setOrCreate<string>('initialRoute', this.routeForWant(want));
    const currentRequestId: number = AppStorage.get<number>('navigationRequestId') ?? 0;
    AppStorage.setOrCreate<number>('navigationRequestId', currentRequestId + 1);
  }

  private publishWarmRoute(want: Want): void {
    if (this.routeForWant(want) !== ROUTE_CART) {
      return;
    }
    this.publishRoute(want);
  }

  onCreate(want: Want, _launchParam: AbilityConstant.LaunchParam): void {
    this.publishRoute(want);
  }

  onNewWant(want: Want, _launchParam: AbilityConstant.LaunchParam): void {
    this.publishWarmRoute(want);
  }

  onConfigurationUpdate(newConfig: Configuration): void {
    this.applySystemBars(newConfig.colorMode);
    const currentRequestId: number = AppStorage.get<number>('configurationRequestId') ?? 0;
    AppStorage.setOrCreate<number>('configurationRequestId', currentRequestId + 1);
  }

  onWindowStageCreate(windowStage: window.WindowStage): void {
    try {
      this.mainWindow = windowStage.getMainWindowSync();
      this.mainWindow.setWindowLayoutFullScreen(true);
      this.mainWindow.getUIContext().setKeyboardAvoidMode(KeyboardAvoidMode.RESIZE);
      this.applySystemBars(this.context.resourceManager.getConfigurationSync().colorMode);
      this.observeAvoidAreas();
      windowStage.loadContent('pages/Index');
    } catch {
      hilog.error(0x0000, 'Jetsnack', 'Failed to create the main Jetsnack window');
    }
  }

  onWindowStageDestroy(): void {
    if (this.mainWindow !== undefined) {
      try {
        this.mainWindow.off('avoidAreaChange', this.onAvoidAreaChange);
      } catch {
        hilog.error(0x0000, 'Jetsnack', 'Failed to stop Jetsnack avoid area observation');
      }
    }
    this.mainWindow = undefined;
  }
}
