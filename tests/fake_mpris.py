#!/usr/bin/env python3
"""Minimal MPRIS player for the QML smoke test.

Owns org.mpris.MediaPlayer2.mediaPlayerSmoke on the session bus it is started
on (the smoke test gives it a private bus), answers the properties the widget
reads, and prints one line per method call so the test can check that the
widget's buttons reach the player.
"""

import struct
import sys
import zlib
from pathlib import Path

import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib  # noqa: E402

BUS_NAME = "org.mpris.MediaPlayer2.mediaPlayerSmoke"
OBJECT_PATH = "/org/mpris/MediaPlayer2"
TRACK_PATH = "/org/mpris/MediaPlayer2/track/1"
LENGTH_US = 264 * 1_000_000

INTROSPECTION = """
<node>
  <interface name="org.mpris.MediaPlayer2">
    <method name="Raise"/>
    <method name="Quit"/>
    <property name="CanQuit" type="b" access="read"/>
    <property name="CanRaise" type="b" access="read"/>
    <property name="HasTrackList" type="b" access="read"/>
    <property name="Identity" type="s" access="read"/>
    <property name="DesktopEntry" type="s" access="read"/>
    <property name="SupportedUriSchemes" type="as" access="read"/>
    <property name="SupportedMimeTypes" type="as" access="read"/>
  </interface>
  <interface name="org.mpris.MediaPlayer2.Player">
    <method name="Next"/>
    <method name="Previous"/>
    <method name="Pause"/>
    <method name="PlayPause"/>
    <method name="Stop"/>
    <method name="Play"/>
    <method name="Seek"><arg direction="in" name="Offset" type="x"/></method>
    <method name="SetPosition">
      <arg direction="in" name="TrackId" type="o"/>
      <arg direction="in" name="Position" type="x"/>
    </method>
    <method name="OpenUri"><arg direction="in" name="Uri" type="s"/></method>
    <signal name="Seeked"><arg name="Position" type="x"/></signal>
    <property name="PlaybackStatus" type="s" access="read"/>
    <property name="LoopStatus" type="s" access="readwrite"/>
    <property name="Rate" type="d" access="readwrite"/>
    <property name="Shuffle" type="b" access="readwrite"/>
    <property name="Metadata" type="a{sv}" access="read"/>
    <property name="Volume" type="d" access="readwrite"/>
    <property name="Position" type="x" access="read"/>
    <property name="MinimumRate" type="d" access="read"/>
    <property name="MaximumRate" type="d" access="read"/>
    <property name="CanGoNext" type="b" access="read"/>
    <property name="CanGoPrevious" type="b" access="read"/>
    <property name="CanPlay" type="b" access="read"/>
    <property name="CanPause" type="b" access="read"/>
    <property name="CanSeek" type="b" access="read"/>
    <property name="CanControl" type="b" access="read"/>
  </interface>
</node>
"""


def write_cover(path, size=256):
    """Writes a two-tone gradient PNG with the standard library only."""
    rows = []
    for y in range(size):
        row = bytearray([0])
        for x in range(size):
            row += bytes((40 + x * 180 // size, 60 + y * 120 // size, 200 - x * 100 // size))
        rows.append(bytes(row))

    def chunk(kind, data):
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    header = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    Path(path).write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(b"".join(rows)))
        + chunk(b"IEND", b"")
    )


