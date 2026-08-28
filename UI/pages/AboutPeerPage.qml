import QtQuick
import QtQuick.Layouts
import Theme
import panels
import components

PageWithBottomPanel {
    id: root

    HeaderPanel {currentPage: "Информация о пире"}

    property var peerData: null

    // Отслеживает выбранного пира (свойство главного окна).
    // Поскольку страница создаётся один раз, пересчитываем данные
    // при смене выделения, а не только при загрузке.
    property string watchedPeer: selectedPeer
    onWatchedPeerChanged: root.loadPeer()

    function loadPeer() {
        for (var p of app.peers) {
            if (p.peer_id === selectedPeer) {
                peerData = p
                return
            }
        }
        peerData = null
    }

    Connections {
        target: app
        function onPeersChanged() { root.loadPeer() }
    }

    Component.onCompleted: root.loadPeer()

    Rectangle {
        Layout.fillHeight: true
        Layout.fillWidth: true
        Layout.margins: 20
        radius: 10
        color: Theme.cardBackground
        visible: root.peerData !== null

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 30
            spacing: 15

            Text {
                text: root.peerData ? root.peerData.peer_name : ""
                font.pixelSize: 22
                font.bold: true
                color: Theme.textColor
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: Theme.textSecondaryColor }

            RowLayout {
                Text { text: "ID: "; color: Theme.textSecondaryColor; font.pixelSize: 14 }
                Text { text: root.peerData ? root.peerData.peer_id : ""; color: Theme.textColor; font.pixelSize: 14 }
            }

            RowLayout {
                Text { text: "IP: "; color: Theme.textSecondaryColor; font.pixelSize: 14 }
                Text { text: root.peerData ? root.peerData.ip : ""; color: Theme.textColor; font.pixelSize: 14 }
            }

            RowLayout {
                Text { text: "Порт: "; color: Theme.textSecondaryColor; font.pixelSize: 14 }
                Text { text: root.peerData ? root.peerData.port : ""; color: Theme.textColor; font.pixelSize: 14 }
            }

            RowLayout {
                Text { text: "Версия: "; color: Theme.textSecondaryColor; font.pixelSize: 14 }
                Text { text: root.peerData ? root.peerData.version : ""; color: Theme.textColor; font.pixelSize: 14 }
            }

            Item { Layout.fillHeight: true }

            RowLayout {
                Layout.fillWidth: true

                UniversalButton {
                    text: "Назад"
                    onClicked: currentScreen = pagePeers
                }

                Item { Layout.fillWidth: true }

                UniversalButton {
                    text: "Удалить пира"
                    normalColor: Theme.buttonSecondary
                    hoverColor: Theme.buttonSecondaryHover
                    onClicked: {
                        if (root.peerData) {
                            app.remove_peer(root.peerData.peer_id)
                            currentScreen = pagePeers
                        }
                    }
                }
            }
        }
    }

    Rectangle {
        Layout.fillHeight: true
        Layout.fillWidth: true
        Layout.margins: 20
        radius: 10
        color: Theme.cardBackground
        visible: root.peerData === null

        Text {
            anchors.centerIn: parent
            text: "Пир не найден"
            color: Theme.textSecondaryColor
            font.pixelSize: 16
        }
    }
}
