
import QtQuick
import QtQuick.Effects

Rectangle {
    width: 300; height: 200
    Rectangle {
        id: card
        x: 50; y: 40; width: 200; height: 100
        radius: 8
        color: "#ffffff"
    }
    MultiEffect {
        source: card
        anchors.fill: card
        shadowEnabled: true
        shadowColor: "#000000"
        shadowBlur: 0.6
        shadowVerticalOffset: 6
    }
}
