from PyQt5.QtWidgets import QApplication

import sys
import pycx4.qcda as cda


class ConditionImes:
    def __init__(self, chan):
        super(ConditionImes, self).__init__()
        print("Imes", chan.name)
        chan.valueMeasured.connect(self.callback)

    def callback(self, chan):
        print("Imes")


class ConditionUmes:
    def __init__(self, chan):
        super(ConditionUmes, self).__init__()
        print("Umes", chan.name)
        chan.valueMeasured.connect(self.callback)

    def callback(self, chan):
        print("Umes")


class ConditionFactory:
    def __init__(self, chans):
        super(ConditionFactory, self).__init__()
        for chan in chans:
            try:
                self.factory_elem = cond_factory[chan.name.split('.')[1]](chan)
            except:
                pass


cond_factory = {'Imes': ConditionImes, 'Iset': ConditionImes, 'Umes': ConditionUmes}
if __name__ == "__main__":
    app = QApplication(['cond'])
    sys.exit(app.exec_())