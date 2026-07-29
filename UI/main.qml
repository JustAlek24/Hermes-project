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

    readonly property int pageIncoming: 0
    readonly property int pageViewIncoming: 1
    readonly property int pageSent: 2
    readonly property int pageSendFile: 3
    readonly property int pagePeers: 4
    readonly property int pageAddPeer: 5
    readonly property int pageAbout: 6
    readonly property int pageSettings: 7


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
            color: Theme.leftPanelColor
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
                    Layout.alignment: Qt.AlignHCenter
                    
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
                        currentScreen = pageIncoming
                    }
                }

                SidePanelButton {
                    Layout.fillWidth: true
                    collapsed: !leftPanelVisible
                    text: "Отправленные"
                    icon: "icons/sent_icon.png"
                    onClicked: {
                        currentScreen = pageSent
                    }
                }

                SidePanelButton {
                    Layout.fillWidth: true
                    collapsed: !leftPanelVisible
                    text: "Пиры"
                    icon: "icons/peer_icon.png"
                    onClicked: {
                        currentScreen = pagePeers
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
                        currentScreen = pageSettings
                    }
                }

                SidePanelButton {
                    collapsed: !leftPanelVisible
                    Layout.fillWidth: true
                    text: "О программе"
                    icon: "icons/about_icon.png"
                    onClicked: {
                        currentScreen = pageAbout
                    }
                }
            }
        }

        StackLayout { //Верхняя панель
            anchors.left: leftPanel.right
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom

            currentIndex: currentScreen

            IncomingPage {} //Входящие
            ViewIncomingPage {} //Посмотреть входящее сообщение
            SentPage {} //Отправленные
            SendFilePage {} //Отправить
            PeersPage {} //Пиры
            AddPeerPage {} // Добавить пир
            AboutPage {} //О программе
            SettingsPage {} //Настройки
        }
    }
}
