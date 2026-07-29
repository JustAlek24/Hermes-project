import QtQuick
import QtQuick.Layouts
import Theme

Rectangle { //Верхняя панель
    id: topPanel
    Layout.fillWidth: true
    height: 80
    color: Theme.mainTopleftPanelColor

    property string currentPage: currentPage

    RowLayout {
        anchors.fill: parent
        spacing: 16
        Rectangle { //Кнопка меню
            id: leftButton 
        
            width: 48
            height: 48
            Layout.leftMargin: 16
            radius: 8

            color: menuMouseArea.containsMouse ? Theme.accentColor : "transparent"

            Behavior on color {
                ColorAnimation {
                    duration: 300
                }
            }
            
            Text {
                anchors.centerIn: parent
                anchors.leftMargin: 16
                
                text: "☰"
                font.pixelSize: 28
                color: Theme.textColor
            }
            MouseArea {
                id: menuMouseArea
                anchors.fill: parent
                hoverEnabled: true
                onClicked: leftPanelVisible = !leftPanelVisible
                cursorShape: Qt.PointingHandCursor
            }
        }
        Rectangle { // Заголовок страницы
            Layout.fillWidth: true
            Text {
                anchors.centerIn: parent
                text: currentPage
                font.pixelSize: 22
                font.bold: true
                color: Theme.textColor 
            }
        }
    }
}