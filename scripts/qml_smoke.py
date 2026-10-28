#!/usr/bin/env python3
"""Run the widget against the real DMS QML tree and a fake MPRIS player.

The test starts a private D-Bus session, publishes tests/fake_mpris.py on it,
and loads MediaPlayerWidget.qml in an isolated Quickshell instance that reuses
the installed DMS modules (no stubs). It then drives the widget with real
mouse clicks and checks that the player receives them.

Needs a Wayland session, quickshell, dbus-run-session and PyGObject. Set
DMS_QML_ROOT when the DMS QML tree is not found automatically.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "test-results"
PRIVATE_BUS = "MEDIA_PLAYER_SMOKE_BUS"

SHELL = """import QtQuick
import QtTest
import Quickshell
import Quickshell.Wayland
import Quickshell.Services.Mpris
import qs.Common
import qs.Services
import qs.DCommon.Common as DC
import qs.Plugin

ShellRoot {
    id: shell

    property int step: 0
    property int waited: 0
    property var shots: []

    Component.onCompleted: {
        DC.Style.theme = Theme;
        DC.Style.settings = SettingsData;
        DC.I18n.backend = I18n;
    }

    function find(item, name) {
        if (!item)
            return null;
        if (item.objectName === name)
            return item;
        const kids = item.children || [];
        for (let i = 0; i < kids.length; i++) {
            const hit = find(kids[i], name);
            if (hit)
                return hit;
        }
        return null;
    }

    function fail(message) {
        console.log("SMOKE FAIL " + message);
        Qt.exit(1);
    }

    function shot(name) {
        widget.grabToImage(result => result.saveToFile(ARTIFACTS + "/" + name + ".png"));
    }

    function click(name) {
        const button = find(widget, name);
        if (!button || !button.visible || !button.enabled)
            return fail("button not clickable: " + name);
        input.mouseClick(button, button.width / 2, button.height / 2);
    }

    // Each check waits up to 15 s for its condition, then moves on.
    function waitFor(condition, label) {
        if (condition) {
            waited = 0;
            step++;
            return true;
        }
        if (++waited > 150)
            fail("timeout: " + label);
        return false;
    }

    PanelWindow {
        id: window
        anchors {
            top: true
            left: true
        }
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.namespace: "media-player-smoke"
        implicitWidth: 400
        implicitHeight: 210
        color: "transparent"

        MediaPlayerWidget {
            id: widget
            anchors.fill: parent
            anchors.margins: 5
        }

        TestCase {
            id: input
            when: false
        }
    }

    Loader {
        id: settings
        source: Qt.resolvedUrl("Plugin/MediaPlayerSettings.qml")
    }

    Timer {
        interval: 100
        repeat: true
        running: true
        onTriggered: {
            const player = MprisController.activePlayer;
            const length = shell.find(widget, "lengthLabel");
            const elapsed = shell.find(widget, "elapsedLabel");
            switch (shell.step) {
            case 0:
                shell.waitFor(settings.status === Loader.Ready, "settings component");
                break;
            case 1:
                shell.waitFor(player && player.identity === "Media Player Smoke" && widget.hasMedia && !widget.hidden && MprisController.stableTitle === "Smoke Track 1", "player shows track 1");
                break;
            case 2:
                if (shell.waitFor(length && length.text === "4:24" && elapsed && elapsed.text !== "0:00" && shell.find(widget, "seekbar").visible, "length and seekbar")) {
                    console.log("SMOKE track ready", MprisController.stableTitle, elapsed.text, length.text);
                    shell.shot("playing-dark");
                }
                break;
            case 3:
                shell.click("nextButton");
                shell.step++;
                break;
            case 4:
                shell.waitFor(MprisController.stableTitle === "Smoke Track 2", "next reaches player");
                break;
            case 5:
                shell.click("playButton");
                shell.step++;
                break;
            case 6:
                shell.waitFor(player.playbackState === MprisPlaybackState.Paused && !widget.playing, "play button pauses");
                break;
            case 7:
                shell.click("previousButton");
                shell.step++;
                break;
            case 8:
                shell.waitFor(MprisController.stableTitle === "Smoke Track 1", "previous reaches player");
                break;
            case 9:
                Theme.isLightMode = true;
                widget.pluginData = {
                    "showWaves": false,
                    "showArtBackdrop": true,
                    "rotateThumbnail": false,
                    "backgroundOpacity": 95
                };
                shell.step++;
                break;
            case 10:
                if (shell.waitFor(widget.showArtBackdrop && !widget.showWaves && !widget.rotateThumbnail && widget.backgroundOpacity === 0.95, "settings applied"))
                    shell.shot("paused-light");
                break;
            case 11:
                Theme.isLightMode = false;
                widget.pluginData = {};
                player.stop();
                shell.step++;
                break;
            case 12:
                shell.waitFor(!widget.hasMedia && widget.hidden && !widget.visible, "hides when idle");
                break;
            case 13:
                widget.pluginData = {
                    "hideWhenIdle": false
                };
                shell.step++;
                break;
            case 14:
                if (shell.waitFor(widget.visible && !widget.hasMedia, "empty state when not hiding"))
                    shell.shot("empty");
                break;
            case 15:
                console.log("SMOKE PASS");
                Qt.exit(0);
                break;
            }
        }
    }
}
"""

ERRORS = (
    "TypeError:",
    "ReferenceError:",
    "is not a type",
    "Cannot assign",
    "Unable to assign",
    "Cannot load",
    "Binding loop",
    "Deprecation",
    "SMOKE FAIL",
    "Plugin/Media",
)


def find_dms():
    override = os.environ.get("DMS_QML_ROOT")
    runtime = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
    candidates = [Path(override)] if override else []
    candidates += sorted(runtime.glob("dms-shell/*"), key=lambda p: p.stat().st_mtime, reverse=True)
    candidates += [Path.home() / ".config/quickshell/dms", Path("/usr/share/quickshell/dms")]
    for path in candidates:
        if (path / "VERSION").exists() and (path / "Modules/Plugins/DesktopPluginComponent.qml").exists():
            return path
    raise SystemExit("DMS QML root not found; set DMS_QML_ROOT to a DMS 2.0 tree")


def wayland_display(runtime):
    display = os.environ.get("WAYLAND_DISPLAY")
    if not display:
        sockets = [p for p in runtime.glob("wayland-*") if p.is_socket()]
        if not sockets:
            raise SystemExit("no Wayland session found; the QML smoke test needs one")
        display = sockets[0].name
    return display if display.startswith("/") else str(runtime / display)


def run():
    dms = find_dms()
    for tool in ("quickshell", "dbus-run-session"):
        if not shutil.which(tool):
            raise SystemExit(f"{tool} is required for the QML smoke test")
    if os.environ.get(PRIVATE_BUS) != "1":
        # Re-run inside a private bus so the fake player never reaches the real shell.
        env = {**os.environ, PRIVATE_BUS: "1"}
        return subprocess.call(["dbus-run-session", "--", sys.executable, __file__], env=env)

    ARTIFACTS.mkdir(exist_ok=True)
    player = subprocess.Popen(
        [sys.executable, str(ROOT / "tests/fake_mpris.py"), str(ARTIFACTS / "cover.png")],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        if player.stdout.readline().strip() != "FAKE MPRIS READY":
            raise SystemExit("fake MPRIS player did not start")
        with tempfile.TemporaryDirectory(prefix="media-player-qml-") as directory:
            target = Path(directory)
            # qs.* resolves relative to this shell; reuse the real modules, not stubs.
            for child in dms.iterdir():
                if child.name != "shell.qml":
                    (target / child.name).symlink_to(child)
            (target / "Plugin").symlink_to(ROOT)
            (target / "shell.qml").write_text(SHELL.replace("ARTIFACTS", repr(str(ARTIFACTS))))
            runtime = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
            private_runtime = target / "runtime"
            private_runtime.mkdir(mode=0o700)
            env = {
                **os.environ,
                "QT_QPA_PLATFORM": "wayland",
                "WAYLAND_DISPLAY": wayland_display(runtime),
                "XDG_RUNTIME_DIR": str(private_runtime),
                "HOME": str(target),
                "XDG_CONFIG_HOME": str(target / "config"),
                "XDG_CACHE_HOME": str(target / "cache"),
                "XDG_DATA_HOME": str(target / "data"),
                "XDG_STATE_HOME": str(target / "state"),
                # GPU rendering by default: the art clip and wave seekbar are shaders.
                "QT_QUICK_BACKEND": os.environ.get("QT_QUICK_BACKEND", ""),
                "QT_LOGGING_RULES": "qml.debug=true",
            }
            started = time.monotonic()
            result = subprocess.run(
                ["quickshell", "--path", str(target / "shell.qml"), "--no-color"],
                env=env,
                capture_output=True,
                text=True,
                timeout=90,
            )
    finally:
        player.terminate()
        calls, _ = player.communicate(timeout=5)

    output = result.stdout + result.stderr
    print(output)
    print(calls)
    plugin_errors = [
        line for line in output.splitlines() if any(error in line for error in ERRORS) and "SMOKE PASS" not in line
    ]
    expected_calls = ("CALL Next", "CALL Pause", "CALL Previous", "CALL Stop")
    missing = [call for call in expected_calls if call not in calls]
    if result.returncode or "SMOKE PASS" not in output or plugin_errors or missing:
        for line in plugin_errors:
            print("unexpected:", line)
        if missing:
            print("player never received:", ", ".join(missing))
        return 1
    print(
        f"QML smoke passed in {time.monotonic() - started:.1f}s with real DMS imports:",
        dms,
        (dms / "VERSION").read_text().strip(),
    )
    return 0


if __name__ == "__main__":
    sys.exit(run())
