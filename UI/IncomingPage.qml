import QtQuick
import QtQuick.Layouts
import Theme

Column {
    Rectangle { //Верхняя панель
        id: topPanel
        width: parent.width
        height: 80
        color: Theme.primaryColor

        Row {
            anchors.fill: parent
            spacing: 16
            leftPadding: 16
            rightPadding: 16
            Rectangle { //Кнопка меню
                width: 48
                height: 48
                anchors.verticalCenter: parent.verticalCenter
                radius: 8
                color: menuMouseArea.containsMouse ? Qt.rgba(1,1,1,0.2) : "transparent"
                Text {
                    anchors.centerIn: parent
                    text: "☰"
                    font.pixelSize: 28
                    color: Theme.textColor
                }
                MouseArea {
                    id: menuMouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: leftPanelVisible = !leftPanelVisible
                    cursorShape: Qt.PointingHandCursor
                }
            }
            Rectangle { // Кнопка отправить
                width: 220
                height: parent.height
                radius: 8
                color: sendMouseArea.containsMouse ? Qt.rgba(1,1,1,0.2) : "transparent"
                Row {
                    anchors.left: parent.left
                    anchors.leftMargin: 15
                    anchors.right: parent.right
                    anchors.rightMargin: 15
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 10
                    Image {
                        source: "icons/send_icon.png"
                        width: 24
                        height: 24
                        anchors.verticalCenter: parent.verticalCenter
                        fillMode: Image.PreserveAspectFit
                    }
                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        text: "Отправить"
                        font.pixelSize: 22
                        font.bold: true
                        color: Theme.textColor
                    }
                }
                MouseArea {
                    id: sendMouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: currentScreen = 3
                    cursorShape: Qt.PointingHandCursor
                }
            }
        }
    }
}
