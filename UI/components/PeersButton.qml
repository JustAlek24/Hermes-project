import QtQuick
import QtQuick.Layouts
import Theme

Rectangle {
    id: root
    property string text: ""
    property string icon: ""
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
        hoverEnabled: true
        onClicked: root.clicked()
    }
}