import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import panels
import pages
import components
//import dialogs
import Theme

ApplicationWindow {
    id: mainWindow
    width: 1200
    height: 800
    minimumWidth: 900
    minimumHeight: 600
    visible: true
    title: "Hermes файлообменник"

    readonly property int pageIncoming: 0
    readonly property int pageViewIncoming: 1
    readonly property int pageSent: 2
    readonly property int pageSendFile: 3
    readonly property int pagePeers: 4
    readonly property int pageAboutPeer: 5
    readonly property int pageAddPeer: 6
    readonly property int pageAbout: 7
    readonly property int pageSettings: 8


    property bool leftPanelVisible: true
    property int currentScreen: 0
    property string selectedTransferId: ""
    property string selectedPeer: ""

    Rectangle { //Корень окна
        id: rootContainer
        anchors.fill: parent
        color: Theme.backgroundColor

        SideBar {id: leftPanel} // Левая панель

        StackLayout { // Правая панель
            id: rightPanel
            anchors.left: leftPanel.right
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom

            currentIndex: currentScreen

            IncomingPage {} //Входящие
            ViewIncomingPage {} //Посмотреть входящее сообщение
            SentPage {} //Отправленные
            SendFilePage {} //Отправить
            PeersPage {} //Пиры
            AboutPeerPage {} //Страница пира
            AddPeerPage {} // Добавить пир
            AboutPage {} //О программе
            SettingsPage {} //Настройки
        }

        NotificationBanner {
            id: notification
            selectedTransferId: mainWindow.selectedTransferId

            function currentTransferName(transferId) {
                for (var t of app.transfers) {
                    if (t.transfer_id === transferId) {
                        return t.peer_name
                    }
                }
                return ""
            }

            onViewed: function(transferId) {
                // Явно пишем в корневое свойство окна. Нельзя просто
                // `selectedTransferId = ...`: у NotificationBanner есть собственное
                // свойство selectedTransferId (для автозакрытия), оно перекрывает
                // корневое (shadowing), из-за чего страница не обновлялась.
                mainWindow.selectedTransferId = transferId
                currentScreen = pageViewIncoming
                notification.hide()
            }
            onDismissed: notification.hide()
        }

        Connections {
            target: app
            function onIncomingTransfer(transferId) {
                notification.show(
                    "Пир " + notification.currentTransferName(transferId) + " хочет передать файл",
                    transferId
                )
            }
        }
    }
}
