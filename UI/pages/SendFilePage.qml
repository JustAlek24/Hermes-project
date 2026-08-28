import QtQuick
import QtQuick.Layouts
import QtQuick.Dialogs
import Theme
import panels
import components

PageWithBottomPanel {
    id: root

    HeaderPanel {currentPage: "Отправить файл"}

    property string selectedFilePath: ""
    property string selectedFileName: ""
    property string selectedPeerId: ""

    Rectangle {
        Layout.fillHeight: true
        Layout.fillWidth: true
        Layout.margins: 20
        radius: 10
        color: Theme.cardBackground

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 30
            spacing: 20

            Text {
                text: "Выберите файл для отправки"
                font.pixelSize: 18
                font.bold: true
                color: Theme.textColor
            }

            Rectangle {
                Layout.fillWidth: true
                height: 50
                radius: 8
                color: Theme.secondaryColor

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 15
                    anchors.rightMargin: 15

                    Text {
                        text: root.selectedFileName || "Файл не выбран"
                        Layout.fillWidth: true
                        color: root.selectedFileName ? Theme.textColor : Theme.textSecondaryColor
                        elide: Text.ElideMiddle
                    }

                    UniversalButton {
                        text: "Обзор..."
                        onClicked: fileDialog.open()
                    }
                }
            }

            Text {
                text: "Выберите пира"
                font.pixelSize: 16
                font.bold: true
                color: Theme.textColor
            }

            Rectangle {
                Layout.fillWidth: true
                height: 200
                radius: 8
                color: Theme.secondaryColor

                ListView {
                    id: peersListView
                    anchors.fill: parent
                    anchors.margins: 5
                    clip: true
                    model: peersModel

                    delegate: Rectangle {
                        width: ListView.view.width
                        height: 40
                        color: peerArea.containsMouse ? Theme.accentColor : "transparent"
                        radius: 4

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 10
                            anchors.rightMargin: 10

                            Text {
                                text: model.peerName
                                Layout.preferredWidth: 150
                            }
                            Text {
                                text: model.peerIP + ":" + model.peerPort
                                Layout.fillWidth: true
                            }
                        }

                        MouseArea {
                            id: peerArea
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: {
                                root.selectedPeerId = model.peerID
                            }
                            cursorShape: Qt.PointingHandCursor
                        }
                    }
                }

                ListModel { id: peersModel }
            }

            Text {
                text: root.selectedPeerId ? "Пир выбран" : "Пир не выбран"
                font.pixelSize: 12
                color: root.selectedPeerId ? Theme.buttonPrimary : Theme.textSecondaryColor
            }

            Item { Layout.fillHeight: true }

            RowLayout {
                Layout.fillWidth: true

                Item { Layout.fillWidth: true }

                UniversalButton {
                    text: "Отправить"
                    enabled: root.selectedFilePath !== "" && root.selectedPeerId !== ""
                    normalColor: Theme.buttonPrimary
                    hoverColor: Theme.buttonPrimaryHover
                    onClicked: {
                        app.send_file(root.selectedPeerId, root.selectedFilePath)
                        root.selectedFilePath = ""
                        root.selectedFileName = ""
                        root.selectedPeerId = ""
                        currentScreen = pageSent
                    }
                }
            }
        }
    }

    FileDialog {
        id: fileDialog
        title: "Выберите файл"
        onAccepted: {
            var path = fileDialog.selectedFile.toString()
            if (Qt.platform.os === "windows") {
                path = path.replace("file:///", "")
            } else {
                path = path.replace("file://", "")
            }
            root.selectedFilePath = path
            var parts = path.split("/")
            root.selectedFileName = parts[parts.length - 1]
        }
    }

    Connections {
        target: app
        function onPeersChanged() {
            peersModel.clear()
            for (var p of app.peers) {
                peersModel.append({
                    peerID: p.peer_id, peerName: p.peer_name,
                    peerIP: p.ip, peerPort: p.port
                })
            }
        }
    }

    Component.onCompleted: {
        peersModel.clear()
        for (var p of app.peers) {
            peersModel.append({
                peerID: p.peer_id, peerName: p.peer_name,
                peerIP: p.ip, peerPort: p.port
            })
        }
    }
}
