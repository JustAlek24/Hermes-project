import QtQuick
import QtQuick.Layouts
import Theme
import panels
import components

PageWithBottomPanel {

    HeaderPanel {currentPage: "Отправленные"}

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
}