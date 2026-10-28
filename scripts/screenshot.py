#!/usr/bin/env python3
"""Capture assets/screenshot.png from whatever is playing right now.

Loads the widget in an isolated Quickshell instance (stock dark theme, the
default dank purple) on the real session bus, waits for the active player and
saves a 2x capture. Start some music first.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from qml_smoke import ROOT, find_dms, wayland_display  # noqa: E402

OUTPUT = ROOT / "assets/screenshot.png"

SHELL = """import QtQuick
import Quickshell
import Quickshell.Wayland
import qs.Common
import qs.Services
import qs.DCommon.Common as DC
import qs.Plugin

ShellRoot {
    Component.onCompleted: {
        DC.Style.theme = Theme;
        DC.Style.settings = SettingsData;
        DC.I18n.backend = I18n;
    }

    PanelWindow {
        anchors {
            top: true
            left: true
        }
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.namespace: "media-player-screenshot"
        implicitWidth: 420
        implicitHeight: 210
        color: "transparent"

        MediaPlayerWidget {
            id: widget
            anchors.fill: parent
        }
    }

    Timer {
        property int ticks: 0
        interval: 250
        repeat: true
        running: true
        onTriggered: {
            ticks++;
            // Give the art and the theme a few seconds to settle once media shows up.
            if (widget.hasMedia && TrackArtService.resolvedArtUrl !== "" && ticks > 16) {
                running = false;
                widget.grabToImage(result => {
                    result.saveToFile(OUTPUT);
                    console.log("SCREENSHOT SAVED");
                    Qt.exit(0);
                }, Qt.size(widget.width * 2, widget.height * 2));
            } else if (ticks > 120) {
                console.log("SCREENSHOT NO MEDIA");
                Qt.exit(1);
            }
        }
    }
}
"""


def main():
    dms = find_dms()
    with tempfile.TemporaryDirectory(prefix="media-player-shot-") as directory:
        target = Path(directory)
        for child in dms.iterdir():
            if child.name != "shell.qml":
                (target / child.name).symlink_to(child)
        (target / "Plugin").symlink_to(ROOT)
        (target / "shell.qml").write_text(SHELL.replace("OUTPUT", repr(str(OUTPUT))))
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
            "QT_LOGGING_RULES": "qml.debug=true",
        }
        OUTPUT.parent.mkdir(exist_ok=True)
        result = subprocess.run(
            ["quickshell", "--path", str(target / "shell.qml"), "--no-color"],
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
    output = result.stdout + result.stderr
    if "SCREENSHOT SAVED" not in output:
        print(output)
        print("no screenshot: is a player active?")
        return 1
    print("saved", OUTPUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
