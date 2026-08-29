import QtQuick
import QtQuick.Layouts
import Theme
import components
import panels
import "../utils.js" as Utils

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

            UniversalButton {
                Layout.leftMargin: 10
                text: "Найти пир в сети Wi-Fi"
                onClicked: app.find_peers()
            }

            UniversalButton {
                text: "Проверить статус пиров"
                onClicked: app.check_status()
            }

            UniversalButton {
                Layout.rightMargin: 10
                text: "Добавить пир вручную"
                onClicked: currentScreen = pageAddPeer
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

    ListView { //Список пиров
        id: peersList
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
                onClicked: {
                    selectedPeer = model.peerID
                    currentScreen = pageAboutPeer
                }
                cursorShape: Qt.PointingHandCursor
            }
        }
    }

    ListModel {
        id: peersListModel
    }

    Connections {
        target: app
        function onNew_peer() {
            peersListModel.clear()
            for (var p of app.transfers) {
                peersListModel.append({
                    peerID: p.peer_id, lastSeen: Utils.formatDate(p.timestamp),
                    status: p.status
                })
            }
        }
    }
}
