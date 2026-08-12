import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import panels
import pages
//import dialogs
import Theme

ApplicationWindow {
    id: mainWindow
    width: 1200
    height: 800
    minimumWidth: 900
    minimumHeight: 400
    visible: true
    title: "Hermes файлообменник"

    readonly property int pageIncoming: 0
    readonly property int pageViewIncoming: 1
    readonly property int pageSent: 2
    readonly property int pageSendFile: 3
    readonly property int pagePeers: 4
    readonly property int pageAddPeer: 5
    readonly property int pageAbout: 6
    readonly property int pageSettings: 7


    property bool leftPanelVisible: true
    property int currentScreen: 0
    property string selectedTransferId: ""

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
            AddPeerPage {} // Добавить пир
            AboutPage {} //О программе
            SettingsPage {} //Настройки
        }
    }
}
