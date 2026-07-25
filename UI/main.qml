import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Theme

ApplicationWindow {
    id: mainWindow
    width: 1200
    height: 800
    minimumWidth: 800
    minimumHeight: 400
    visible: true
    title: "Hermes файлообменник"

    property bool leftPanelVisible: true
    property int currentScreen: 0

    Rectangle { //Корень окна
        id: rootContainer
        anchors.fill: parent
        color: Theme.backgroundColor

        Rectangle { //Левая панель целиком
            id: leftPanel
            width: leftPanelVisible ? 250 : 70
            height: parent.height
            color: Theme.panelColor
            z: 10
            clip: true

            Behavior on width {
                NumberAnimation {
                    duration: 300
                    easing.type: Easing.InOutQuad
                }
            }

            opacity: 1

            ColumnLayout { //Колонка содержания левой панели
                anchors.fill: parent
                anchors.margins: 12
                spacing: 10

                Rectangle { //Верхний текст
                    height: 60
                    anchors.horizontalCenter: parent.horizontalCenter
                    
                    Text {
                        y: 10
                        text: leftPanelVisible ? "Hermes Project" : "H P"
                        font.pixelSize: 24
                        font.bold: true
                        color: Theme.textColor
                        anchors.horizontalCenter: parent.horizontalCenter
                        elide: Text.ElideRight
                    }
                }

                SidePanelButton {
                    Layout.fillWidth: true
                    collapsed: !leftPanelVisible
                    text: "Входящие"
                    icon: "icons/incoming_icon.png"
                    onClicked: {
                        currentScreen = 0
                    }
                }

                SidePanelButton {
                    Layout.fillWidth: true
                    collapsed: !leftPanelVisible
                    text: "Отправленные"
                    icon: "icons/sent_icon.png"
                    onClicked: {
                        currentScreen = 1
                    }
                }

                SidePanelButton {
                    Layout.fillWidth: true
                    collapsed: !leftPanelVisible
                    text: "Пиры"
                    icon: "icons/peer_icon.png"
                    onClicked: {
                        currentScreen = 3
                    }
                }

                Item {
                    Layout.fillHeight:true
                }

                SidePanelButton {
                    id: settingsButton
                    collapsed: !leftPanelVisible
                    Layout.fillWidth: true
                    text: "Настройки"
                    icon: "icons/settings_icon.png"
                    onClicked: {
                        currentScreen = 6
                    }
                }

                SidePanelButton {
                    collapsed: !leftPanelVisible
                    Layout.fillWidth: true
                    text: "О программе"
                    icon: "icons/about_icon.png"
                    onClicked: {
                        currentScreen = 5
                    }
                }
            }
        }

        Column { //Главная панель
            id: mainPanel
            anchors.left: leftPanel.right
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom

            StackLayout { //Верхняя панель
                anchors.fill: parent

                currentIndex: currentScreen

                IncomingPage {} //Входящие

                SentPage {} //Отправленные

                SendPage {} //Отправить
                
                PeersPage {} //Пиры

                AddPeerPage {} // Добавить пир

                AboutPage {} //О программе

                SettingsPage {} //Настройки
            }
        }
    }
}
