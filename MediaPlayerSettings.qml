import Quickshell
import QtQuick
import qs.Common
import qs.Modules.Plugins

PluginSettings {
    id: root
    pluginId: "mediaPlayer"

    SliderSetting {
        settingKey: "backgroundOpacity"
        label: I18n.tr("Background Opacity")
        defaultValue: 80
        minimum: 0
        maximum: 100
        unit: "%"
    }
}