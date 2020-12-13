from PyQt5.QtWidgets import QApplication
import sys
from irc.gui.mydesign import ClientWindow
from irc.client import Client

if __name__ == "__main__":
    app = QApplication([])
    client = Client("Pashka", "cp866", set())
    main_window = ClientWindow(client)
    main_window.setup_ui()
    main_window.show()
    sys.exit(app.exec())
