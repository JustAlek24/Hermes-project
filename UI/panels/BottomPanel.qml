import QtQuick
import QtQuick.Layouts
import components
import Theme
import "../utils.js" as Utils

Rectangle {
    id: bottomPanel

    property bool expanded: false

    height: expanded ? parent.height * 0.6 : 80

    color: Theme.leftPanelColor

    signal expandedSignal

    Behavior on height {
        NumberAnimation {
            duration: 300
            easing.type: Easing.OutCubic
        }
    }

    // Ручка-хендл сверху панели (перетаскивание не делаем, просто визуальный якорь)
    Rectangle {
        id: handle
        width: 48
        height: 5
        radius: 2.5
        anchors.top: parent.top
        anchors.topMargin: 6
        anchors.horizontalCenter: parent.horizontalCenter
        color: Theme.textSecondaryColor
        visible: bottomPanel.expanded
    }

    // ---------- Свёрнутое состояние ----------
    RowLayout {
        id: collapsedRow
        anchors.fill: parent
        anchors.topMargin: 12
        visible: !bottomPanel.expanded && !expanded

        Text {
            Layout.leftMargin: 20
            Layout.alignment: Qt.AlignVCenter
            text: "Внутренний IP: " + app.own_address
            font.pixelSize: 14
            color: Theme.textColor
        }
        Text {
            Layout.leftMargin: 20
            Layout.alignment: Qt.AlignVCenter
            text: "Онлайн: " + app.online_count
            font.pixelSize: 14
            color: Theme.textColor
        }

        CustomProgressBar {
            id: activeProgress
            Layout.fillWidth: true
            Layout.preferredHeight: 18
            Layout.alignment: Qt.AlignVCenter
            Layout.leftMargin: 20
            Layout.rightMargin: 15
            visible: app.transfers.length > 0
            value: {
                var progress = app.transfer_progress
                var keys = Object.keys(progress)
                if (keys.length === 0)
                    return 0
                var maxPct = 0
                for (var k of keys)
                    maxPct = Math.max(maxPct, progress[k] / 100)
                return maxPct
            }
        }
        Text {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignVCenter
            Layout.leftMargin: 20
            horizontalAlignment: Text.AlignRight
            Layout.rightMargin: 15
            visible: app.transfers.length == 0
            text: "Приёма/передачи файлов не происходит"
            font.pixelSize: 14
            color: Theme.textColor
        }
    }

    // ---------- Развёрнутое состояние ----------
    ColumnLayout {
        id: expandedColumn
        anchors.fill: parent
        anchors.topMargin: 18
        anchors.leftMargin: 20
        anchors.rightMargin: 20
        spacing: 8
        visible: bottomPanel.expanded

        Text {
            text: "Детализация передач"
            font.pixelSize: 16
            font.bold: true
            color: Theme.textColor
        }

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: Theme.divider
        }

        ListView {
            id: transfersList
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            model: transfersListModel

            delegate: Rectangle {
                width: transfersList.width
                height: 64
                color: "transparent"

                ColumnLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 8
                    anchors.rightMargin: 8
                    spacing: 3

                    RowLayout {
                        Layout.fillWidth: true
                        Text {
                            text: (model.direction === "out" ? "→ " : "← ") + model.peerName
                            font.bold: true
                            color: Theme.textColor
                        }
                        Item { Layout.fillWidth: true }
                        Text {
                            text: model.status
                            color: Theme.textSecondaryColor
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Text {
                            text: model.filename
                            elide: Text.ElideMiddle
                            Layout.fillWidth: true
                            color: Theme.textColor
                        }
                        Text {
                            text: "Размер: " + Utils.formatSize(model.fileSize)
                            color: Theme.textSecondaryColor
                        }
                    }
                    CustomProgressBar {
                        id: rowProgress
                        Layout.fillWidth: true
                        Layout.preferredHeight: 10
                        visible: model.status === "sending" || model.status === "receiving" || model.status === "accepted"
                        value: app.transfer_progress[model.transferId] !== undefined
                               ? app.transfer_progress[model.transferId] / 100 : 0
                    }
                    Text {
                        text: "SHA256: " + model.sha256
                        elide: Text.ElideRight
                        color: Theme.textSecondaryColor
                        font.pixelSize: 11
                        Layout.fillWidth: true
                    }
                }

                Rectangle {
                    anchors.bottom: parent.bottom
                    anchors.left: parent.left
                    anchors.right: parent.right
                    height: 1
                    color: Theme.divider
                }
            }
        }
    }

    ListModel {
        id: transfersListModel
    }

    function refresh() {
        var items = []
        for (var t of app.transfers) {
            items.push({
                transferId: t.transfer_id,
                direction: t.direction,
                peerName: t.peer_name,
                filename: t.filename,
                fileSize: t.file_size,
                status: t.status,
                sha256: t.sha256
            })
        }
        Utils.fillListModel(transfersListModel, items)
    }

    Connections {
        target: app
        function onTransfersChanged() { bottomPanel.refresh() }
    }

    Component.onCompleted: bottomPanel.refresh()

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        visible: !expanded
        hoverEnabled: true
        onClicked: expandedSignal()
        cursorShape: Qt.PointingHandCursor
    }
}
