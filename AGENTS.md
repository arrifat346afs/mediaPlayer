# Repository Guidelines

## Scope and layout

Media Player is a desktop widget plugin for Dux Shell (DMS) 2.0, plugin id
`mediaPlayer`. `MediaPlayerWidget.qml` is the widget, `MediaPlayerSettings.qml`
its settings, and `MediaFormat.js` holds the pure helpers (time formatting,
percent settings, wave geometry). `translations/` has one catalog per locale.
`scripts/verify.py` checks the manifest, sources and translations,
`tests/media_format.test.mjs` unit-tests the helpers, and
`scripts/qml_smoke.py` runs the widget against the installed DMS modules with
`tests/fake_mpris.py` on a private D-Bus session.

## Development and verification

Run `scripts/check --core` for portable checks and `scripts/check` for the full
run, which adds the QML smoke test (Wayland, Quickshell and DMS 2.0 required).
Never report `--core` as a QML validation. Reload a running shell with
`dms ipc call plugins reload mediaPlayer`; renamed files also need
`dms ipc call plugin-scan rescan mediaPlayer` and possibly a shell restart, which
is the user's call.

## Style and safety

Four-space indentation, DMS `D*` components and Theme tokens. Read media state
from `MprisController`, `TrackArtService` and `DSeekbar`; do not spawn
processes, download files or write outside the plugin folder. No repeating
timers that always run and no per-frame repainting; gate animations on
playback, visibility and `SettingsData.reduceMotion`. Every user-facing string
goes through `I18n.trFor("mediaPlayer", ...)` with a literal id, and every
catalog in `translations/` carries the same keys.

## Contributions

Conventional Commits. Pull requests describe the user-visible change, update
`CHANGELOG.md` and translations, and list the checks actually run. Do not
change the plugin id, publish releases, or restart the user's shell as part of
routine checks.
