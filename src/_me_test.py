import os
import sys

_pyside6_dir = os.path.join(os.path.dirname(__file__), "..", ".venv", "Lib", "site-packages", "PySide6")
_pyside6_dir = os.path.normpath(_pyside6_dir)
if sys.platform == "win32" and os.path.isdir(_pyside6_dir):
    os.add_dll_directory(_pyside6_dir)

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

qml = """
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
"""
open(os.path.join(os.path.dirname(__file__), "_me_test.qml"), "w", encoding="utf-8").write(qml)

app = QApplication(sys.argv)
engine = QQmlApplicationEngine()
engine.load(QUrl.fromLocalFile(os.path.join(os.path.dirname(__file__), "_me_test.qml")))
QTimer.singleShot(600, app.quit)
app.exec()
print("LOAD STATUS:", "FAILED" if not engine.rootObjects() else "OK")
