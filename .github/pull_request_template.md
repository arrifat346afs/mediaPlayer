## What changes

<!-- Behavior visible to users. Link the issue: Closes #123 -->

## Checks run

- [ ] `scripts/check --core`
- [ ] `scripts/check` (QML smoke test against the installed DMS 2.0)
- [ ] Manual test on a live shell with a real player (say which one)

## Checklist

- [ ] `CHANGELOG.md` updated under `[Unreleased]`
- [ ] New strings use `I18n.trFor("mediaPlayer", ...)` and are in every `translations/*.json`
- [ ] No new processes, network calls or always-running timers
- [ ] Screenshots attached for UI changes
