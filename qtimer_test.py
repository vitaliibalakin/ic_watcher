#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

#import functools
import sys

class IcWatcher:
    def __init__(self):
        super(IcWatcher, self).__init__()
        self.timer = QTimer()
        self.gell()
        self.name = "Dick"
        self.count = 0

    def gell(self):
        #self.timer.singleShot(3000, functools.partial(self.on_update, 'bitch'))
        self.timer.singleShot(3000, self.on_update)


    def on_update(self):
        print('im here', self.name)
        self.count +=1
        print('shot:', self.count)
        self.timer.singleShot(3000, self.on_update)



app = QApplication(['IcWatcher'])
print("init timer")
w = IcWatcher()


sys.exit(app.exec_())