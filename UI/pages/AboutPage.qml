import QtQuick
import QtQuick.Layouts
import Theme
import panels
import components

PageWithBottomPanel {
    HeaderPanel {currentPage: "О программе"}

    Rectangle {
        Layout.fillHeight: true
        Layout.fillWidth: true
        Layout.margins: 20
        radius: 10
        color: Theme.cardBackground

        ColumnLayout {
            anchors.centerIn: parent
            spacing: 15

            Text {
                text: "Hermes"
                font.pixelSize: 28
                font.bold: true
                color: Theme.textColor
                Layout.alignment: Qt.AlignHCenter
            }

            Text {
                text: "v0.1.0"
                font.pixelSize: 14
                color: Theme.textSecondaryColor
                Layout.alignment: Qt.AlignHCenter
            }

            Text {
                text: "P2P файлообменник"
                font.pixelSize: 16
                color: Theme.textColor
                Layout.alignment: Qt.AlignHCenter
            }

            Text {
                text: "Пир-to-пир передача файлов\nбез централизованного сервера"
                font.pixelSize: 13
                color: Theme.textSecondaryColor
                horizontalAlignment: Text.AlignHCenter
                Layout.alignment: Qt.AlignHCenter
            }
        }
    }
}
