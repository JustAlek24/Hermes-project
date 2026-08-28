import QtQuick
import Theme
import QtQuick.Layouts

Rectangle {
    id: root
    property string text: ""
    property string icon: ""
    property color normalColor: "transparent"
    property color hoverColor: Theme.accentColor
    signal clicked()

    height: 50
    radius: 8

    Layout.preferredWidth: 200
    Layout.fillWidth: true

    opacity: root.enabled ? 1.0 : 0.4

    color: root.enabled && mouseArea.containsMouse ? root.hoverColor : root.normalColor

    Behavior on color {
        ColorAnimation {
            duration: 300
        }
    }

    Row {
        anchors.centerIn: parent

        spacing: 10
        padding: 10

        Text {
            text: root.text
            font.pixelSize: 16
            color: Theme.textColor
        }
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: root.enabled
        enabled: root.enabled
        onClicked: {
            if (root.enabled)
                root.clicked()
        }
        cursorShape: root.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
    }
}
