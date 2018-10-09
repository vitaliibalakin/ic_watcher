import pycx4.qcda as cda
from PyQt5.QtWidgets import QApplication
import sys


class Test:
    def __init__(self):
        super(Test, self).__init__()
        self.fail = cda.DChan('canhw:11.vit_sim_ist.is_on')

        self.fail.valueChanged.connect(self.clb)

    def clb(self, chan):
        print(chan.val)


app = QApplication(['IcWatcherInfo'])
w = Test()
sys.exit(app.exec_())