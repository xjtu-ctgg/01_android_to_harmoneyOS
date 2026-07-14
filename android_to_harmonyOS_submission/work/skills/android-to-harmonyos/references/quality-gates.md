# Quality gates

## ArkTS and Harmony conventions

- Use explicit interfaces, enums, and primitive types. Do not use `any` or `unknown`.
- Use `@Observed` and `@ObjectLink` for shared authored state; return copied fixture arrays instead of exposing mutable constants.
- Put UI text, theme colors, media, and dark-mode overrides in resources.
- Give every event handler an explicit method or state transition. Do not leave empty lambdas.
- Keep source files under Stage module conventions and declare phone/tablet in the formal HarmonyOS profile.
- Avoid external runtime dependencies when the Android baseline is entirely local.

## Screenshot matching order

Use the same viewport, density, locale, theme, system-bar policy, and cold-start state. Compare in this order:

1. system insets and root bounds;
2. major containers, navigation, scroll position, and fixed bars;
3. font family, weight, size, line height, and wrapping;
4. images, crop mode, masks, and vector geometry;
5. colors, borders, radii, shadows, and dividers.

Make the initial frame deterministic. Disable unseeded animation or choose a fixed initial gradient frame. Load local fonts before capture.

## Locale, currency, and bidirectional text

- Resolve the current system locale at formatting time; cover explicit region tags, language-only likely regions, Unicode currency overrides, and unknown territories.
- Use one shared `Intl.NumberFormat` currency path for every price surface. Test currency symbol placement, grouping, decimal separators, zero-minor-unit currencies, non-breaking spacing, and negative values.
- Preserve Unicode bidirectional controls emitted by the formatter. Under RTL locales, compare the complete rendered text and bounds rather than stripping marks for convenience.
- Keep localized resources in source case and apply locale-aware case mapping where the Android source does. Include Turkish dotted-I and accessibility text in the same contract.
- Exercise a runtime locale/configuration change after mutating navigation and cart state; assert that derived presentation refreshes without losing state that Android retains.

## Required gates

Run static contracts, source-fact validation, migration-manifest validation, ArkTS policy scans, resource hash checks, an official HarmonyOS HAP build, and official Code Linter. Run core UI journeys and screenshot comparisons on the grading-equivalent device when available. Five cold-start repetitions should produce the same visible state and pass result.

An OpenHarmony public SDK build proves only public API and ArkTS compatibility. It does not replace an official HarmonyOS build, Code Linter, signing, or device verification.

## Five-Executor platform rehearsal

The grading model uses five independent Executor tasks. Each receives the same submitted repository and runs the complete case suite in its own writable task directory while the extracted package root may be read-only. Require all five runs to have valid artifacts, equal nonzero local case counts, equal authored-source digests, and successful builds; stability is the intersection of passed cases and accuracy is the best run.

`tools/five_executor_verify.py` is a local five-Executor proxy for delivery shape, isolation, build reproducibility, and failure propagation. It does not contain platform hidden tests, does not prove screenshot similarity on a device, and must never be reported as a hidden-case full score. Do not invoke it recursively from one real platform Executor.

## Device evidence procedure

On an official HarmonyOS device or grading-equivalent emulator, first confirm that exactly one intended target is visible with `hdc list targets`. For every Journey checkpoint, locate and operate components by the Journey `stable_id`; do not substitute screen coordinates when an ID is exposed. After the UI is idle and local fonts and images have settled, retain both the accessibility/component tree and an unmodified screenshot:

```sh
hdc shell uitest dumpLayout -p /data/local/tmp/jetsnack-layout.json
hdc shell uitest screenCap -p /data/local/tmp/jetsnack.png
hdc file recv /data/local/tmp/jetsnack-layout.json ./device-evidence/
hdc file recv /data/local/tmp/jetsnack.png ./device-evidence/
```

Prefer the repository collector after manually preparing the requested Journey checkpoint. It rejects zero or multiple targets, validates the stable ID against every raw component tree, keeps every raw PNG, and writes a path-independent summary:

```sh
tools/device_evidence.py \
  --journey-id core.feed \
  --stable-id screen.feed \
  --expected-text "Android's picks" \
  --output-dir device-evidence/core.feed
```

The default is five captures. `checkpoint.json` records filenames, selector matches, PNG SHA-256 values, and `allPngHashesEqual`; it does not by itself navigate the app to the checkpoint or compare against an Android reference image.

After capturing the Android reference and HarmonyOS checkpoint with the same viewport, density, font scale, locale, layout direction, theme, and system bars, compare the unmodified, same-size raw PNG files:

```sh
tools/screenshot_compare.py \
  --reference device-evidence/android/core.feed.png \
  --actual device-evidence/harmony/core.feed.png \
  --output device-evidence/comparison/core.feed.json
```

The dependency-free comparator supports non-interlaced 8-bit grayscale, RGB, grayscale-alpha, and RGBA PNG files. It rejects dimension mismatch instead of resizing, composites alpha over white, and reports `meanAbsoluteError`, `pixelMismatchRate`, and windowed `ssim`. Defaults are repository regression thresholds, not a claim about unknown platform scoring thresholds; tighten or explicitly override them only for a documented, consistently captured reference set. Keep the raw PNG files beside the JSON report.

Keep the raw PNG before cropping or comparison. Record viewport, density, font scale, locale, layout direction, theme, system/cutout/navigation avoid areas, app version, device build, Journey ID, and capture time beside each pair of artifacts. Validate that the dumped node matching `stable_id` has the expected text, bounds, selected/checked state, clickability, and visibility before accepting the screenshot.

Run five cold-start repetitions for the core feed, search, cart, profile, detail, and filter checkpoints. The component-tree assertions and raw PNG hash must be deterministic unless the Android source intentionally animates that checkpoint. Then compare aligned Android and HarmonyOS crops and report pixel difference and SSIM; never treat a hand-edited image as runtime evidence.

For every migrated Form Kit card, use the Launcher card picker to add the declared form, then resize it through every `supportDimensions` value and record its physical width/height in vp. Do not infer layout only from the categorical dimension. For each source width or height discontinuity, capture one vp below, exactly at, and one vp above whenever that value changes behavior. Capture the card at each representative size, light/dark theme, and large font scale. Verify the title cart and every visible trailing cart target independently; do not treat the whole row as clickable unless the Android widget does. Repeat both cold-start and warm-start routing and confirm that resize updates the bound width, height, and dimension without recreating stale card state.
