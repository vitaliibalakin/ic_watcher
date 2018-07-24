from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

import sys
import json
import datetime
import psycopg2
import signal
import functools
import pycx4.qcda as cda

signal.signal(signal.SIGINT, signal.SIG_DFL)


class IcWatcher:
    def __init__(self):
        super(IcWatcher, self).__init__()
        try:
            self.conn = psycopg2.connect(dbname='icdata', user='postgres', host='pg10-srv', password='')
            print("Connected to DB")
        except:
            print("No access to DB")

        # self.chan_log = cda.StrChan('cxhw:1.ic_watcher.logs', max_nelems=1024)
        # self.chan_ofr = cda.StrChan('cxhw:1.ic_watcher.ofr', max_nelems=1024)

        self.sys_info_d = {'logs': cda.StrChan('cxhw:1.ic_watcher.logs', max_nelems=1024),
                         'ofr': cda.StrChan('cxhw:1.ic_watcher.ofr', max_nelems=1024)}

        self.dev_chans_list = []

        self.conditions_um4 = [{'func': 'curr_state', 'chans': ['Iset', 'Imes'], 'wait_time': 100},
                               {'func': 'vol_state', 'chans': ['Umes']}]
        self.conditions_um15 = [{'func': 'curr_state', 'chans': ['Iset', 'Imes'], 'wait_time': 3000}]
        self.conditions_cvh1000 = [{'func': 'curr_state', 'chans': ['Iset', 'Imes']},
                                   {'func': 'is_on', 'cnd_chan_1': 'is_on'}]

        self.conditions_dict = {'UM15': self.conditions_um15, 'UM4': self.conditions_um4}
                                # 'vch1000': self.conditions_cvh1000}
        self.chans_dict = {'UM15': [], 'UM4': [], 'magnet': []} #, 'vch1000': []}
        self.devnames_dict = {'UM15': [], 'UM4': []} #, 'vch1000': []}

        self.cur = self.conn.cursor()
        self.cur.execute("select devtype.name, chan.name from chan,devtype_chans,devtype "
                         "where chan.id=devtype_chans.chan_id and devtype.id=devtype_chans.devtype_id and "
                         "devtype.name in ('UM4', 'UM15', 'magnet') group by grouping sets((devtype.name, chan.name))")
        for elem in self.cur.fetchall():
            self.chans_dict[elem[0]].append(elem[1])
        print(self.chans_dict)

        self.cur.execute("select devtype.name, namesys.name || '.' || dev.name as full_name from dev,dev_devtype,devtype, namesys "
                         "where dev.id=dev_devtype.dev_id and devtype.id=dev_devtype.devtype_id and namesys.id=dev.namesys_id and "
                         "devtype.name in ('UM4', 'UM15') group by grouping sets((devtype.name, full_name))")
        for elem in self.cur.fetchall():
            self.devnames_dict[elem[0]].append(elem[1])
        print(self.devnames_dict)

        for elem in self.devnames_dict:
            for dname in self.devnames_dict[elem]:
                self.dev_chans_list.append(Dev(dname, self.chans_dict[elem], self.conditions_dict[elem],
                                               self.chans_dict['magnet'], self.sys_info_d))


class Dev:
    def __init__(self, dname, dtype, dcnd, dmagnet, sys_info_d):
        super(Dev, self).__init__()
        self.chans = []
        self.values = {}
        self.dname = dname
        self.dcnd = dcnd
        self.cnd_callback = {}
        self.sys_chans = {}
        for dchan in dmagnet:
            chan = cda.DChan('cxhw:1' + '.' + dname.split('.')[-1] + '.' + dchan)
            self.sys_chans[dchan] = chan
        for dchan in dtype:
            chan = cda.DChan(dname + '.' + dchan)
            chan.valueChanged.connect(self.ps_change_state)
            self.chans.append(chan)
            self.values[chan.name] = None
            for elem in self.dcnd:
                try:
                    for x in elem['chans']:
                        if chan.name.split('.')[-1] == x:
                            self.cnd_callback[chan.name] = getattr(Cond(self.dname, self.values, elem, self.sys_chans,
                                                                        sys_info_d),
                                                                   elem['func'])
                except:
                    pass

    def ps_change_state(self, chan):
        self.values[chan.name] = chan.val
        self.cnd_callback[chan.name]()


class Cond:
    def __init__(self, dname, values, cnd, sys_chans, sys_info_d):
        super(Cond, self).__init__()
        self.values = values
        self.dname = dname
        self.cnd = cnd
        self.sys_chans = sys_chans
        self.sys_info_d = sys_info_d
        self.timer = QTimer()
        self.tout_run = False

    def timer_run(self, name):
        val_1 = self.values[self.dname + '.' + self.cnd['chans'][0]]
        val_2 = self.values[self.dname + '.' + self.cnd['chans'][1]]
        print('on_update', name, 'FAIL', val_2, val_1)
        if val_1 and val_2 > 200:
            if abs(val_2 - val_1) > 0.1 * val_1:
                self.sys_chans['fail'].setValue(1)
                time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                log = time + '|' + self.dname + '|' + 'I_set_problem'
                self.sys_info_d['logs'].setValue(json.dumps(log))

                ofr = self.sys_info_d['ofr'].val
                ofr = ofr + '|' + self.dname.split('.')[-1]
                self.sys_info_d['ofr'].setValue(json.dumps(ofr))
                print("REAL FAIL, GUYS")
        self.tout_run = False

    def curr_state(self):
        val_1 = self.values[self.dname + '.' + self.cnd['chans'][0]]
        val_2 = self.values[self.dname + '.' + self.cnd['chans'][1]]
        if val_1 and val_2:
            if val_1 and val_2 > 200:
                if abs(val_2 - val_1) > 0.1 * val_1:
                    if not self.tout_run:
                        self.tout_run = True
                        self.timer.singleShot(self.cnd['wait_time'], functools.partial(self.timer_run, self.dname +
                                                                                       self.cnd['chans'][0]))
                else:
                    print(self.dname + self.cnd['chans'][1], 'ok', val_2, val_1)

    def vol_state(self):
        if abs(self.values[self.dname + '.' + self.cnd['chans'][0]]) > 10:
            print(self.dname + '.' + self.cnd['chans'][0], 'high voltage')

    def is_on(self):
        print("is_on", self.dname + self.cnd['chans'][0], self.values[self.dname + '.' + self.cnd['chans'][0]])


app = QApplication(['IcWatcher'])
w = IcWatcher()
sys.exit(app.exec_())