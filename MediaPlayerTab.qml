import QtQuick
import QtQuick.Effects
import QtQuick.Layouts
import Quickshell.Services.Mpris
import Quickshell.Io
import qs.Common
import qs.Services
import qs.Widgets

Item {
    id: root

    LayoutMirroring.enabled: I18n.isRtl
    LayoutMirroring.childrenInherit: true

    property MprisPlayer activePlayer: MprisController.activePlayer
    property var allPlayers: MprisController.availablePlayers

    property bool isSwitching: false
    property string _lastArtUrl: ""
    property string _bgArtSource: ""

    property string activeTrackArtFile: ""

    function loadArtwork(url) {
        if (!url)
            return;
        if (url.startsWith("http://") || url.startsWith("https://")) {
            const filename = "/tmp/.dankshell/trackart_" + Date.now() + ".jpg";
            activeTrackArtFile = filename;

            cleanupProcess.command = ["sh", "-c", "mkdir -p /tmp/.dankshell && find /tmp/.dankshell -name 'trackart_*' ! -name '" + filename.split('/').pop() + "' -delete"];
            cleanupProcess.running = true;

            imageDownloader.command = ["curl", "-L", "-s", "--user-agent", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36", "-o", filename, url];
            imageDownloader.targetFile = filename;
            imageDownloader.running = true;
            return;
        }
        _bgArtSource = url;
    }

    function maybeFinishSwitch() {
        if (activePlayer && activePlayer.trackTitle !== "") {
            isSwitching = false;
            _switchHold = false;
        }
    }

    // Derived "no players" state: always correct, no timers.
    readonly property int _playerCount: allPlayers ? allPlayers.length : 0
    readonly property bool _noneAvailable: _playerCount === 0
    readonly property bool _trulyIdle: activePlayer && activePlayer.playbackState === MprisPlaybackState.Stopped && !activePlayer.trackTitle && !activePlayer.trackArtist
    readonly property bool showNoPlayerNow: (!_switchHold) && (_noneAvailable || _trulyIdle)

    property bool _switchHold: false
    Timer {
        id: _switchHoldTimer
        interval: 650
        repeat: false
        onTriggered: _switchHold = false
    }

    onActivePlayerChanged: {
        if (!activePlayer) {
            isSwitching = false;
            _switchHold = false;
            return;
        }
        isSwitching = true;
        _switchHold = true;
        _switchHoldTimer.restart();
        if (activePlayer.trackArtUrl)
            loadArtwork(activePlayer.trackArtUrl);
    }



    // Responsive sizing with min/max constraints
    property real userScale: 1.0
    readonly property real minWidth: 320
    readonly property real maxWidth: 800
    readonly property real minHeight: 160
    readonly property real maxHeight: 400
    readonly property real baseWidth: 380
    readonly property real baseHeight: 200

    implicitWidth: Math.max(minWidth, Math.min(maxWidth, baseWidth * userScale))
    implicitHeight: Math.max(minHeight, Math.min(maxHeight, baseHeight * userScale))

    Connections {
        target: activePlayer
        function onTrackTitleChanged() {
            _switchHoldTimer.restart();
            maybeFinishSwitch();
        }
        function onTrackArtUrlChanged() {
            if (activePlayer?.trackArtUrl) {
                _lastArtUrl = activePlayer.trackArtUrl;
                loadArtwork(activePlayer.trackArtUrl);
            }
        }
    }

    Connections {
        target: MprisController
        function onAvailablePlayersChanged() {
            const count = (MprisController.availablePlayers?.length || 0);
            if (count === 0) {
                isSwitching = false;
                _switchHold = false;
            } else {
                _switchHold = true;
                _switchHoldTimer.restart();
            }
        }
    }

    Process {
        id: imageDownloader
        running: false
        property string targetFile: ""

        onExited: exitCode => {
            if (exitCode === 0 && targetFile)
                _bgArtSource = "file://" + targetFile;
        }
    }

    Process {
        id: cleanupProcess
        running: false
    }



    property bool isSeeking: false

    Timer {
        interval: 1000
        running: activePlayer?.playbackState === MprisPlaybackState.Playing && !isSeeking
        repeat: true
        onTriggered: {
            // Timer tick - position updates are automatically handled by bindings
        }
    }

    Item {
        id: bgContainer
        anchors.fill: parent
        visible: _bgArtSource !== ""

        Image {
            id: bgImage
            anchors.centerIn: parent
            width: Math.max(parent.width, parent.height) * 1.1
            height: width
            // source: _bgArtSource
            fillMode: Image.PreserveAspectCrop
            asynchronous: true
            cache: true
            visible: false
            onStatusChanged: {
                if (status === Image.Ready)
                    maybeFinishSwitch();
            }
        }

        Item {
            id: blurredBg
            anchors.fill: parent
            visible: false

            MultiEffect {
                anchors.centerIn: parent
                width: bgImage.width
                height: bgImage.height
                source: bgImage
                blurEnabled: true
                blurMax: 64
                blur: 2
                saturation: -0.2
                brightness: -0.25
            }
        }

        Rectangle {
            id: bgMask
            anchors.fill: parent
            radius: Theme.cornerRadius
            visible: false
            layer.enabled: true
        }

        MultiEffect {
            anchors.fill: parent
            source: blurredBg
            maskEnabled: true
            maskSource: bgMask
            maskThresholdMin: 0.5
            maskSpreadAtMin: 1.0
            opacity: 0.7
        }

        Rectangle {
            anchors.fill: parent
            radius: Theme.cornerRadius
            color: Theme.surface
            opacity: 1
        }
    }

    Column {
        anchors.centerIn: parent
        spacing: Theme.spacingM
        visible: showNoPlayerNow

        DankIcon {
            name: "music_note"
            size: Theme.iconSize * 3
            color: Qt.rgba(Theme.surfaceText.r, Theme.surfaceText.g, Theme.surfaceText.b, 0.5)
            anchors.horizontalCenter: parent.horizontalCenter
        }
    }

    // Main content container - Layout with thumbnail
    Item {
        anchors.fill: parent
        anchors.margins: Theme.spacingM * userScale
        visible: !_noneAvailable && (!showNoPlayerNow)

        Row {
            anchors.fill: parent
            spacing: Theme.spacingM * userScale

            // Album Thumbnail Section (Left)
            Rectangle {
                id: thumbnailContainer
                width: parent.height * 0.85
                height: parent.height * 0.85
                anchors.verticalCenter: parent.verticalCenter
                radius: 6 * userScale
                color: Qt.rgba(0, 0, 0, 0.3)
                clip: true

                DankAlbumArt {
                    id: albumArt
                    anchors.fill: parent
                    activePlayer: root.activePlayer
                }

                // Subtle border
                Rectangle {
                    anchors.fill: parent
                    radius: parent.radius
                    color: "transparent"
                    border.color: Qt.rgba(1, 1, 1, 0.1)
                    border.width: 1
                }
            }

            // Content Section (Right)
            Column {
                width: parent.width - thumbnailContainer.width - parent.spacing
                height: parent.height
                spacing: Theme.spacingS * userScale

                // Song Info Section (Top)
                Column {
                    id: songInfo
                    width: parent.width
                    spacing: 2 * userScale

                    StyledText {
                        text: activePlayer?.trackTitle || "The (Overdue) Collapse of Wind..."
                        font.pixelSize: Theme.fontSizeMedium * 1.1 * userScale
                        font.weight: Font.Bold
                        color: Theme.surfaceText
                        width: parent.width
                        elide: Text.ElideRight
                        maximumLineCount: 1
                    }

                    StyledText {
                        text: activePlayer?.trackArtist || "Catalyst"
                        font.pixelSize: Theme.fontSizeSmall * userScale
                        color: Qt.rgba(Theme.surfaceText.r, Theme.surfaceText.g, Theme.surfaceText.b, 0.6)
                        width: parent.width
                        elide: Text.ElideRight
                        maximumLineCount: 1
                    }
                }

                // Spacer
                Item {
                    width: parent.width
                    height: Theme.spacingXS * userScale
                }

                // Controls Row (Middle)
                Row {
                    id: controlsRow
                    width: parent.width
                    spacing: Theme.spacingS * userScale

                    // Previous Button
                    Rectangle {
                        width: 32 * userScale
                        height: 32 * userScale
                        radius: 4 * userScale
                        color: "transparent"
                        anchors.verticalCenter: parent.verticalCenter

                        DankIcon {
                            anchors.centerIn: parent
                            name: "skip_previous"
                            size: 28 * userScale
                            color: Theme.primary
                        }

                        MouseArea {
                            id: prevBtnArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                if (!activePlayer)
                                    return;
                                if (activePlayer.position > 8 && activePlayer.canSeek) {
                                    activePlayer.position = 0;
                                } else {
                                    activePlayer.previous();
                                }
                            }
                        }
                    }

                    // Play/Pause Button
                    Rectangle {
                        width: 32 * userScale
                        height: 32 * userScale
                        radius: 4 * userScale
                        color: "transparent"
                        anchors.verticalCenter: parent.verticalCenter

                        DankIcon {
                            anchors.centerIn: parent
                            name: activePlayer && activePlayer.playbackState === MprisPlaybackState.Playing ? "pause" : "play_arrow"
                            size: 28 * userScale
                            color: Theme.primary
                        }

                        MouseArea {
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: activePlayer && activePlayer.togglePlaying()
                        }
                    }

                    // Next Button
                    Rectangle {
                        width: 32 * userScale
                        height: 32 * userScale
                        radius: 4 * userScale
                        color: "transparent"
                        anchors.verticalCenter: parent.verticalCenter

                        DankIcon {
                            anchors.centerIn: parent
                            name: "skip_next"
                            size: 28 * userScale
                            color: Theme.primary
                        }

                        MouseArea {
                            id: nextBtnArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: activePlayer && activePlayer.next()
                        }
                    }

                    // Spacer to push buttons to right
                    Item {
                        width: parent.width - (32 * 3 * userScale) - (Theme.spacingS * 3 * userScale)
                        height: 1
                    }
                }

                // Seekbar Section (Bottom)
                Column {
                    id: seekbarSection
                    width: parent.width
                    spacing: 2 * userScale

                    // Progress bar
                    Item {
                        width: parent.width
                        height: 16 * userScale

                        DankSeekbar {
                            anchors.fill: parent
                            activePlayer: root.activePlayer
                            isSeeking: root.isSeeking
                            onIsSeekingChanged: root.isSeeking = isSeeking
                        }
                    }

                    // Time labels
                    Item {
                        width: parent.width
                        height: 12 * userScale

                        StyledText {
                            anchors.left: parent.left
                            anchors.verticalCenter: parent.verticalCenter
                            text: {
                                if (!activePlayer)
                                    return "0:00";
                                const rawPos = Math.max(0, activePlayer.position || 0);
                                const pos = activePlayer.length ? rawPos % Math.max(1, activePlayer.length) : rawPos;
                                const minutes = Math.floor(pos / 60);
                                const seconds = Math.floor(pos % 60);
                                return minutes + ":" + (seconds < 10 ? "0" : "") + seconds;
                            }
                            font.pixelSize: Theme.fontSizeSmall * 0.9 * userScale
                            color: Theme.surfaceVariantText
                        }

                        StyledText {
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter
                            text: {
                                if (!activePlayer || !activePlayer.length)
                                    return "0:00";
                                const dur = Math.max(0, activePlayer.length || 0);
                                const minutes = Math.floor(dur / 60);
                                const seconds = Math.floor(dur % 60);
                                return minutes + ":" + (seconds < 10 ? "0" : "") + seconds;
                            }
                            font.pixelSize: Theme.fontSizeSmall * 0.9 * userScale
                            color: Theme.surfaceVariantText
                        }
                    }
                }
            }
        }
    }


}
