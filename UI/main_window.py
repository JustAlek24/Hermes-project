import sys
import os

_pyside6_dir = os.path.join(os.path.dirname(__file__), "..", ".venv", "Lib", "site-packages", "PySide6")
_pyside6_dir = os.path.normpath(_pyside6_dir)
if sys.platform == "win32" and os.path.isdir(_pyside6_dir):
    os.add_dll_directory(_pyside6_dir)

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

def main():
    """Запуск UI"""
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(_root)
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
    app = QGuiApplication(sys.argv)

    engine = QQmlApplicationEngine()

    qml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.qml")
    engine.load(QUrl.fromLocalFile(os.path.abspath(qml_path)))

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
