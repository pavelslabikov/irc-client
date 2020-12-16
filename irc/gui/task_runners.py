from PyQt5.QtCore import QRunnable


class BackgroundTask(QRunnable):
    def __init__(self, target: callable, *args):
        super(BackgroundTask, self).__init__()
        self.target = target
        self.args = args

    def run(self) -> None:
        self.target(*self.args)
