import QtQuick
import QtQuick.Layouts
import Theme
import components
import panels

PageWithBottomPanel {

    HeaderPanel {currentPage: "Известные пиры"}

    Rectangle { //Панель кнопок для работы с пирами
        id: peersButtons
        height: 60
        color: Theme.mainTopleftPanelColor
        Layout.fillWidth: true
        RowLayout { //Строка кнопок
            anchors.fill: parent
            
            spacing: 20

            PeersButton {
            
                Layout.fillWidth: true
                Layout.leftMargin: 10
                Layout.preferredWidth: 200
                text: "Найти пир в сети Wi-Fi"
                onClicked: app.find_peers()
            }

            PeersButton {
                Layout.preferredWidth: 200
                Layout.fillWidth: true
                text: "Проверить статус пиров"
                onClicked: app.check_status()
            }

            PeersButton {
                Layout.fillWidth: true
                Layout.rightMargin: 10
                Layout.preferredWidth: 200
                text: "Добавить пир вручную"
                onClicked: app.add_peer()
            }
        }
    }

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
                text: "Был в сети"
                Layout.fillWidth: true
            }
            Text {
                text: "Статус"
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
        

        model: peersListModel

        delegate: Rectangle {

            width: ListView.view.width
            height: 50
            color: listArea.containsMouse ? Theme.accentColor : "transparent"
            RowLayout {
                anchors.fill: parent

                Text {
                    text: model.peerID
                    Layout.preferredWidth: 150
                    Layout.leftMargin: 10
                }

                Text {
                    text: model.lastSeen
                    Layout.fillWidth: true
                }

                Text {
                    text: model.status
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
        id: peersListModel
        ListElement { peerID: "Абоба"; lastSeen: "Чуркистан"; status: "Негры"}
        ListElement { peerID: "Абоба"; lastSeen: "Чуркистан"; status: "Негры"}
        ListElement { peerID: "Абоба"; lastSeen: "Чуркистан"; status: "Негры"}
        ListElement { peerID: "Абоба"; lastSeen: "Чуркистан"; status: "Негры"}
        ListElement { peerID: "Абоба"; lastSeen: "Чуркистан"; status: "Негры"}
        ListElement { peerID: "Абоба"; lastSeen: "Чуркистан"; status: "Негры"}
        ListElement { peerID: "Абоба"; lastSeen: "Чуркистан"; status: "Негры"}
        ListElement { peerID: "Абоба"; lastSeen: "Чуркистан"; status: "Негры"}
        ListElement { peerID: "Абоба"; lastSeen: "Чуркистан"; status: "Негры"}
        ListElement { peerID: "Абоба"; lastSeen: "Чуркистан"; status: "Негры"}
        ListElement { peerID: "Абоба"; lastSeen: "Чуркистан"; status: "Негры"}
        ListElement { peerID: "Абоба"; lastSeen: "Чуркистан"; status: "Негры"}
        ListElement { peerID: "Абоба"; lastSeen: "Чуркистан"; status: "Негры"}
        ListElement { peerID: "Абоба"; lastSeen: "Чуркистан"; status: "Негры"}
        ListElement { peerID: "Абоба"; lastSeen: "Чуркистан"; status: "Негры"}
        ListElement { peerID: "Абоба"; lastSeen: "Чуркистан"; status: "Негры"}
        ListElement { peerID: "Абоба"; lastSeen: "Чуркистан"; status: "Негры"}
        ListElement { peerID: "Абоба"; lastSeen: "Чуркистан"; status: "Негры"}
        ListElement { peerID: "Абоба"; lastSeen: "Чуркистан"; status: "Негры"}
        ListElement { peerID: "Абоба"; lastSeen: "Чуркистан"; status: "Негры"}
        ListElement { peerID: "Абоба"; lastSeen: "Чуркистан"; status: "Негры"}

    }
}