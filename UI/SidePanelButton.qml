import QtQuick
import QtQuick.Controls

Rectangle {
    id: root
    property string text: ""
    property string icon: ""
    property bool collapsed: false
    property color accentColor: '#9fa0fe'
    property color textColor: '#00014c'
    signal clicked()

    anchors.left: parent.left
    anchors.right: parent.right
    height: 50
    radius: 8
    color: mouseArea.containsMouse ? accentColor : "transparent"

    Behavior on color {
        ColorAnimation {
            duration: 200
        }
    }

    Row {
        anchors.verticalCenter: parent.verticalCenter
        spacing: 10

        Image {
            id: buttonIcon
            source: root.icon
            width: 24
            height: 24
            anchors.left: parent.left
            anchors.leftMargin: 10
            anchors.verticalCenter: parent.verticalCenter
            fillMode: Image.PreserveAspectFit
        }

        Text {
            text: root.text
            font.pixelSize: 16
            color: root.textColor
            anchors.left: buttonIcon.right
            anchors.leftMargin: 10
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