function formatSize(bytes) {
    if (bytes === null) return "-"
    return (bytes / 1048576).toFixed(1) + " МБ"
}

function formatDate(sec) {
    if (sec === null) return "-"
    return new Date(sec * 1000).toLocaleString()
}

function formatRelative(sec) {
    if (sec === null || sec === 0) return "никогда"
    var now = Math.floor(Date.now() / 1000)
    var diff = Math.max(0, now - sec)
    if (diff < 60) return "только что"
    if (diff < 3600) return Math.floor(diff / 60) + " мин назад"
    if (diff < 86400) return Math.floor(diff / 3600) + " ч назад"
    return Math.floor(diff / 86400) + " дн назад"
}

// Общий helper для сборки ListModel из массива объектов (clear + append).
// Используется в PeersPage / IncomingPage / SentPage / BottomPanel.
function fillListModel(model, items) {
    model.clear()
    for (var i = 0; i < items.length; i++) {
        model.append(items[i])
    }
}