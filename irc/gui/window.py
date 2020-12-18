import os

from PyQt5 import QtWidgets, QtGui, QtCore
from irc.client import Client
from irc.config import ClientConfig
from irc.gui.task_runners import BackgroundTask

RESOURCE_PATH = "resources"


class ClientWindow(QtWidgets.QMainWindow):
    print_signal = QtCore.pyqtSignal(str)
    print_channel_signal = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.central_widget = QtWidgets.QWidget(self)
        self.send_button = QtWidgets.QPushButton(self.central_widget)
        self.input_line = QtWidgets.QLineEdit(self.central_widget)
        self.tabs_panel = QtWidgets.QTabWidget(self.central_widget)
        self._client = None
        self.print_signal.connect(self.print_chat_text)
        self.print_channel_signal.connect(self.print_channel)

    def setup_ui(self):
        self.setObjectName("main_window")
        self.setWindowTitle("IRC Client")
        self.resize(800, 600)
        path_to_icon = os.path.join(RESOURCE_PATH, "icon.png")
        self.setWindowIcon(QtGui.QIcon(path_to_icon))
        self.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.setCentralWidget(self.central_widget)

        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)

        self.send_button.setFont(font)
        self.send_button.setObjectName("send_button")
        self.send_button.setText("Отправить")
        self.send_button.setShortcut("Return")
        self.send_button.clicked.connect(self.send_user_input)

        grid_layout = QtWidgets.QGridLayout(self.central_widget)
        grid_layout.addWidget(self.send_button, 1, 0, 1, 1)
        grid_layout.addWidget(self.input_line, 1, 1, 1, 1)
        grid_layout.addWidget(self.tabs_panel, 0, 0, 1, 2)

        self.add_new_tab("Client")
        self.tabs_panel.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(self)

    @property
    def client(self):
        return self._client

    @client.setter
    def client(self, client: Client):
        if self._client is None:
            self._client = client

    @property
    def current_chat(self):
        return self.tabs_panel.currentWidget().findChild(
            QtWidgets.QWidget, "chat_content"
        )

    def send_user_input(self):
        text = self.input_line.text()
        if text.strip():
            input_text = f"<{self.client.nickname}>: {text}"
            self.current_chat.layout().insertWidget(
                0, QtWidgets.QLabel(input_text)
            )
            self.input_line.clear()
            thread = BackgroundTask(self.client.process_user_input, text)
            QtCore.QThreadPool.globalInstance().start(thread)

    def print_chat_text(self, text: str):
        self.current_chat.layout().insertWidget(0, QtWidgets.QLabel(text))

    def print_channel(self, channel: str):
        table = self.tabs_panel.currentWidget().findChild(
            QtWidgets.QWidget, "user_content"
        )
        table.layout().addWidget(QtWidgets.QLabel(channel))

    def add_new_tab(self, name: str):
        tab_to_add = ClientTab()
        self.tabs_panel.addTab(tab_to_add, name)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.client.exit_client()
        QtCore.QThreadPool.globalInstance().clear()
        ClientConfig.refresh_file(self.client)
        event.accept()


class ClientTab(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        vertical_layout = QtWidgets.QVBoxLayout()
        self.setLayout(vertical_layout)
        self.content_layout = QtWidgets.QHBoxLayout()
        vertical_layout.addLayout(self.content_layout)
        self.user_area = QtWidgets.QScrollArea(self)
        self.chat_area = QtWidgets.QScrollArea(self)
        self.chat_area.setWidgetResizable(True)
        self.user_area.setWidgetResizable(True)
        self.user_content = QtWidgets.QWidget()
        self.chat_content = QtWidgets.QWidget()
        self.user_area.setWidget(self.user_content)
        self.chat_area.setWidget(self.chat_content)
        self.set_up_areas()

    def set_up_areas(self):
        self.content_layout.addWidget(self.user_area)
        self.content_layout.addWidget(self.chat_area)
        self.content_layout.setSpacing(10)

        self.user_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

        users_layout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.TopToBottom)
        users_layout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        self.user_content.setLayout(users_layout)
        self.user_content.setObjectName("user_content")

        size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )
        size_policy.setHorizontalStretch(1)

        self.user_area.setSizePolicy(size_policy)

        self.chat_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.chat_area.verticalScrollBar().rangeChanged.connect(self.move_bar)

        chat_layout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.BottomToTop)
        chat_layout.setAlignment(QtCore.Qt.AlignBottom | QtCore.Qt.AlignLeft)
        self.chat_content.setLayout(chat_layout)
        self.chat_content.setObjectName("chat_content")

        size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )
        size_policy.setHorizontalStretch(4)
        self.chat_area.setSizePolicy(size_policy)

    def move_bar(self, min_n: int, max_n: int):
        scroll_bar = self.sender()
        if not scroll_bar.isSliderDown():
            scroll_bar.setValue(max_n)
