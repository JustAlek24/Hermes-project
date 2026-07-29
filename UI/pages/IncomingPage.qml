import QtQuick
import QtQuick.Layouts
import Theme
import panels

ColumnLayout {
    spacing: 0

    HeaderPanel {currentPage: "Входящие"}

    Rectangle { //Шапка таблицы
        id: tableHead
        height: 40
        Layout.fillWidth: true
        color: Theme.secondaryColor
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

    ListView { //Список входящих
        id: incomingMessages
        Layout.fillHeight: true
        Layout.fillWidth: true
        clip: true
        

        model: incomingMessageModel

        delegate: Rectangle {

            width: ListView.view.width
            height: 50

            color: listArea.containsMouse ? Theme.accentColor : "transparent"

            Behavior on color {
                ColorAnimation {
                    duration: 300
                }
            }

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
        ListElement { peerID: "Абоба"; message: "Чуркистан"; date: "Негры"}
        ListElement { peerID: "Абоба"; message: "Чуркистан"; date: "Негры"}
        ListElement { peerID: "Абоба"; message: "Чуркистан"; date: "Негры"}
        ListElement { peerID: "Абоба"; message: "Чуркистан"; date: "Негры"}
        ListElement { peerID: "Абоба"; message: "Чуркистан"; date: "Негры"}
        ListElement { peerID: "Абоба"; message: "Чуркистан"; date: "Негры"}
        ListElement { peerID: "Абоба"; message: "Чуркистан"; date: "Негры"}
        ListElement { peerID: "Абоба"; message: "Чуркистан"; date: "Негры"}
        ListElement { peerID: "Абоба"; message: "Чуркистан"; date: "Негры"}
        ListElement { peerID: "Абоба"; message: "Чуркистан"; date: "Негры"}
        ListElement { peerID: "Абоба"; message: "Чуркистан"; date: "Негры"}
        ListElement { peerID: "Абоба"; message: "Чуркистан"; date: "Негры"}

        ListElement { peerID: "Абоба"; message: "Чуркистан"; date: "Негры"}
        ListElement { peerID: "Абоба"; message: "Чуркистан"; date: "Негры"}
        ListElement { peerID: "Абоба"; message: "Чуркистан"; date: "Негры"}
        ListElement { peerID: "Абоба"; message: "Чуркистан"; date: "Негры"}
        ListElement { peerID: "Абоба"; message: "Чуркистан"; date: "Негры"}
        ListElement { peerID: "Абоба"; message: "Чуркистан"; date: "Негры"}
        ListElement { peerID: "Абоба"; message: "Чуркистан"; date: "Негры"}
        ListElement { peerID: "Абоба"; message: "Чуркистан"; date: "Негры"}

    }   
    
    Rectangle { //Нижняя панель со статусом работы
        id: bottomPanel
        Layout.fillWidth: true
        height: 100
        color: Theme.leftPanelColor
    }
}

//Rectangle { // Кнопка отправить
//    id: rightButton
//    width: 220
//    height: 48
//    Layout.rightMargin: 16
//
//    radius: 8
//    color: sendMouseArea.containsMouse ? Theme.accentColor : "transparent"
//    Row {
//        anchors.left: parent.left
//        anchors.leftMargin: 15
//        anchors.right: parent.right
//        anchors.rightMargin: 15
//        anchors.verticalCenter: parent.verticalCenter
//        spacing: 10
//        Image {
//            source: "icons/send_icon.png"
//            width: 20
//            height: 20
//            anchors.verticalCenter: parent.verticalCenter
//            fillMode: Image.PreserveAspectFit
//        }
//        Text {
//            anchors.verticalCenter: parent.verticalCenter
//            text: "Отправить"
//            font.pixelSize: 20
//            font.bold: true
//            color: Theme.textColor
//        }
//    }
//    MouseArea {
//        id: sendMouseArea
//        anchors.fill: parent
//        hoverEnabled: true
//        onClicked: currentScreen = pageSendFile
//        cursorShape: Qt.PointingHandCursor
//    }
//}