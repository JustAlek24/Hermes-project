import QtQuick
import QtQuick.Layouts
import Theme

ColumnLayout {
    Rectangle { //Верхняя панель
        id: topPanel
        Layout.fillWidth: true
        height: 80
        color: Theme.mainTopleftPanelColor

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
                color: menuMouseArea.containsMouse ? Theme.accentColor : "transparent"
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
                height: 48
                anchors.verticalCenter: parent.verticalCenter
                radius: 8
                color: sendMouseArea.containsMouse ? Theme.accentColor : "transparent"
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
                    onClicked: currentScreen = pageSendFile
                    cursorShape: Qt.PointingHandCursor
                }
            }
        }
    }

    Rectangle { //Шапка таблицы
        id: tableHead
        height: 40
        Layout.fillWidth: true
        color: Theme.backgroundColor
        RowLayout {
            anchors.fill: parent
            Text {
                text: "ID пира"
                Layout.preferredWidth: 150
                Layout.leftMargin: 10
            }
            Text {
                text: "Сообщение"
                Layout.fillWidth: true
            }
            Text {
                text: "Дата"
                Layout.preferredWidth: 100
                Layout.rightMargin: 10
            }
        }
    }

    ListView {
        id: incomingMessages
        Layout.fillHeight: true
        Layout.fillWidth: true
        clip: true

        model: incomingMessageModel

        delegate: Rectangle {

            width: parent.width
            height: 50
            //color: index % 2 === 0 ? "transparent" : Theme.tableColor
            color: listArea.containsMouse ? Theme.accentColor : "transparent"
            RowLayout {
                anchors.fill: parent

                Text {
                    text: model.peerID
                    Layout.preferredWidth: 150
                    Layout.leftMargin: 10
                }

                Text {
                    text: model.message
                    Layout.fillWidth: true
                }

                Text {
                    text: model.date
                    Layout.preferredWidth: 100
                    Layout.rightMargin: 10
                }
            }

            Rectangle {
                anchors.bottom: parent.bottom
                anchors.right: parent.right
                anchors.left: parent.left
            
                color: Theme.textSecondaryColor
                width: parent.width
                height: 1
            }
        
            MouseArea {
                id: listArea
                anchors.fill: parent
                hoverEnabled: true
                onClicked: currentScreen = pageViewIncoming
                cursorShape: Qt.PointingHandCursor
            }
        }
    }

    ListModel {
        id: incomingMessageModel
        ListElement {
            peerID: "Абоба"
            message: "Чуркистан"
            date: "Негры"
        }
    }   
    
    Rectangle { //Нижняя панель со статусом работы
        id: bottomPanel
        Layout.fillWidth: true
        height: 100
        color: Theme.leftPanelColor
    }
}