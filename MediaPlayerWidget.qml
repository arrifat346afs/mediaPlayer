pragma ComponentBehavior: Bound

import QtQuick
import Quickshell.Services.Mpris
import qs.Common
import qs.Services
import qs.Widgets
import qs.DCommon.Widgets
import qs.Modules.Plugins
import "MediaFormat.js" as MediaFormat

DesktopPluginComponent {
    id: root

    minWidth: 300
    minHeight: 150
    implicitWidth: 380
    implicitHeight: 200

    readonly property real backgroundOpacity: MediaFormat.percent(pluginData.backgroundOpacity, 80)
    readonly property real borderOpacity: MediaFormat.percent(pluginData.borderOpacity, 100)
    readonly property bool rotateThumbnail: pluginData.rotateThumbnail ?? true
    readonly property bool showWaves: pluginData.showWaves ?? true
    readonly property bool showArtBackdrop: pluginData.showArtBackdrop ?? false
    readonly property bool hideWhenIdle: pluginData.hideWhenIdle ?? true

    readonly property MprisPlayer activePlayer: MprisController.activePlayer
    readonly property bool hasMedia: !!activePlayer && !MprisController.isIdle(activePlayer)
    readonly property bool playing: activePlayer?.playbackState === MprisPlaybackState.Playing
    readonly property real trackLength: MprisController.activePlayerStableLength
    readonly property bool onScreen: visible && (Window.window?.visible ?? false)
    readonly property bool motionAllowed: !SettingsData.reduceMotion && Theme.currentAnimationSpeed !== SettingsData.AnimationSpeed.None
    readonly property bool animate: onScreen && playing && motionAllowed

    // Hiding waits briefly so a player switch or a gap between tracks does not blink the widget.
    readonly property bool wantsHidden: hideWhenIdle && !hasMedia
    property bool hidden: false

    onWantsHiddenChanged: {
        if (wantsHidden) {
            hideDelay.restart();
            return;
        }
        hideDelay.stop();
        hidden = false;
    }
    Component.onCompleted: hidden = wantsHidden

    Timer {
        id: hideDelay
        interval: 650
        onTriggered: root.hidden = root.wantsHidden
    }

    opacity: hidden ? 0 : 1
    visible: opacity > 0

    Behavior on opacity {
        enabled: root.motionAllowed
        NumberAnimation {
            duration: Theme.mediumDuration
            easing.type: Easing.OutCubic
        }
    }

    Rectangle {
        id: card
        anchors.fill: parent
        radius: Theme.cornerRadius
        color: Theme.withAlpha(Theme.hostSurface, root.backgroundOpacity)
        clip: true

        MediaArtBackdrop {
            anchors.fill: parent
            radius: card.radius
            activePlayer: root.activePlayer
            artOpacity: 0.45
            visible: root.showArtBackdrop && root.hasMedia
        }

        Item {
            id: waves
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: parent.height * 0.3
            visible: root.showWaves && root.hasMedia
            opacity: root.playing ? 1 : 0.35

            Behavior on opacity {
                enabled: root.motionAllowed
                NumberAnimation {
                    duration: Theme.mediumDuration
                }
            }

            Repeater {
                model: [
                    {
                        "alpha": 0.06,
                        "amplitude": 0.16,
                        "cycles": 2,
                        "phase": 0,
                        "duration": 9000
                    },
                    {
                        "alpha": 0.09,
                        "amplitude": 0.12,
                        "cycles": 3,
                        "phase": 1.4,
                        "duration": 7000
                    },
                    {
                        "alpha": 0.12,
                        "amplitude": 0.09,
                        "cycles": 4,
                        "phase": 2.6,
                        "duration": 5200
                    }
                ]

                // Painted once per size or color change; the loop only moves the strip.
                delegate: Canvas {
                    id: wave

                    required property var modelData

                    readonly property real period: waves.width / modelData.cycles
                    readonly property color fill: Theme.withAlpha(Theme.primary, modelData.alpha)

                    width: waves.width + period
                    height: waves.height
                    renderStrategy: Canvas.Cooperative

                    onFillChanged: requestPaint()
                    onWidthChanged: requestPaint()
                    onHeightChanged: requestPaint()

                    onPaint: {
                        const ctx = getContext("2d");
                        ctx.reset();
                        if (waves.width <= 0 || height <= 0)
                            return;
                        const amplitude = height * modelData.amplitude;
                        const baseline = amplitude + 2;
                        ctx.fillStyle = fill;
                        ctx.beginPath();
                        ctx.moveTo(0, height);
                        for (let x = 0; x <= width; x += 4)
                            ctx.lineTo(x, MediaFormat.waveY(x, waves.width, baseline, amplitude, modelData.cycles, modelData.phase));
                        ctx.lineTo(width, height);
                        ctx.closePath();
                        ctx.fill();
                    }

                    NumberAnimation on x {
                        from: 0
                        to: -wave.period
                        duration: wave.modelData.duration
                        loops: Animation.Infinite
                        running: waves.visible
                        paused: running && !root.animate
                    }
                }
            }
        }

        Rectangle {
            anchors.fill: parent
            radius: card.radius
            color: "transparent"
            border.width: 1
            border.color: Theme.withAlpha(Theme.primary, root.borderOpacity * 0.35)
        }
    }

    Column {
        anchors.centerIn: parent
        spacing: Theme.spacingS
        visible: !root.hasMedia

        DIcon {
            anchors.horizontalCenter: parent.horizontalCenter
            name: "music_note"
            size: Theme.iconSizeLarge
            color: Theme.surfaceVariantText
        }

        StyledText {
            anchors.horizontalCenter: parent.horizontalCenter
            text: I18n.trFor("mediaPlayer", "No media playing")
            font.pixelSize: Theme.fontSizeSmall
            color: Theme.surfaceVariantText
        }
    }

    Row {
        id: content
        anchors.fill: parent
        anchors.margins: Theme.spacingM
        spacing: Theme.spacingM
        visible: root.hasMedia

        Rectangle {
            id: thumbnail
            width: Math.min(content.height, content.width * 0.42)
            height: width
            anchors.verticalCenter: parent.verticalCenter
            radius: Theme.cornerRadiusS
            color: "transparent"
            border.width: 1
            border.color: Theme.withAlpha(Theme.primary, root.borderOpacity)

            MediaArtwork {
                id: artwork
                anchors.centerIn: parent
                width: parent.width * 0.78
                height: width
                cornerRadius: width / 2
                artUrl: TrackArtService.resolvedArtUrl

                NumberAnimation on rotation {
                    id: spin
                    from: 0
                    to: 360
                    duration: 20000
                    loops: Animation.Infinite
                    running: root.rotateThumbnail && root.hasMedia
                    paused: running && !root.animate
                    onRunningChanged: {
                        if (!running)
                            artwork.rotation = 0;
                    }
                }
            }
        }

        Column {
            id: details
            width: content.width - thumbnail.width - content.spacing
            anchors.verticalCenter: parent.verticalCenter
            spacing: Theme.spacingXS

            StyledText {
                width: parent.width
                text: MprisController.stableTitle || I18n.trFor("mediaPlayer", "Unknown track")
                font.pixelSize: Theme.fontSizeLarge
                font.weight: Font.Bold
                color: Theme.surfaceText
                elide: Text.ElideRight
                maximumLineCount: 1
            }

            StyledText {
                width: parent.width
                text: MprisController.stableArtist || I18n.trFor("mediaPlayer", "Unknown artist")
                font.pixelSize: Theme.fontSizeSmall
                color: Theme.surfaceVariantText
                elide: Text.ElideRight
                maximumLineCount: 1
            }

            Row {
                id: transport
                spacing: Theme.spacingXS
                topPadding: Theme.spacingXS

                DIconButton {
                    objectName: "previousButton"
                    iconName: "skip_previous"
                    iconColor: Theme.primary
                    enabled: !!root.activePlayer?.canGoPrevious || (!!root.activePlayer?.canSeek && root.activePlayer.position > 8)
                    Accessible.name: I18n.trFor("mediaPlayer", "Previous")
                    onClicked: MprisController.previousOrRewind()
                }

                DIconButton {
                    objectName: "playButton"
                    variant: "filled"
                    iconName: root.playing ? "pause" : "play_arrow"
                    enabled: !!root.activePlayer?.canTogglePlaying
                    Accessible.name: root.playing ? I18n.trFor("mediaPlayer", "Pause") : I18n.trFor("mediaPlayer", "Play")
                    onClicked: root.activePlayer.togglePlaying()
                }

                DIconButton {
                    objectName: "nextButton"
                    iconName: "skip_next"
                    iconColor: Theme.primary
                    enabled: !!root.activePlayer?.canGoNext
                    Accessible.name: I18n.trFor("mediaPlayer", "Next")
                    onClicked: MprisController.next()
                }
            }

            DSeekbar {
                id: seekbar
                objectName: "seekbar"
                width: parent.width
                height: 20
                activePlayer: root.activePlayer
                stableLength: root.trackLength
                visible: root.trackLength > 0
            }

            Item {
                width: parent.width
                height: elapsed.implicitHeight
                visible: seekbar.visible

                StyledText {
                    id: elapsed
                    objectName: "elapsedLabel"
                    anchors.left: parent.left
                    text: MediaFormat.formatTime(seekbar.value * root.trackLength)
                    font.pixelSize: Theme.fontSizeSmall
                    font.features: {
                        "tnum": 1
                    }
                    color: Theme.surfaceVariantText
                }

                StyledText {
                    objectName: "lengthLabel"
                    anchors.right: parent.right
                    text: MediaFormat.formatTime(root.trackLength)
                    font.pixelSize: Theme.fontSizeSmall
                    font.features: {
                        "tnum": 1
                    }
                    color: Theme.surfaceVariantText
                }
            }
        }
    }
}
