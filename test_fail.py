import pycx4.qcda as cda
from PyQt5.QtWidgets import QApplication
import sys


class Test:
    def __init__(self):
        super(Test, self).__init__()
        self.fail = cda.DChan('canhw:11.vit_sim_ist.rst_ilks')
        self.ilk_water = cda.DChan('canhw:11.vit_sim_ist.ilk_water')

        self.fail.valueChanged.connect(self.clb)
        print('started')

    def clb(self, chan):
        if chan.val:
            self.ilk_water.setValue(0)
            self.fail.setValue(0)
        print("I did it")


app = QApplication(['IcWatcherInfo'])
w = Test()
sys.exit(app.exec_())