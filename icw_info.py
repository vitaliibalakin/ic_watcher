#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import uic

import sys
import pycx4.qcda as cda
import json
import pyqtgraph as pg


class IcWatcherInfo(QMainWindow):
    """
    show DR elements info
    """
    def __init__(self):
        super(IcWatcherInfo, self).__init__()
        uic.loadUi("icw_info.ui", self)
        # f = pg.PlotWidget()
        # label = pg.TextItem('Vacuum', angle=90, rotateAxis=None)
        # f.addItem(label)
        # self.gridLayout.addWidget(f, 1, 0)

        self.sys_info = {'logs': cda.StrChan('cxhw:1.ic_watcher.logs', max_nelems=1024, on_update=1),
                         'ofr': cda.StrChan('cxhw:1.ic_watcher.ofr', max_nelems=1024, on_update=1)}
        for chan in self.sys_info:
            self.sys_info[chan].valueMeasured.connect(self.update_sys_info)

        self.update_dict = {'cxhw:1.ic_watcher.logs': self.update_logs, 'cxhw:1.ic_watcher.ofr': self.update_ofr}

    def update_sys_info(self, chan):        # factory pattern
        self.update_dict[chan.name](chan.val)

    def update_logs(self, val):
            self.log_text.append(val)

    def update_ofr(self, val):
        self.ofr_text.clear()
        print(val)
        chan_stat_list = json.loads(val)
        if chan_stat_list:
            for elem in chan_stat_list:
                self.ofr_text.append(elem)
        else:
            self.ofr_text.setText('OK')


if __name__ == "__main__":
    app = QApplication(['IcWatcherInfo'])
    w = IcWatcherInfo()
    w.show()
    sys.exit(app.exec_())
