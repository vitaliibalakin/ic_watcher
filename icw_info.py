from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import uic

import sys
import pycx4.qcda as cda
import functools


class IcWatcherInfo(QMainWindow):
    def __init__(self):
        super(IcWatcherInfo, self).__init__()
        uic.loadUi("icw_info.ui", self)
        self.sys_info = {'logs': cda.StrChan('cxhw:1.ic_watcher.logs', max_nelems=1024, on_update=1),
                         'ofr': cda.StrChan('cxhw:1.ic_watcher.ofr', max_nelems=1024, on_update=1)}
        for chan in self.sys_info:
            self.sys_info[chan].valueChanged.connect(self.update_sys_info)
        self.btn_clr_logs.clicked.connect(functools.partial(self.clr, 'logs'))
        self.btn_clr_ofr.clicked.connect(functools.partial(self.clr, 'ofr'))

    def update_sys_info(self, chan):
        if chan.name == 'logs':
            self.log_text.append(chan.val)
        if chan.name == 'ofr':
            for elem in chan.val.split('|'):
                self.ofr_text.append(elem)

    def ofr_update(self, chan):
        ofr = chan.val.split('|')
        if ofr:
            for elem in ofr:
                self.ofr_text.append(elem)

    def clr(self, name):
        self.sys_info[name].setValue(' ')


app = QApplication(['IcWatcherInfo'])
w = IcWatcherInfo()
w.show()
sys.exit(app.exec_())