# Contributing

Bug reports, translations and fixes are welcome.

## Setup

Clone the repository into your plugins folder and enable it in DMS:

```sh
git clone https://github.com/bernardopg/mediaPlayer ~/.config/DankMaterialShell/plugins/mediaPlayer
```

After editing QML, reload the plugin without restarting the shell:

```sh
dms ipc call plugins reload mediaPlayer
```

If you rename or add a QML file, run `dms ipc call plugin-scan rescan mediaPlayer`
first. The running shell caches the type list of the plugin folder, so a
renamed component may still need a shell restart (`dms restart`).

## Checks

```sh
scripts/check --core   # verify.py and unit tests, runs anywhere (this is what CI runs)
scripts/check          # also the QML smoke test against the installed DMS 2.0
```

The smoke test needs a Wayland session, `quickshell`, `dbus-run-session` and
PyGObject. It never touches the running shell: it uses a private D-Bus session
and a temporary `HOME`. Set `DMS_QML_ROOT` if the DMS QML tree is not found.
Run it for any QML change and say so in the pull request.

## Rules

- **Use the shell's services.** Media state comes from `MprisController`, art
  from `TrackArtService`, position from `DSeekbar`. Do not add `Process`,
  network calls or files outside the plugin folder.
- **No idle work.** No repeating timers that always run, no per-frame
  repainting. Animations pause when nothing plays, when the widget is hidden
  and when *Reduce motion* is on.
- **DMS 2.0 widgets only.** Use the `D*` components (`DIcon`, `DIconButton`,
  `DSeekbar`...), never the deprecated `Dank*` shims, and Theme tokens for
  colors, spacing and sizes.
- **Translatable text.** Wrap every user-facing string in
  `I18n.trFor("mediaPlayer", "...")` with the id written literally, and add the
  term to every file in `translations/`. Keep English terms stable.
- **Keep the id.** `mediaPlayer` must not change; existing widgets depend on it.

`scripts/verify.py` enforces most of these.

## Commits and releases

Commits follow [Conventional Commits](https://www.conventionalcommits.org/)
(`fix: keep the seekbar visible after a player switch`). Record user-visible
changes under `## [Unreleased]` in `CHANGELOG.md`. A release bumps `version` in
`plugin.json` and turns `[Unreleased]` into the new version; `verify.py` checks
that both agree.
