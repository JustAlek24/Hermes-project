import QtQuick
import QtQuick.Layouts
import Theme
import panels
import components

PageWithBottomPanel {
    HeaderPanel {currentPage: "Настройки"}

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
                text: "Настройки"
                font.pixelSize: 18
                font.bold: true
                color: Theme.textColor
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: Theme.textSecondaryColor }

            Text {
                text: "Папка загрузок: ~/Downloads"
                font.pixelSize: 14
                color: Theme.textColor
            }

            Text {
                text: "Порт по умолчанию: 65432"
                font.pixelSize: 14
                color: Theme.textColor
            }

            Text {
                text: "Размер чанка: 1 MB"
                font.pixelSize: 14
                color: Theme.textColor
            }

            Item { Layout.fillHeight: true }

            Text {
                text: "Настройки будут доступны в следующих версиях"
                font.pixelSize: 12
                color: Theme.textSecondaryColor
                Layout.alignment: Qt.AlignHCenter
            }
        }
    }
}
