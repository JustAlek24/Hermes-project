import QtQuick
import Theme

Rectangle {
    id: bar

    // Прогресс в диапазоне [from; to]; внутри нормализуется в 0..1.
    property real from: 0
    property real to: 1
    property real value: 0
    property bool showLabel: true
    property int labelSize: 10
    property color trackColor: Theme.divider
    property color fillStartColor: Theme.accentColor
    property color fillEndColor: Theme.secondaryColor
    property color labelColor: Theme.textColor

    implicitHeight: 14
    radius: height / 2
    color: trackColor

    readonly property real progress: {
        var span = bar.to - bar.from
        var raw = span !== 0 ? (bar.value - bar.from) / span : 0
        return Math.max(0, Math.min(1, raw))
    }

    // Заполнение
    Rectangle {
        id: fill
        height: bar.height
        width: bar.width * bar.progress
        radius: height / 2
        clip: true

        gradient: Gradient {
            GradientStop { position: 0.0; color: bar.fillStartColor }
            GradientStop { position: 1.0; color: bar.fillEndColor }
        }

        // Блик, пробегающий по заполненной части
        Rectangle {
            id: glint
            x: -width
            width: bar.width * 0.25
            height: bar.height * 0.6
            anchors.verticalCenter: parent.verticalCenter
            radius: height / 2
            color: "#40ffffff"

            NumberAnimation on x {
                running: bar.visible && bar.progress > 0.01 && bar.progress < 1
                from: -glint.width
                to: bar.width + glint.width
                duration: 2600
                loops: Animation.Infinite
            }
        }

        Behavior on width {
            NumberAnimation {
                duration: 220
                easing.type: Easing.OutCubic
            }
        }
    }

    // Процентный текст поверх полоски
    Text {
        id: pct
        anchors.centerIn: parent
        visible: bar.showLabel && bar.width > 56
        text: Math.round(bar.progress * 100) + "%"
        font.pixelSize: bar.labelSize
        font.bold: true
        // Текст лежит на заполнении -> белый, иначе обычный цвет.
        color: fill.width >= (bar.width - 38) / 2 + 38 ? "#ffffff" : bar.labelColor
    }
}