class Player:
    def __init__(self, connection, cover=None):
        self.connection = connection
        self.cover = cover
        self.status = "Playing"
        self.position = 42 * 1_000_000
        self.track = 1

    def metadata(self):
        return {
            "mpris:trackid": GLib.Variant("o", TRACK_PATH),
            "mpris:length": GLib.Variant("x", LENGTH_US),
            "xesam:title": GLib.Variant("s", f"Smoke Track {self.track}"),
            "xesam:artist": GLib.Variant("as", ["Smoke Artist"]),
            "xesam:album": GLib.Variant("s", "Smoke Album"),
            **({"mpris:artUrl": GLib.Variant("s", Path(self.cover).as_uri())} if self.cover else {}),
        }

    def properties(self, interface):
        if interface == "org.mpris.MediaPlayer2":
            return {
                "CanQuit": GLib.Variant("b", False),
                "CanRaise": GLib.Variant("b", False),
                "HasTrackList": GLib.Variant("b", False),
                "Identity": GLib.Variant("s", "Media Player Smoke"),
                "DesktopEntry": GLib.Variant("s", "media-player-smoke"),
                "SupportedUriSchemes": GLib.Variant("as", []),
                "SupportedMimeTypes": GLib.Variant("as", []),
            }
        return {
            "PlaybackStatus": GLib.Variant("s", self.status),
            "LoopStatus": GLib.Variant("s", "None"),
            "Rate": GLib.Variant("d", 1.0),
            "Shuffle": GLib.Variant("b", False),
            "Metadata": GLib.Variant("a{sv}", self.metadata()),
            "Volume": GLib.Variant("d", 1.0),
            "Position": GLib.Variant("x", self.position),
            "MinimumRate": GLib.Variant("d", 1.0),
            "MaximumRate": GLib.Variant("d", 1.0),
            "CanGoNext": GLib.Variant("b", True),
            "CanGoPrevious": GLib.Variant("b", True),
            "CanPlay": GLib.Variant("b", True),
            "CanPause": GLib.Variant("b", True),
            "CanSeek": GLib.Variant("b", True),
            "CanControl": GLib.Variant("b", True),
        }

    def changed(self, names):
        props = self.properties("org.mpris.MediaPlayer2.Player")
        self.connection.emit_signal(
            None,
            OBJECT_PATH,
            "org.freedesktop.DBus.Properties",
            "PropertiesChanged",
            GLib.Variant(
                "(sa{sv}as)",
                (
                    "org.mpris.MediaPlayer2.Player",
                    {name: props[name] for name in names},
                    [],
                ),
            ),
        )

    def call(self, _conn, _sender, _path, _interface, method, params, invocation):
        print(f"CALL {method}", flush=True)
        if method == "Next":
            self.track += 1
            self.position = 0
            self.changed(["Metadata"])
        elif method == "Previous":
            self.track = max(1, self.track - 1)
            self.position = 0
            self.changed(["Metadata"])
        elif method in ("PlayPause", "Play", "Pause", "Stop"):
            playing = self.status == "Playing"
            self.status = {
                "PlayPause": "Paused" if playing else "Playing",
                "Play": "Playing",
                "Pause": "Paused",
                "Stop": "Stopped",
            }[method]
            self.changed(["PlaybackStatus"])
        elif method == "SetPosition":
            self.position = params.unpack()[1]
            self.connection.emit_signal(
                None,
                OBJECT_PATH,
                "org.mpris.MediaPlayer2.Player",
                "Seeked",
                GLib.Variant("(x)", (self.position,)),
            )
        elif method == "Seek":
            self.position = max(0, self.position + params.unpack()[0])
        invocation.return_value(None)

    def get(self, _conn, _sender, _path, interface, name):
        return self.properties(interface).get(name)

    def set(self, _conn, _sender, _path, _interface, _name, _value):
        return True


def main():
    node = Gio.DBusNodeInfo.new_for_xml(INTROSPECTION)
    loop = GLib.MainLoop()
    connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    cover = sys.argv[1] if len(sys.argv) > 1 else None
    if cover:
        write_cover(cover)
    player = Player(connection, cover)
    for interface in node.interfaces:
        connection.register_object(
            OBJECT_PATH, interface, player.call, player.get, player.set
        )

    def acquired(*_args):
        print("FAKE MPRIS READY", flush=True)

    def lost(*_args):
        print("FAKE MPRIS NAME LOST", flush=True)
        loop.quit()

    Gio.bus_own_name_on_connection(
        connection, BUS_NAME, Gio.BusNameOwnerFlags.NONE, acquired, lost
    )
    try:
        loop.run()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
