import QtQuick
import QtQuick.Controls

Rectangle {
    property string text: ""
    property string icon: ""
    property color accentColor: '#9fa0fe'
    property color textColor: '#00014c'
    signal clicked()

    anchors.left: parent.left
    anchors.right: parent.right
    height:50
    radius: 8
    color: mouseArea.containsMouse ? accentColor : "transparent"

    Behavior on color {
        ColorAnimation {
            duration: 200
        }
    }

    Row {
        anchors.left: parent.left
        anchors.leftMargin: 15
        anchors.right: parent.right
        anchors.rightMargin: 15
        anchors.verticalCenter: parent.verticalCenter
        spacing: 10

        Image {
            source: parent.parent.icon
            width: 24
            height: 24
            anchors.verticalCenter: parent.verticalCenter
            fillMode: Image.PreserveAspectFit
        }

        Text {
            text: parent.parent.text
            font.pixelSize: 16
            color: textColor
            anchors.verticalCenter: parent.verticalCenter
        }
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        onClicked: parent.clicked()
    }
}