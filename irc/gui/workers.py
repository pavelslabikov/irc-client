from PyQt5.QtCore import QRunnable


class Worker(QRunnable):
    def __init__(self, target: callable, *args):
        super(Worker, self).__init__()
        self.target = target
        self.args = args

    def run(self) -> None:
        self.target(*self.args)
