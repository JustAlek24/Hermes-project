import QtQuick
import QtQuick.Layouts
import panels
import components
import Theme
import "../utils.js" as Utils

PageWithBottomPanel {
    id: root

    // Отслеживает выбранную передачу (свойство главного окна).
    // Страница создаётся один раз, поэтому пересчитываем данные
    // при смене выделения, а не только при переключении страниц.
    property string watchedTransferId: selectedTransferId
    onWatchedTransferIdChanged: root.updateTransfer()

    property var currentTransfer: ({
        transfer_id: "-",
        peer_name: "-", 
        filename: "-", 
        file_size: "-",
        timestamp: "-", 
        sha256: "-", 
        status: "error"
    })


    HeaderPanel {
        id: headerPanel
        currentPage: root.currentTransfer.direction === "out" ? "Отправленное сообщение" : "Входящее сообщение"
    }
    
    Item {
        Layout.fillWidth: true
        z: -1

        StatusIndicator {
            status: root.currentTransfer.status
            anchors.horizontalCenter: parent.right
            anchors.verticalCenter: parent.top
        }
    }


    Rectangle {
        id: infoBar
        z: -2
        radius: 10

        Layout.fillHeight: true
        Layout.fillWidth: true
        Layout.margins: 10

        color: Theme.cardBackground
        
        ColumnLayout {
            
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.right: parent.right
            anchors.bottom: parent.bottom

            anchors.leftMargin: 30
            anchors.rightMargin: 30

            Text {
                id: headerText
                Layout.alignment: Qt.AlignHCenter

                text: root.currentTransfer.peer_name
                font.pixelSize: 22
            }

            InfoRow {label: "Файл: "; value: root.currentTransfer.filename}
            InfoRow {label: "Размер: "; value: Utils.formatSize(root.currentTransfer.file_size)}
            InfoRow {label: "Дата: "; value: Utils.formatDate(root.currentTransfer.timestamp)}
            InfoRow {label: "SHA256: "; value: root.currentTransfer.sha256}

            CustomProgressBar {
                id: transferProgressBar
                Layout.fillWidth: true
                Layout.topMargin: 18
                Layout.preferredHeight: 16
                visible: {
                    var s = root.currentTransfer.status
                    return s === "pending" || s === "accepted" || s === "sending" || s === "receiving"
                }
                value: {
                    var p = app.transfer_progress[root.currentTransfer.transfer_id]
                    return p !== undefined ? p / 100 : 0
                }
            }

            Text {
                id: progressHint
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: 4
                visible: transferProgressBar.visible
                text: {
                    var s = root.currentTransfer.status
                    if (s === "pending") return "Ожидает решения..."
                    if (s === "accepted") return "Принято, идёт приём файла..."
                    if (s === "sending") return "Идёт отправка файла..."
                    if (s === "receiving") return "Идёт приём файла..."
                    return ""
                }
                font.pixelSize: 12
                color: Theme.textSecondaryColor
            }
        }
    }

    Rectangle {
        visible: (root.currentTransfer.direction === "in" && root.currentTransfer.status === "pending") ? true : false
        height: 100

        radius: 10

        Layout.fillWidth: true
        Layout.margins: 10
        Layout.leftMargin: 100
        Layout.rightMargin: 100

        RowLayout {
            anchors.fill: parent
            spacing: 20
            UniversalButton {
                text: "Принять"
                Layout.leftMargin: 10
                normalColor: Theme.buttonPrimary
                hoverColor: Theme.buttonPrimaryHover 
                onClicked: {
                    var dir = app.choose_save_dir()
                    if (dir) {
                        app.accept_transfer(root.currentTransfer.transfer_id)
                    }
                }
            }

            UniversalButton {
                text: "Отклонить"
                Layout.rightMargin: 10
                normalColor: Theme.buttonSecondary
                hoverColor: Theme.buttonSecondaryHover
                onClicked: app.reject_transfer(root.currentTransfer.transfer_id)
            }
        }

        Behavior on height {
            NumberAnimation {
                duration: 300
                easing.type: Easing.OutCubic
            }
        }
    }

    function updateTransfer() {
        for (let i = 0; i < app.transfers.length; i++) {
            if (app.transfers[i].transfer_id === selectedTransferId) {
                root.currentTransfer = app.transfers[i]
                return
            }
        }
        root.currentTransfer = ({
            transfer_id: "-",
            peer_name: "-", filename: "-", file_size: "-",
            timestamp: "-", sha256: "-", status: "pending"
        })
    }

    Connections {
        target: app
        function onTransfersChanged() {
            root.updateTransfer()
        }
    }
}