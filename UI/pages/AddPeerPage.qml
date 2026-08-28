import QtQuick
import QtQuick.Layouts
import Theme
import panels
import components

PageWithBottomPanel {
    id: root

    HeaderPanel {currentPage: "Добавить пир"}

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
                text: "Добавление нового пира"
                font.pixelSize: 18
                font.bold: true
                color: Theme.textColor
            }

            ColumnLayout {
                spacing: 5
                Text { text: "Имя"; color: Theme.textColor; font.pixelSize: 14 }
                Rectangle {
                    Layout.fillWidth: true
                    height: 40
                    radius: 6
                    color: Theme.secondaryColor
                    TextInput {
                        id: nameInput
                        anchors.fill: parent
                        anchors.margins: 10
                        color: Theme.textColor
                        font.pixelSize: 14
                        clip: true
                    }
                }
            }

            ColumnLayout {
                spacing: 5
                Text { text: "IP-адрес"; color: Theme.textColor; font.pixelSize: 14 }
                Rectangle {
                    Layout.fillWidth: true
                    height: 40
                    radius: 6
                    color: Theme.secondaryColor
                    TextInput {
                        id: ipInput
                        anchors.fill: parent
                        anchors.margins: 10
                        color: Theme.textColor
                        font.pixelSize: 14
                        clip: true
                        inputMethodHints: Qt.ImhFormattedNumbersOnly
                    }
                }
            }

            ColumnLayout {
                spacing: 5
                Text { text: "Порт"; color: Theme.textColor; font.pixelSize: 14 }
                Rectangle {
                    Layout.fillWidth: true
                    height: 40
                    radius: 6
                    color: Theme.secondaryColor
                    TextInput {
                        id: portInput
                        anchors.fill: parent
                        anchors.margins: 10
                        color: Theme.textColor
                        font.pixelSize: 14
                        clip: true
                        inputMethodHints: Qt.ImhDigitsOnly
                    }
                }
            }

            Text {
                id: statusText
                text: ""
                color: statusText.text.indexOf("Ошибка") >= 0 ? Theme.statusError : Theme.statusDone
                font.pixelSize: 13
                visible: text !== ""
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
                    text: "Добавить"
                    enabled: nameInput.text !== "" && ipInput.text !== "" && portInput.text !== ""
                    normalColor: Theme.buttonPrimary
                    hoverColor: Theme.buttonPrimaryHover
                    onClicked: {
                        var ok = app.add_peer(nameInput.text, ipInput.text, portInput.text)
                        if (ok) {
                            nameInput.text = ""
                            ipInput.text = ""
                            portInput.text = ""
                            statusText.text = "Пир добавлен"
                        } else {
                            statusText.text = "Ошибка: пир уже существует или неверные данные"
                        }
                    }
                }
            }
        }
    }
}
