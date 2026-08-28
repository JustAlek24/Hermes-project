import QtQuick
import QtQuick.Layouts
import Theme
import components
import panels

PageWithBottomPanel {

    HeaderPanel {currentPage: "Известные пиры"}

    Rectangle {
        id: peersButtons
        height: 60
        color: Theme.mainTopleftPanelColor
        Layout.fillWidth: true
        RowLayout {
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

    Rectangle {
        id: tableHead
        height: 40
        Layout.fillWidth: true
        color: Theme.secondaryColor
        RowLayout {
            anchors.fill: parent
            Text {
                text: "Имя пира"
                Layout.preferredWidth: 150
                Layout.leftMargin: 10
            }
            Text {
                text: "IP"
                Layout.fillWidth: true
            }
            Text {
                text: "Порт"
                Layout.preferredWidth: 80
                Layout.rightMargin: 10
            }
        }
    }

    ListView {
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
                    text: model.peerName
                    Layout.preferredWidth: 150
                    Layout.leftMargin: 10
                }

                Text {
                    text: model.peerIP
                    Layout.fillWidth: true
                }

                Text {
                    text: model.peerPort
                    Layout.preferredWidth: 80
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
        function onPeersChanged() {
            peersListModel.clear()
            for (var p of app.peers) {
                peersListModel.append({
                    peerID: p.peer_id, peerName: p.peer_name,
                    peerIP: p.ip, peerPort: p.port
                })
            }
        }
    }

    Component.onCompleted: {
        peersListModel.clear()
        for (var p of app.peers) {
            peersListModel.append({
                peerID: p.peer_id, peerName: p.peer_name,
                peerIP: p.ip, peerPort: p.port
            })
        }
    }
}
