from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import uic

import sys
import pycx4.qcda as cda


class IcWatcherInfo(QMainWindow):
    def __init__(self):
        super(IcWatcherInfo, self).__init__()
        uic.loadUi("icw_info.ui", self)
        self.chan_log = cda.VChan('ic_watcher.log', max_nelems=1024, on_update=1)
        self.chan_ofr = cda.VChan('ic_watcher.ofr', max_nelems=1024, on_update=1)


app = QApplication(['IcWatcherInfo'])
w = IcWatcherInfo()
w.show()
sys.exit(app.exec_())


