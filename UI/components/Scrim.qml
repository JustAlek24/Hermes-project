import QtQuick


Rectangle {
    id: scrim

    property bool active: false    

    anchors.fill: parent
    z: 1
    color: "#80000000"
    signal closed
    
    opacity: active ? 1 : 0
    visible: active
    
    Behavior on opacity {
        NumberAnimation { duration: 300 }
    }

    MouseArea {
        anchors.fill: parent
        onClicked: scrim.closed()
    }
}