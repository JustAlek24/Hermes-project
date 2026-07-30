from PySide6.QtCore import QObject, Slot, Signal

class AppBridge(QObject):

    new_peer = Signal(str, str)         # peer_ip, peer_id
    status_changed = Signal(str, str)   # peer_id, status
    incoming_transfer = Signal(str, str)
    

    def __init__(self, parent=None):
        super().__init__(parent)

    def new_peer_connected(self, name):
        self.new_peer.emit(name)

    @Slot()
    def find_peers(self):
        print("Поиск пиров в сети...")

    @Slot()
    def check_status(self):
        print("Проверка статуса пиров...")

    @Slot()
    def add_peer(self):
        print("Добавление пира...")

    @Slot(str)
    def search_peers(self, query):
        print(f"Поиск: {query}")

    @Slot(str, str)
    def send_file(self, peer_id, file_path):
        print(f"Отправка {file_path} пиру {peer_id}")