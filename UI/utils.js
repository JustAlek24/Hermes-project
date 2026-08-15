function formatSize(bytes) {
    if (bytes === null) return "-"
    return (bytes / 1048576).toFixed(1) + " МБ"
}

function formatDate(sec) {
    if (sec === null) return "-"
    return new Date(sec * 1000).toLocaleString()
}