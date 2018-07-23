from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import uic

import sys
import pycx4.qcda as cda


class IcWatcherInfo(QMainWindow):
    def __init__(self):
        super(IcWatcherInfo, self).__init__()
        uic.loadUi("icw_info.ui", self)
        self.chan_log = cda.StrChan('cxhw:2.ic_watcher.log', max_nelems=1024, on_update=1)
        self.chan_ofr = cda.StrChan('cxhw:2.ic_watcher.ofr', max_nelems=1024, on_update=1)

        self.chan_log.valueChanged.connect(self.log_update)
        self.chan_ofr.valueChanged.connect(self.ofr_update)

    def log_update(self, chan):
        print("log")
        log = chan.val
        self.log_text.append(log)

    def ofr_update(self, chan):
        ofr = chan.val
        if ofr:
            for elem in ofr:
                self.ofr_text.append(elem)


app = QApplication(['IcWatcherInfo'])
w = IcWatcherInfo()
w.show()
sys.exit(app.exec_())


