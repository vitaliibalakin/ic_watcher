from PyQt5.QtWidgets import QApplication
import sys


class DevsTree:
    def __init__(self):
        super(DevsTree, self).__init__()


app = QApplication(['DevsTree'])
w = DevsTree()
sys.exit(app.exec_())