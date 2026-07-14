# Jetsnack for HarmonyOS

Native Stage-model ArkTS/ArkUI reconstruction of the competition Android Jetsnack baseline at commit `23e1421b72b602d80486777efbf24dd248abf3bb`.

The project contains one dependency-free entry HAP, six screens/routes, deterministic local data and assets, stable automation IDs, frozen source evidence, an Android-to-HarmonyOS migration Skill, core journeys, and executable contract tests.

Run from this directory:

```bash
tools/verify.sh --build
```

Use `--static` without a Harmony toolchain or `--strict` when the official Code Linter is installed. The authoritative platform instructions are in `../INSTRUCTION.md` in the submitted archive.
