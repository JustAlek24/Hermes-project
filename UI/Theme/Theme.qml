pragma Singleton
import QtQuick

QtObject {
    // === ВАШИ ЦВЕТА (сохранены, но переосмыслены) ===
    readonly property color mainTopleftPanelColor: '#a9d5ff'      // Шапки, заголовки
    readonly property color secondaryColor: '#a9aaff'            // Вторичные элементы
    readonly property color backgroundColor: '#e1f0ff'           // Основной фон страниц
    readonly property color leftPanelColor: '#e1e1ff'            // Боковые панели
    readonly property color textColor: '#00014c'                 // Основной текст
    readonly property color textSecondaryColor: '#00274c'        // Второстепенный текст
    readonly property color accentColor: '#9ea1ff'              // Акцентные элементы
    readonly property color tableColor: '#2148da'               // Таблицы, выделение
    
    // === НОВЫЕ ЦВЕТА (для завершённости) ===
    readonly property color cardBackground: '#ffffff'            // Фон карточек (белый)
    readonly property color cardShadow: '#00000020'             // Тень карточек (прозрачность)
    readonly property color divider: '#d0d8ff'                 // Разделители
    
    // === СТАТУСЫ ===
    
    readonly property color statusPending: '#ffb74d'           // Оранжевый (ожидает)
    readonly property color statusAccepted: '#9effa3'          // Зелёный (разрешён)
    readonly property color statusDone: '#66bb6a'              // Зелёный (получен)
    readonly property color statusRejected: '#ef5350'          // Красный (отклонён)
    readonly property color statusError: '#ff0000'             // Серый (ошибка)
    
    // === КНОПКИ ===
    readonly property color buttonPrimary: '#4fe4ff'           // Синяя (принять)
    readonly property color buttonPrimaryHover: '#2fdca2'      // При наведении
    readonly property color buttonSecondary: '#e8ecf8'         // Серая (отклонить)
    readonly property color buttonSecondaryHover: '#fbd0d0'    // При наведении
    
    // === ГРАДИЕНТЫ (для шапок) ===
    readonly property var headerGradient: {
        return {
            type: "linear",
            x1: 0, y1: 0, x2: 1, y2: 0,
            stops: [
                { position: 0, color: '#a9d5ff' },
                { position: 1, color: '#e1e1ff' }
            ]
        }
    }
}