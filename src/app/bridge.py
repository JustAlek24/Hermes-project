from PySide6.QtCore import Property, QObject, Signal, Slot

from network import get_local_ip

DEFAULT_PORT = 65432  # !!! ПОСЛЕ СОЗДАНИЯ РАБОЧЕЙ БД - УДАЛИТЬ НАХУЙ !!!


class AppBridge(QObject):
    ### Сигналы ###
    new_peer = Signal(str)  # peer_id
    status_changed = Signal(str, str)  # peer_id, status
    incoming_transfer = Signal(str, str)
    peerStatusChanged = Signal()

    ownAddressChanged = Signal()
    transfersChanged = Signal()

    # Инициализация класса
    def __init__(self, parent=None):
        super().__init__(parent)
        self._peer_status = {}

    # Метод, запускающий сигнал к QML о новом пире
    def new_peer_connected(self, name):
        self.new_peer.emit(name)

    # Слот для кнопки поиска пиров в WI-FI сети
    @Slot()
    def find_peers(self):
        print("Поиск пиров в сети...")

    # Слот для кнопки запуска проверки известных пиров
    @Slot()
    def check_status(self):
        print("Проверка статуса пиров...")

    # Слот для добавления пира в бд
    @Slot()
    def add_peer(self):
        print("Добавление пира...")

    # Слот для поиска пиров
    @Slot(str)
    def search_peers(self, query):
        print(f"Поиск: {query}")

    # Слот для отправки файла выбранному пиру
    @Slot(str, str)
    def send_file(self, peer_id, file_path):
        print(f"Отправка {file_path} пиру {peer_id}")

    # Свойство для проверки статуса пира
    @Property(dict, notify=peerStatusChanged)
    def peer_status(self):
        return self._peer_status  # dict[int, str] Словарь со статусом пиров

    # Свойство для отображения адреса пользователя
    @Property(str, notify=ownAddressChanged)
    def own_address(self):
        return f"{get_local_ip()}:{DEFAULT_PORT}"

    # Свойство для подсчёта онлайн пиров
    @Property(int, notify=peerStatusChanged)
    def online_count(self):
        return sum(1 for s in self._peer_status.values() if s == "online")

    # Свойство для отображения данных по передаче
    @Property(list, notify=transfersChanged)
    def transfers(self):
        return []

    # Метод, запускающий сигнал для обновления статуса пира в интерфейсе
    def update_peer_status(self, peer_id, status):
        self._peer_status[peer_id] = status
        self.status_changed.emit(peer_id, status)
        self._peer_status = dict(self._peer_status)
        self.peerStatusChanged.emit()
