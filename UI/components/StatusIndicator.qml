import QtQuick
import Theme



Rectangle {
    id: statusBar
    property string status: "pending"
    property color statusColor: Theme.statusPending
    
    width: 300
    height: 200
    radius: 100
    color: statusColor

    Text {
        id: statusText
        x: 50
        y: 130
        text: "Ожидает"
        font.pixelSize: 20
        color: Theme.textColor
    }

    onStatusChanged: {
        if (status === "pending") {
            statusBar.width = 300
            statusText.text = "Ожидает"
            statusColor = Theme.statusPending
        }
        else if (status === "accepted") {
            statusBar.width = 520
            statusText.text = "Передача разрешена"
            statusColor = Theme.statusAccepted
        }
        else if (status === "done") {
            statusBar.width = 350
            statusText.text = "Завершено"
            statusColor = Theme.statusDone
        }
        else if (status === "rejected") {
            statusBar.width = 520
            statusText.text = "Передача отклонена"
            statusColor = Theme.statusRejected
        }
        else {
            statusBar.width = 300
            statusText.text = "Ошибка"
            statusColor = Theme.statusError
        }
    }
}