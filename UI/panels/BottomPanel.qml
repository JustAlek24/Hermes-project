import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import Theme

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

    Column {

        anchors.fill: parent

        RowLayout {
            Text {
                Layout.leftMargin: 20
                Layout.alignment: Qt.AlignVCenter
                text: "Внутренний IP: " + app.own_address
                font.pixelSize: 14
            }
            Text {
                Layout.leftMargin: 20
                Layout.alignment: Qt.AlignVCenter
                
                text: "Онлайн: " + app.online_count
                font.pixelSize: 14

            }

            ProgressBar {
                id: activeProgress
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignVCenter
                Layout.rightMargin: 15
                visible: app.transfers.length > 0
                value: {
                    var progress = app.transfer_progress
                    var keys = Object.keys(progress)
                    if (keys.length > 0)
                        return progress[keys[0]] / 100
                    return 0
                }
            }
            Text {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignVCenter
                Layout.leftMargin: 20
                horizontalAlignment: Text.AlignRight
                visible: app.transfers.length == 0
                text: "Приёма/передачи файлов не происходит"
                font.pixelSize: 14
            }
        }

    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        visible: !expanded
        hoverEnabled: true
        onClicked: expandedSignal()
        cursorShape: Qt.PointingHandCursor
    }
}
