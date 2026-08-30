import QtQuick
import QtQuick.Layouts
import Theme
import components
import panels
import "../utils.js" as Utils

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
                Layout.preferredWidth: 150
            }
            Text {
                text: "Был в сети"
                Layout.fillWidth: true
            }
            Text {
                text: "Статус"
                Layout.preferredWidth: 90
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
                    elide: Text.ElideRight
                }

                Text {
                    text: model.peerIP
                    Layout.preferredWidth: 150
                    elide: Text.ElideRight
                }

                Text {
                    text: model.lastSeen
                    Layout.fillWidth: true
                }

                RowLayout {
                    Layout.preferredWidth: 90
                    Layout.rightMargin: 10
                    spacing: 6

                    Rectangle {
                        width: 10
                        height: 10
                        radius: 5
                        color: model.status === "online" ? Theme.statusOnline
                             : model.status === "missed" ? Theme.statusMissed
                             : Theme.statusOffline
                    }
                    Text {
                        text: model.statusText
                        color: Theme.textColor
                    }
                }
            }

            Rectangle {
                anchors.bottom: parent.bottom
                anchors.right: parent.right
                anchors.left: parent.left
            
                color: Theme.divider
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
            appendPeers()
        }
        function onPeerStatusChanged() {
            appendPeers()
        }
    }

    function peerStatusOf(p) {
        var st = app.peer_status[p.peer_id]
        if (st === "online") return "online"
        if (st === "missed" || st === "warning") return "missed"
        return "offline"
    }

    function statusTextOf(status) {
        if (status === "online") return "онлайн"
        if (status === "missed") return "пропущен"
        return "офлайн"
    }

    function appendPeers() {
        var items = []
        for (var p of app.peers) {
            var st = peerStatusOf(p)
            items.push({
                peerID: p.peer_id, peerName: p.peer_name,
                peerIP: p.ip, peerPort: p.port,
                lastSeen: Utils.formatRelative(p.last_seen),
                status: st,
                statusText: statusTextOf(st)
            })
        }
        Utils.fillListModel(peersListModel, items)
    }

    Component.onCompleted: appendPeers()
}
