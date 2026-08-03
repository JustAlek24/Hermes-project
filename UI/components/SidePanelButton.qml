import QtQuick
import Theme

Rectangle {
    id: root
    property string text: ""
    property string icon: ""
    property bool collapsed: false
    signal clicked()

    height: 50
    radius: 8
    color: mouseArea.containsMouse ? Theme.accentColor : "transparent"

    Behavior on color {
        ColorAnimation {
            duration: 300
        }
    }

    Row {
        anchors.verticalCenter: parent.verticalCenter
        spacing: 10
        padding: 10

        Image {
            id: buttonIcon
            source: root.icon
            width: 24
            height: 24
            anchors.verticalCenter: parent.verticalCenter
            fillMode: Image.PreserveAspectFit
        }

        Text {
            text: root.text
            font.pixelSize: 16
            color: Theme.textColor
            anchors.verticalCenter: parent.verticalCenter
            visible: !root.collapsed
        }
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        onClicked: root.clicked()
    }
}