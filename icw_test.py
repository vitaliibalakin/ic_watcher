from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import uic

import sys
import datetime, time


class ICWT(QMainWindow):
    def __init__(self):
        super(ICWT, self).__init__()
        uic.loadUi("icw_test.ui", self)
        self.on_off_st = 0
        self.auto_st = 0
        self.LOG = ''

        self.Imeas.valueChanged.connect(self.cond)
        self.ilk_water.stateChanged.connect(self.ilks_water)
        self.ilk_battery.stateChanged.connect(self.ilks_battery)
        self.ilk_heat.stateChanged.connect(self.ilks_heat)
        self.ilk_overcurr.stateChanged.connect(self.ilks_overcurr)
        self.ilk_reset.clicked.connect(self.ilk_rst)
        self.on_off.stateChanged.connect(self.ps_st_change)
        self.permission.valueChanged.connect(self.auto_switch)

    def auto_switch(self):
        if self.permission.value() == 0:
            self.auto_st = 1
        if self.permission.value() == 2:
            self.auto_st = 0

    def ps_st_change(self):
        if self.on_off.isChecked():
            if self.ilk_battery.isChecked() + self.ilk_water.isChecked() + self.ilk_heat.isChecked() \
                    + self.ilk_overcurr.isChecked() == 0:
                self.on_off_st = 1
                self.Imeas.setValue(100)
            else:
                self.log_text.append("INTERLOCKS")
                self.on_off.setCheckState(0)
        else:
            self.on_off_st = 0
            self.Imeas.setValue(0)

    def cond(self):
        if self.on_off_st == 1:
            if abs(self.Iset.value() - self.Imeas.value()) >= 0.1 * self.Imeas.value():
                self.fail_st.setText("FAIL = 1")
                self.ofr_text.append("PS FAIL")
                self.log_text.append("The value changed so much")
            else:
                self.fail_st.setText("FAIL = 0")
                self.ofr_text.clear()

    def ilks_water(self):
        if self.on_off_st == 1:
            print("inside")
            if self.ilk_water.isChecked():
                self.fail_st.setText("FAIL = 1")
                time_on = datetime.datetime.time(datetime.datetime.now())
                self.log_text.append(str(time_on))
                self.log_text.append("water is clicked")
                self.auto_ilk_reset(self.ilk_water)
            else:
                self.fail_st.setText("FAIL = 0")
                time_off = datetime.datetime.time(datetime.datetime.now())
                self.log_text.append(str(time_off))
                self.log_text.append("water is out")
                self.ofr_text.clear()

    def ilks_battery(self):
        if self.on_off_st == 1:
            if self.ilk_battery.isChecked():
                self.fail_st.setText("FAIL = 1")
                time_on = datetime.datetime.time(datetime.datetime.now())
                self.log_text.append(str(time_on))
                self.log_text.append("battery is clicked")
                self.auto_ilk_reset(self.ilk_battery)
            else:
                self.fail_st.setText("FAIL = 0")
                time_off = datetime.datetime.time(datetime.datetime.now())
                self.log_text.append(str(time_off))
                self.log_text.append("battery is out")

    def ilks_overcurr(self):
        if self.on_off_st == 1:
            if self.ilk_overcurr.isChecked():
                self.fail_st.setText("FAIL = 1")
                time_on = datetime.datetime.time(datetime.datetime.now())
                self.log_text.append(str(time_on))
                self.log_text.append("overcurr is clicked")
                self.auto_ilk_reset(self.ilk_overcurr)
            else:
                self.fail_st.setText("FAIL = 0")
                time_off = datetime.datetime.time(datetime.datetime.now())
                self.log_text.append(str(time_off))
                self.log_text.append("overcurr is out")

    def ilks_heat(self):
        if self.on_off_st == 1:
            if self.ilk_heat.isChecked():
                self.fail_st.setText("FAIL = 1")
                time_on = datetime.datetime.time(datetime.datetime.now())
                self.log_text.append(str(time_on))
                self.log_text.append("heat is clicked")
                self.auto_ilk_reset(self.ilk_heat)
            else:
                self.fail_st.setText("FAIL = 0")
                time_off = datetime.datetime.time(datetime.datetime.now())
                self.log_text.append(str(time_off))
                self.log_text.append("heat is out")

    def auto_ilk_reset(self, obj):
        if self.auto_st == 1:
            time.sleep(1)

            obj.setCheckState(self.permission.value())

            time.sleep(1)
            if obj.isChecked():
                print(obj.isChecked())
                self.log_text.append("auto can't make it work")
            else:
                print(obj.isChecked())
                time_off = datetime.datetime.time(datetime.datetime.now())
                self.log_text.append(str(time_off))
                self.log_text.append("auto made it work")

    def ilk_rst(self):
        self.ilk_water.setChecked(0)
        self.ilk_battery.setChecked(0)
        self.ilk_heat.setChecked(0)
        self.ilk_overcurr.setChecked(0)
        # a = self.log_text.toPlainText()
        # a = a.split("\n")
        # print(a)
        # for i in range(0, len(a)):
        #     if a[i] != 'water is clicked':
        #         self.ofr_text.append(a[i])


if __name__ == "__main__":
        app = QApplication(['icw_test'])
        w = ICWT()
        w.show()
        sys.exit(app.exec_())