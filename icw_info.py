from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import uic

import sys
import pycx4.qcda as cda
import functools
import json


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

    def update_sys_info(self, chan):        # later factory pattern will be here
        if chan.name == 'cxhw:1.ic_watcher.logs':
            self.log_text.append(chan.val)
        if chan.name == 'cxhw:1.ic_watcher.ofr':
            self.ofr_text.clear()
            chan_stat_dict = json.loads(chan.val)
            for elem in chan_stat_dict:
                if chan_stat_dict[elem]:
                    self.ofr_text.append(elem)

    def clr(self, name):
        self.sys_info[name].setValue(' ')
        self.sys_info['ofr'].setValue(json.dumps({"empty": True}))


app = QApplication(['IcWatcherInfo'])
w = IcWatcherInfo()
w.show()
sys.exit(app.exec_())