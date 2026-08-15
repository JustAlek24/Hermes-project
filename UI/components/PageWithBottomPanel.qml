import QtQuick
import QtQuick.Layouts
import panels

Item {
    id: root
    property bool statusBarExpanded: false

    default property alias content: contentArea.data
    
    ColumnLayout {
        id: contentArea
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: bottomPanel.top
        spacing: 0
    }

    Scrim {
        anchors.fill: parent
        active: root.statusBarExpanded
        onClosed: root.statusBarExpanded = false
    }

    BottomPanel {
        id: bottomPanel
        z: 2
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        expanded: root.statusBarExpanded
        onExpandedSignal: root.statusBarExpanded = !root.statusBarExpanded
    }
}
