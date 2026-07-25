import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: mainWindow
    width: 1200
    height: 800
    minimumWidth: 800
    minimumHeight: 400
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
            width: leftPanelVisible ? 250 : 70
            height: parent.height
            color: panelColor
            z: 10
            clip: true

            Behavior on width {
                NumberAnimation {
                    duration: 300
                    easing.type: Easing.InOutQuad
                }
            }

            opacity: 1

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 10

                Rectangle {
                    height: 60
                    anchors.horizontalCenter: parent.horizontalCenter
                    
                    Text {
                        y: 10
                        text: leftPanelVisible ? "Hermes project" : " "
                        font.pixelSize: 24
                        font.bold: true
                        color: textColor
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
                        currentScreen = "main"
                    }
                }

                SidePanelButton {
                    Layout.fillWidth: true
                    collapsed: !leftPanelVisible
                    text: "Отправленные"
                    icon: "icons/sent_icon.png"
                    onClicked: {
                        currentScreen = "sent"
                    }
                }

                SidePanelButton {
                    Layout.fillWidth: true
                    collapsed: !leftPanelVisible
                    text: "Пиры"
                    icon: "icons/peer_icon.png"
                    onClicked: {
                        currentScreen = "peers"
                    }
                }

                Item {
                    Layout.fillHeight:true
                }

                SidePanelButton {
                    id: settingsButton
                    collapsed: !leftPanelVisible
                    width: parent.width
                    text: "Настройки"
                    icon: "icons/settings_icon.png"
                    onClicked: {
                        currentScreen = "settings"
                    }
                }

                SidePanelButton {
                    collapsed: !leftPanelVisible
                    width: parent.width
                    text: "О программе"
                    icon: "icons/about_icon.png"
                    onClicked: {
                        currentScreen = "about"
                    }
                }
            }
        }

        Column {
            id: mainPanel
            anchors.left: leftPanel.right
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            spacing: 0

            Rectangle { //Верхняя панель
                id: topPanel
                width: parent.width
                height: 80
                color: primaryColor

                Row {
                    anchors.fill: parent
                    spacing: 16
                    leftPadding: 16
                    rightPadding: 16

                    Rectangle { //Кнопка меню
                        width: 48
                        height: 48
                        anchors.verticalCenter: parent.verticalCenter
                        radius: 8
                        color: menuMouseArea.containsMouse ? Qt.rgba(1,1,1,0.2) : "transparent"

                        Text {
                            anchors.centerIn: parent
                            text: "☰"
                            font.pixelSize: 28
                            color: textColor
                        }
                        MouseArea {
                            id: menuMouseArea
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: leftPanelVisible = !leftPanelVisible
                            cursorShape: Qt.PointingHandCursor
                        }
                    }

                    Rectangle { // Кнопка отправить
                        width: 220
                        height: parent.height
                        radius: 8
                        color: sendMouseArea.containsMouse ? Qt.rgba(1,1,1,0.2) : "transparent"

                        Row {
                            anchors.left: parent.left
                            anchors.leftMargin: 15
                            anchors.right: parent.right
                            anchors.rightMargin: 15
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 10

                            Image {
                                source: "icons/send_icon.png"
                                width: 24
                                height: 24
                                anchors.verticalCenter: parent.verticalCenter
                                fillMode: Image.PreserveAspectFit
                            }
                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                text: "Отправить"
                                font.pixelSize: 22
                                font.bold: true
                                color: textColor
                            }
                        }

                        MouseArea {
                            id: sendMouseArea
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: currentScreen = "send"
                            cursorShape: Qt.PointingHandCursor
                        }
                    }
                }
            }
        }
    }
}
