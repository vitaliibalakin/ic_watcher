from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import uic

import sys
import pycx4.qcda as cda
import json


class IcWatcherInfo(QMainWindow):
    def __init__(self):
        super(IcWatcherInfo, self).__init__()
        uic.loadUi("icw_info.ui", self)
        self.sys_info = {'logs': cda.StrChan('cxhw:1.ic_watcher.logs', max_nelems=1024, on_update=1),
                         'ofr': cda.StrChan('cxhw:1.ic_watcher.ofr', max_nelems=1024, on_update=1)}
        for chan in self.sys_info:
            self.sys_info[chan].valueMeasured.connect(self.update_sys_info)

        self.update_dict = {'cxhw:1.ic_watcher.logs': self.update_logs, 'cxhw:1.ic_watcher.ofr': self.update_ofr}
        # self.btn_clr_ofr.clicked.connect(self.clr)

    def update_sys_info(self, chan):        # factory pattern
        self.update_dict[chan.name](chan.val)
        # if chan.name == 'cxhw:1.ic_watcher.logs':
        #     self.log_text.append(chan.val)
        # if chan.name == 'cxhw:1.ic_watcher.ofr':
        #     self.ofr_text.clear()
        #     chan_stat_dict = json.loads(chan.val)
        #     for elem in chan_stat_dict:
        #         if chan_stat_dict[elem]:
        #             self.ofr_text.append(elem)

    def update_logs(self, val):
            self.log_text.append(val)

    def update_ofr(self, val):
        self.ofr_text.clear()
        print(val)
        chan_stat_dict = json.loads(val)
        for elem in chan_stat_dict:
            if chan_stat_dict[elem]:
                self.ofr_text.append(elem)


app = QApplication(['IcWatcherInfo'])
w = IcWatcherInfo()
w.show()
sys.exit(app.exec_())