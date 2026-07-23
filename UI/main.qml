import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: mainWindow
    width: 1200
    height: 800
    visible: true
    title: "Hermes файлообменник"

    readonly property color primaryColor: '#a9d5ff'
    readonly property color secondaryColor: '#a9aaff'
    readonly property color backgroundColor: '#e1f0ff'
    readonly property color panelColor: '#e1e1ff'
    readonly property color textColor: '#00014c'
    readonly property color textSecondaryColor: '#00274c'
    readonly property color accentColor: '#9fa0fe'

    property bool leftPanelVisible: true
    property string currentScreen: "main"

    Rectangle {
        id: rootContainer
        anchors.fill: parent
        color: backgroundColor

        Rectangle {
            id: leftPanel
            width: leftPanelVisible ? 250 : 0
            height: parent.height
            x: leftPanelVisible ? 0 : -width
            color: panelColor
            z: 10
            clip: true

            Behavior on x {
                NumberAnimation {
                    duration: 300
                    easing.type: Easing.InOutQuad
                }
            }

            Behavior on width {
                NumberAnimation {
                    duration: 300
                    easing.type: Easing.InOutQuad
                }
            }

            opacity: leftPanelVisible ? 1 : 0

            Behavior on opacity {
                NumberAnimation {
                    duration: 200
                }
            }

            Column {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 15

                Text {
                    text: "Меню"
                    font.pixelSize: 24
                    font.bold: true
                    color: textColor
                    anchors.horizontalCenter: parent.horizontalCenter
                    elide: Text.ElideRight
                }

                SidePanelButton {
                    width: parent.width
                    text: "Входящие"
                    icon: "icons/sent_icon.png"
                    onClicked: {
                        currentScreen = "main"
                    }
                }

                SidePanelButton {
                    width: parent.width
                    text: "Отправленные"
                    icon: "icons/incoming_icon.png"
                    onClicked: {
                        currentScreen = "sent"
                    }
                }

                SidePanelButton {
                    width: parent.width
                    text: "Пиры"
                    icon: "icons/peer_icon.png"
                    onClicked: {
                        currentScreen = "peers"
                    }
                }
            }

            Column{
                anchors.fill: parent
                anchors.margins: 20
                anchors.bottom: parent.bottom
                spacing: 15

                SidePanelButton {
                    id: settingsButton
                    anchors.bottom: parent.bottom
                    width: parent.width

                    text: "Настройки"
                    icon: "icons/settings_icon.png"
                    onClicked: {
                        currentScreen = "settings"
                    }
                }

                SidePanelButton {
                    anchors.bottom: settingsButton.top
                    anchors.bottomMargin: 15
                    width: parent.width
                    text: "О программе"
                    icon: "icons/about_icon.png"
                    onClicked: {
                        currentScreen = "about"
                    }
                }
            }
        }
    }
}
