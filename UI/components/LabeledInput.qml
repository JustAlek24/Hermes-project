import QtQuick
import QtQuick.Layouts
import Theme

// Переиспользуемое поле ввода с подписью: ColumnLayout { Подпись; Поле-редактор }
ColumnLayout {
    id: root
    property string label: ""
    property alias inputText: textField.text
    property alias input: textField
    spacing: 5

    Text {
        text: root.label
        color: Theme.textColor
        font.pixelSize: 14
        visible: root.label !== ""
    }

    Rectangle {
        Layout.fillWidth: true
        height: 40
        radius: 6
        color: Theme.secondaryColor

        border.color: textField.activeFocus ? Theme.accentColor : "transparent"
        border.width: textField.activeFocus ? 2 : 0

        Behavior on border.color {
            ColorAnimation { duration: 200 }
        }

        TextInput {
            id: textField
            anchors.fill: parent
            anchors.margins: 10
            color: Theme.textColor
            font.pixelSize: 14
            clip: true
            selectByMouse: true
        }
    }
}
