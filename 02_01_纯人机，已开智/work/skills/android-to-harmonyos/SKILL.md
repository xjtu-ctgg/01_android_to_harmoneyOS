---
name: android-to-harmonyos
description: Reconstruct Android applications as native Stage-model HarmonyOS projects with traceable source facts, ArkTS/ArkUI implementation, deterministic UI journeys, screenshot-oriented visual matching, static-policy gates, and reproducible HAP builds. Use when migrating Android/Jetpack Compose or View-based source to HarmonyOS, auditing an existing migration, or preparing an Android-to-HarmonyOS competition delivery.
---

# Android to HarmonyOS

Produce a native, testable HarmonyOS repository from an Android baseline. Preserve source behavior—including intentional no-ops—and prove each mapping before declaring it complete.

## Completed-delivery handoff

When this Skill is present inside a submitted repository that already contains `entry/`, `migration-manifest.json`, and `migration-report.md`, treat those files as the completed delivery and use this document only as audit evidence. Do not regenerate or modify the repository during platform scoring; the platform's own scoring Skill performs the supplied intent-case evaluation.

## Workflow

### 1. Freeze source facts

1. Record the exact Android commit and module before editing target code.
2. Preserve a complete fixed-commit text snapshot under `source-facts/android-source/`: all production Kotlin, public tests, manifests, XML resources, and build configuration. Verify hashes and exclude credentials, build products, repository metadata, and duplicated binary assets.
3. Inventory pages, routes, actions, Android widgets, local data, resources, typography, colors, dimensions, delays, error boundaries, and empty states. Audit shared primitives such as Surface, Button, Card, and theme defaults before page-local approximations.
4. Give every page and action a stable automation ID.
5. Save machine-readable facts under `source-facts/` and source-to-target entries in `migration-manifest.json`.
6. For every registered Android widget, freeze its receiver/provider, size breakpoints, visible data, click targets, and update semantics before selecting the matching HarmonyOS Form Kit architecture.
7. Freeze locale-sensitive source behavior: system locale lookup, likely-region resolution, currency selection and minor units, Unicode bidirectional marks, locale-aware case mapping, and configuration-change state boundaries.
8. Freeze public Android unit/instrumentation tests and their ordered selectors. Replay those paths as first-class Journeys before inventing additional adversarial cases.
9. Run `python3 tools/contract_check.py --manifest migration-manifest.json`. Fix facts or mappings; never weaken the checker to hide divergence.

For extraction and mapping rules, read [references/migration-contract.md](references/migration-contract.md).

### 2. Build the Harmony project

1. Use a Stage-model entry HAP, ArkTS, ArkUI, typed state, resource qualifiers, and local media.
2. Rebuild behavior from facts, not screenshots alone. Preserve list order, route/back semantics, search boundaries, quantities, delayed state, and explicitly inert actions.
3. Convert vectors without redrawing path geometry. Copy raster assets and fonts bit-for-bit when licensing permits.
4. Keep visible strings and colors in resources. Avoid `any`, `unknown`, empty event handlers, mutable shared fixtures, unstable IDs, network-only assets, and random initial animation frames.
5. When source facts include a widget, register a typed `FormExtensionAbility`, validate `form_config.json`, keep media resources out of serialized binding data, and reproduce resize plus router behavior. Bind the initial physical geometry from `FormParam.WIDTH_KEY` and `FormParam.HEIGHT_KEY`, then publish the vp rectangle from `onSizeChanged`; a categorical dimension alone cannot reproduce source width/height breakpoints.
6. Implement in thin vertical slices: write a failing contract, add the smallest page/state behavior, run contracts, then compile ArkTS.
7. Format money through one shared system locale entry point backed by `Intl.NumberFormat`; do not hard-code a currency symbol. Preserve formatter-produced Unicode bidirectional marks. Apply source-equivalent navigation casing with `toLocaleUpperCase`, and test Turkish dotted-I behavior.
8. On a runtime configuration change, recompute locale-derived presentation while preserving or resetting authored state exactly where the Android source does.

For visual and ArkTS rules, read [references/quality-gates.md](references/quality-gates.md).

### 3. Verify behavior and visuals

1. Execute every item in `journeys/core.yaml` from a cold start.
2. Execute the frozen public Android tests as ordered cross-screen paths, then assert stable IDs, visible text, navigation result, state boundaries, and no-op invariants.
3. Capture screenshots only after fonts and local images settle. Use fixed device size, density, theme, locale, and system bars. Prepare the Journey checkpoint, then run `tools/device_evidence.py --journey-id <id> --stable-id <id> --expected-text <text> --output-dir <dir>`; its default five repetitions retain the raw layout trees, raw PNG files, hashes, and selector validation in `checkpoint.json`.
4. Compare same-size raw Android and Harmony screenshots with `tools/screenshot_compare.py --reference <android.png> --actual <harmony.png> --output <comparison.json>`. Inspect MAE, mismatch rate, and windowed SSIM; fix geometry and typography before decorative detail. Never resize one platform silently to force a pass.
5. For every discontinuous source breakpoint, add physical-size Journeys at `breakpoint - 1`, the breakpoint, and the next relevant edge before accepting responsive parity.
6. Run `tools/verify.sh --static` after every slice and `tools/verify.sh --strict` in an official HarmonyOS SDK environment.
7. Rehearse the final archive as five independent Executor runs from a read-only package root. Each Executor must use its own writable tree and execute the same complete gate; compare case counts and authored-source digests across all five runs.

Do not claim device, screenshot, or official Code Linter verification without its actual log and artifact.

### 4. Package the result

1. Require all manifest mappings to be `implemented` or `verified` and all gates to pass.
2. Remove Android build products, caches, credentials, absolute personal paths, temporary SDKs, and repository metadata from the submission copy.
3. Keep `INSTRUCTION.md`, the complete Harmony project, `migration-report.md`, this Skill, `source-facts/`, `migration-manifest.json`, `journeys/`, and `tools/`.
4. Run [scripts/run-project-gates.sh](scripts/run-project-gates.sh) from any directory.
5. Package exactly one single root directory named like the ZIP. Inside it keep `INSTRUCTION.md`, `work/`, `result/output.md`, `logs/interaction.md`, and `logs/trace/`; the Harmony project and `migration-report.md` remain under `work/`.
6. Keep the submitted `INSTRUCTION.md` scorer-oriented: for this competition the Scorer reads `work/migration-report.md` and ArkTS sources against the supplied intent cases. This submitted migration Skill is not the platform scoring Skill; do not execute this migration Skill during reproduction when the final `work/` already exists. The delivered `work/` is authoritative; do not regenerate it from Android or require SDK installation/build as a precondition for source scoring. If `tools/verify.sh --build` reports `reason=missing_sdk`, `reason=missing_hvigor`, or `reason=missing_codelinter`, record the environment boundary once and continue to the platform Scorer instead of retrying or installing tools.
7. Use `tools/five_executor_verify.py` only as a local delivery rehearsal. A platform Executor must not recursively launch the five-run harness.

## Decision rules

- If a source interaction is intentionally inert, keep it clickable and observable but do not invent state changes.
- If a proprietary HarmonyOS tool is absent, continue with static contracts and an OpenHarmony public-API cross-build only when clearly labeled; leave the official gate unverified.
- If source truth and a screenshot appear inconsistent, reproduce the executable source behavior and document the discrepancy.
- If a fix improves one screenshot while breaking a journey or lint gate, reject it.
- If the input project differs from the frozen commit, regenerate facts before reusing mappings.
- A successful local five independent Executor rehearsal proves deterministic reproduction only; it is not evidence of platform hidden-case full score.
