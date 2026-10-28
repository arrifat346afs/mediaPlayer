# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Removed

- `screenshot_8.png` at the repository root; the screenshot lives in
  `assets/screenshot.png`.

## [2.0.0] - 2026-10-28

Maintenance moved from [@arrifat346afs](https://github.com/arrifat346afs) to
[@bernardopg](https://github.com/bernardopg). The repository now lives at
`bernardopg/mediaPlayer`; the plugin id stays `mediaPlayer`, so existing
widgets keep their position and settings.

### Changed

- Rebuilt the widget for Dux Shell (DMS) 2.0 on the shell's own media
  services: `MprisController` for the active player and stable metadata,
  `TrackArtService` for album art, and `DSeekbar` with its shared position
  polling. The widget no longer runs its own timers.
- Playback buttons are `DIconButton`s with Theme sizes, accessible names and
  disabled states that follow the player's capabilities.
- The wave background is painted once per size or color change and only
  translated while playing, instead of being redrawn at 60 FPS. It pauses when
  playback stops, when the widget is off screen and when reduce motion is on.
- Album art rotation pauses in the same cases and resets when turned off.
- The time labels follow the seekbar, including while dragging, and show hours
  for long tracks.
- `plugin.json` only declares permissions from the DMS schema and requires
  DMS 2.0.0.

### Added

- Settings to hide the widget when idle (on by default, the 1.x behavior),
  toggle the wave background and use a blurred album art backdrop.
- Empty state ("No media playing") when the widget is kept visible.
- Brazilian Portuguese translation through `translations/pt.json`.
- Static checks, unit tests and a QML smoke test against the real DMS modules
  and a fake MPRIS player, plus CI.

### Removed

- Album art downloads with `curl` into `/tmp/.dankshell` and the cleanup
  `find -delete`; the file was never displayed.
- The 50 ms and 100 ms polling timers, the unused infinite tick animation and
  the stale-position workarounds that `DSeekbar` now handles.
- Placeholder title and artist text shown when a player has no metadata.
- The `cava` dependency, which the code never used.

## [1.0.0] - 2025-12-23

Initial release by [@arrifat346afs](https://github.com/arrifat346afs).
