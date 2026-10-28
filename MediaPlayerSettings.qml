import QtQuick
import qs.Common
import qs.Modules.Plugins

PluginSettings {
    id: root
    pluginId: "mediaPlayer"

    SliderSetting {
        settingKey: "backgroundOpacity"
        label: I18n.trFor("mediaPlayer", "Background opacity")
        defaultValue: 80
        minimum: 0
        maximum: 100
        unit: "%"
    }

    SliderSetting {
        settingKey: "borderOpacity"
        label: I18n.trFor("mediaPlayer", "Border opacity")
        defaultValue: 100
        minimum: 0
        maximum: 100
        unit: "%"
    }

    ToggleSetting {
        settingKey: "rotateThumbnail"
        label: I18n.trFor("mediaPlayer", "Rotate album art")
        description: I18n.trFor("mediaPlayer", "Spin the album art while media is playing")
        defaultValue: true
    }

    ToggleSetting {
        settingKey: "showWaves"
        label: I18n.trFor("mediaPlayer", "Wave background")
        description: I18n.trFor("mediaPlayer", "Draw animated waves behind the controls while media is playing")
        defaultValue: true
    }

    ToggleSetting {
        settingKey: "showArtBackdrop"
        label: I18n.trFor("mediaPlayer", "Album art backdrop")
        description: I18n.trFor("mediaPlayer", "Use a blurred copy of the album art as the background")
        defaultValue: false
    }

    ToggleSetting {
        settingKey: "hideWhenIdle"
        label: I18n.trFor("mediaPlayer", "Hide when idle")
        description: I18n.trFor("mediaPlayer", "Hide the widget when no media is playing")
        defaultValue: true
    }
}
