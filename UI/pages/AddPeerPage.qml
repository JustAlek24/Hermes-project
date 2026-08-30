import QtQuick
import QtQuick.Layouts
import QtQuick.Effects
import Theme
import panels
import components

PageWithBottomPanel {
    id: root

    HeaderPanel {currentPage: "Добавить пир"}

    // Контейнер без layout-управления: внутри — карточка и её тень (anchors валидны).
    Item {
        Layout.fillHeight: true
        Layout.fillWidth: true
        Layout.margins: 20

        Rectangle {
            id: card
            anchors.fill: parent
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

                LabeledInput {
                    id: nameInput
                    label: "Имя"
                    Layout.fillWidth: true
                }
                LabeledInput {
                    id: ipInput
                    label: "IP-адрес"
                    Layout.fillWidth: true
                    input.inputMethodHints: Qt.ImhFormattedNumbersOnly
                }
                LabeledInput {
                    id: portInput
                    label: "Порт"
                    Layout.fillWidth: true
                    input.inputMethodHints: Qt.ImhDigitsOnly
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
                        enabled: nameInput.inputText !== "" && ipInput.inputText !== "" && portInput.inputText !== ""
                        normalColor: Theme.buttonPrimary
                        hoverColor: Theme.buttonPrimaryHover
                        onClicked: {
                            var ok = app.add_peer(nameInput.inputText, ipInput.inputText, portInput.inputText)
                            if (ok) {
                                nameInput.inputText = ""
                                ipInput.inputText = ""
                                portInput.inputText = ""
                                statusText.text = "Пир добавлен"
                            } else {
                                statusText.text = "Ошибка: пир уже существует или неверные данные"
                            }
                        }
                    }
                }
            }
        }

        MultiEffect {
            source: card
            anchors.fill: card
            anchors.margins: 18
            shadowEnabled: true
            shadowColor: Theme.cardShadow
            shadowBlur: 0.55
            shadowVerticalOffset: 8
            z: -1
        }
    }
}
