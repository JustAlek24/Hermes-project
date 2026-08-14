import QtQuick
import QtQuick.Layouts
import Theme

RowLayout {
    id: root
    property string label: ""
    property string value: ""
    Layout.fillWidth: true
    Text {
        text: root.label 
        font.pixelSize: 18
        color: Theme.textSecondaryColor
    }
    Text { 
        Layout.fillWidth: true
        horizontalAlignment: Text.AlignRight
        
        text: root.value
        font.pixelSize: 18
        color: Theme.textSecondaryColor
    }
}