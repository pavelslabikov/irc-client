from PyQt5 import QtCore, QtGui, QtWidgets
from irc.client import Client


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

        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        size_policy.setHorizontalStretch(1)

        self.user_area.setSizePolicy(size_policy)

        self.chat_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.chat_area.verticalScrollBar().rangeChanged.connect(self.move_bar)

        chat_layout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.BottomToTop)
        chat_layout.setAlignment(QtCore.Qt.AlignBottom | QtCore.Qt.AlignLeft)

        self.chat_content.setLayout(chat_layout)
        self.chat_content.setObjectName("chat_content")

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(4)

        self.chat_area.setSizePolicy(sizePolicy)

    def move_bar(self, min_n: int, max_n: int):
        scroll_bar = self.sender()
        if not scroll_bar.isSliderDown():
            scroll_bar.setValue(max_n)

    def append_to_chat(self, text: QtWidgets.QLabel):
        self.chat_content.layout().insertWidget(0, text)

    def append_to_users(self, nickname: QtWidgets.QLabel):
        self.user_content.layout().addWidget(nickname)


class ClientWindow(QtWidgets.QMainWindow):
    def __init__(self, client: Client):
        super().__init__()
        self.client = client
        self.central_widget = QtWidgets.QWidget(self)
        self.send_button = QtWidgets.QPushButton(self.central_widget)
        self.input_line = QtWidgets.QLineEdit(self.central_widget)
        self.tabs_panel = QtWidgets.QTabWidget(self.central_widget)
        self.menu_bar = QtWidgets.QMenuBar(self)
        self.active_tabs = {}

    def send_user_input(self):
        text = self.input_line.text()
        if text.strip():
            command = self.client.command_handler.get_command(text)
            command()  # TODO: надо ли новый поток? da.
            input_text = f"<{self.client.nickname}>: {text}"
            chat = self.tabs_panel.currentWidget().findChild(QtWidgets.QWidget, "chat_content")
            chat.layout().insertWidget(0, QtWidgets.QLabel(input_text))
            if command.output:
                chat.layout().insertWidget(0, QtWidgets.QLabel(command.output))
            self.input_line.clear()

    def print_messages(self, messages: str):
        for message in messages.split("\n"):
            

    def setup_ui(self):
        self.setObjectName("main_window")
        self.resize(800, 600)
        self.setWindowIcon(QtGui.QIcon("etc/icon.png"))
        self.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.setCentralWidget(self.central_widget)
        self.setMenuBar(self.menu_bar)

        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)

        self.send_button.setFont(font)
        self.send_button.setObjectName("send_button")
        self.send_button.clicked.connect(self.send_user_input)

        grid_layout = QtWidgets.QGridLayout(self.central_widget)
        grid_layout.addWidget(self.send_button, 1, 0, 1, 1)
        grid_layout.addWidget(self.input_line, 1, 1, 1, 1)
        grid_layout.addWidget(self.tabs_panel, 0, 0, 1, 2)

        self.add_new_tab("Client")
        self.add_new_tab("Test")
        self.tabs_panel.setCurrentIndex(0)

        self.menu_bar.setGeometry(QtCore.QRect(0, 0, 800, 20))

        self.actionNickname = QtWidgets.QAction(self)
        self.actionNickname.setObjectName("actionNickname")

        self.actionServer1 = QtWidgets.QAction(self)
        self.actionServer1.setMenuRole(QtWidgets.QAction.ApplicationSpecificRole)
        self.actionServer1.setObjectName("actionServer1")

        self.menu_settings = QtWidgets.QMenu(self.menu_bar)
        self.menu_settings.setObjectName("menu_settings")
        self.menu_settings.addAction(self.actionNickname)

        self.menu_favourites = QtWidgets.QMenu(self.menu_bar)
        self.menu_favourites.setObjectName("menu_favourites")
        self.menu_favourites.addAction(self.actionServer1)

        self.menu_bar.addAction(self.menu_settings.menuAction())
        self.menu_bar.addAction(self.menu_favourites.menuAction())

        self.active_tabs["Client"].append_to_chat(QtWidgets.QLabel("TEST"))

        self.retranslateUi(self)

        QtCore.QMetaObject.connectSlotsByName(self)

    def remove_tab(self, name: str):
        if name in self.active_tabs:
            index = self.tabs_panel.indexOf(self.active_tabs[name])
            self.tabs_panel.removeTab(index)

    def add_new_tab(self, name: str):
        tab_to_add = ClientTab()
        self.active_tabs[name] = tab_to_add
        self.tabs_panel.addTab(tab_to_add, name)


    def retranslateUi(self, main_window):
        _translate = QtCore.QCoreApplication.translate
        main_window.setWindowTitle(_translate("main_window", "IRC Client"))
        self.send_button.setText(_translate("main_window", "Отправить"))
        self.send_button.setShortcut(_translate("main_window", "Return"))
        self.menu_settings.setTitle(_translate("main_window", "Settings"))
        self.menu_favourites.setTitle(_translate("main_window", "Favourites"))
        self.actionServer1.setText(_translate("main_window", "Server1"))
        self.actionNickname.setText(_translate("main_window", "Set nickname"))
