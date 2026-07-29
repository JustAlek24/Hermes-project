import QtQuick
import QtQuick.Layouts
//import QtQuick.Controls
import Theme
import components

Rectangle { //Левая панель целиком
    //id: leftPanel
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
            icon: "../icons/incoming_icon.png"
            onClicked: {
                currentScreen = pageIncoming
            }
        }
        SidePanelButton {
            Layout.fillWidth: true
            collapsed: !leftPanelVisible
            text: "Отправленные"
            icon: "../icons/sent_icon.png"
            onClicked: {
                currentScreen = pageSent
            }
        }
        SidePanelButton {
            Layout.fillWidth: true
            collapsed: !leftPanelVisible
            text: "Пиры"
            icon: "../icons/peer_icon.png"
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
            icon: "../icons/settings_icon.png"
            onClicked: {
                currentScreen = pageSettings
            }
        }
        SidePanelButton {
            collapsed: !leftPanelVisible
            Layout.fillWidth: true
            text: "О программе"
            icon: "../icons/about_icon.png"
            onClicked: {
                currentScreen = pageAbout
            }
        }
    }
}