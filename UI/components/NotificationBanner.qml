import QtQuick
import QtQuick.Layouts
import Theme
import components

Rectangle {
    id: banner

    property string message: ""
    property string transferId: ""
    // Отслеживается главным окном: при открытии передачи, за которую
    // отвечает уведомление, банер закрывается сам.
    property string selectedTransferId: ""
    signal viewed(string transferId)
    signal dismissed()

    onSelectedTransferIdChanged: {
        if (selectedTransferId && visible && selectedTransferId === transferId) {
            hide()
        }
    }

    width: 340
    height: 80
    radius: 12
    color: Theme.leftPanelColor
    visible: false

    border.color: Theme.textSecondaryColor
    border.width: 1

    // Позиция: банер прижат к правому верхнему углу родителя.
    // shiftX — сдвиг вправо: при 0 банер виден, при = ширине уезжает за правый край.
    property real shiftX: banner.width

    x: parent ? parent.width - banner.width - 20 + shiftX : 0
    y: 20
    z: 100

    opacity: 0

    Behavior on shiftX {
        NumberAnimation {
            duration: 350
            easing.type: Easing.OutCubic
        }
    }
    Behavior on opacity {
        NumberAnimation {
            duration: 300
        }
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 12

        Rectangle {
            Layout.preferredWidth: 6
            Layout.preferredHeight: parent.height - 28
            Layout.alignment: Qt.AlignVCenter
            radius: 3
            color: Theme.accentColor
        }

        Text {
            id: msgText
            text: banner.message
            Layout.fillWidth: true
            Layout.fillHeight: true
            verticalAlignment: Text.AlignVCenter
            wrapMode: Text.WordWrap
            elide: Text.ElideRight
            color: Theme.textColor
            font.pixelSize: 14
        }

        UniversalButton {
            id: viewBtn
            text: "Посмотреть"
            visible: banner.transferId !== ""
            Layout.preferredWidth: 120
            Layout.fillWidth: false
            normalColor: Theme.buttonPrimary
            hoverColor: Theme.buttonPrimaryHover
            onClicked: {
                banner.viewed(banner.transferId)
            }
        }

        Rectangle {
            id: closeBtn
            Layout.preferredWidth: 24
            Layout.preferredHeight: 24
            Layout.alignment: Qt.AlignVCenter
            radius: 12
            color: closeMouse.containsMouse ? Theme.accentColor : "transparent"

            Text {
                anchors.centerIn: parent
                text: "✕"
                color: Theme.textColor
                font.pixelSize: 14
            }
            MouseArea {
                id: closeMouse
                anchors.fill: parent
                hoverEnabled: true
                onClicked: banner.dismissed()
                cursorShape: Qt.PointingHandCursor
            }
        }
    }

    // Показ уведомления (перезапускает анимацию)
    function show(text, id) {
        banner.message = text
        banner.transferId = (id === undefined || id === null) ? "" : id
        banner.visible = true
        banner.opacity = 1
        banner.shiftX = 0
        // Обычные информационные уведомления (без передачи) прячем сами через 5 сек
        if (!id || id === "") {
            autoHideTimer.start()
        } else {
            autoHideTimer.stop()
        }
    }

    // Скрытие с анимацией уезжания вправо за экран
    function hide() {
        banner.shiftX = banner.width + 40
        banner.opacity = 0
        hideTimer.start()
    }

    Timer {
        id: hideTimer
        interval: 400
        repeat: false
        onTriggered: {
            banner.visible = false
        }
    }

    Timer {
        id: autoHideTimer
        interval: 5000
        repeat: false
        onTriggered: {
            banner.hide()
        }
    }
}
