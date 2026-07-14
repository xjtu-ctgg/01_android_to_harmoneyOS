# Migration contract

## Source audit

Freeze the source commit first. Preserve a complete fixed-commit text snapshot containing all production Kotlin, public tests, manifests, XML resources, and build configuration. Verify the snapshot by hash and exclude credentials, generated build products, repository metadata, and duplicated binary assets. The snapshot must include shared primitives and theme code even when no page fact points to them directly.

Extract facts from executable Android code and resources in this order:

1. navigation graph, destinations, deep links, arguments, and back behavior;
2. screen state and user events, including delays, retry cadence, zero/one boundaries, and intentional no-ops;
3. deterministic fixtures, display order, identifiers, prices, and string-format contracts;
4. drawable geometry, raster hashes, fonts, theme tokens, dimensions, and dark resources;
5. accessibility labels and existing test selectors.

Do not infer behavior from a screenshot when source code is available. A screenshot cannot reveal delayed state, error cadence, removal boundaries, or a no-op callback.

## Required traceability

Store a machine-readable source-facts file containing the source commit and typed collections for pages, routes, actions, data, resources, and visible contract text. Store one mapping per source fact in `migration-manifest.json` with:

- unique `id` and `stableId`;
- `kind` from page, route, action, data, state, theme, resource, component;
- existing source and target file paths;
- status from planned, in_progress, implemented, verified, not_applicable;
- a journey ID for pages and actions.

Treat `implemented` as authored and statically checked. Use `verified` only after the mapped behavior has run in the required Harmony environment.

## Stable automation surface

Use deterministic semantic IDs such as `screen.feed`, `nav.cart`, `snack.card.5`, and `action.cart.checkout`. Add the source stable identifier when elements repeat. Keep accessibility text on interactive nodes and never group an entire screen in a way that hides child nodes.

## Behavioral equivalence

Preserve observable source semantics exactly:

- order and membership of lists;
- case matching and whitespace handling in search;
- route origin and return destination;
- initial quantities, decrement-to-remove behavior, and failure intervals;
- visual-only filters that do not mutate feed results;
- inert buttons as explicit acknowledgement methods with no visible state mutation.
