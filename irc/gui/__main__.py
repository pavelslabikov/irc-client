from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThreadPool
import sys

from irc.config import ClientConfig
from irc.gui.window import ClientWindow
from irc.gui.view import GuiView
from irc.client import Client
from irc.gui.task_runners import BackgroundTask


def start_client():
    main_window.client = client
    main_window.setup_ui()
    main_window.show()
    response_thread = BackgroundTask(client.wait_for_response)
    QThreadPool.globalInstance().start(response_thread)


if __name__ == "__main__":
    app = QApplication([])
    main_window = ClientWindow()
    config = ClientConfig.get_parser()
    client = Client(
        config["Settings"]["nickname"],
        config["Settings"]["codepage"],
        set(config["Servers"].keys()),
        GuiView(main_window),
    )
    start_client()
    ClientConfig.refresh_file(client)
    sys.exit(app.exec_())
