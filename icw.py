from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

import sys
import json
import datetime
import psycopg2
import signal
import functools
import operator
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

        self.sys_info_d = {'logs': cda.StrChan('cxhw:1.ic_watcher.logs', max_nelems=1024, on_update=1),
                           'ofr': cda.StrChan('cxhw:1.ic_watcher.ofr', max_nelems=1024, on_update=1)}
        self.ofr_dict = {'empty': 1}

        self.dev_chans_list = []

        self.conditions_um4 = [{'func': 'curr_state', 'chans': ['Iset', 'Imes'], 'wait_time': 3000, 'up_lim': 5000,
                                'down_lim': 200, 'err_code': 'I_mes_problem'},
                               {'func': 'range_state', 'chans': ['Umes'], 'up_lim': 10, 'down_lim': 0,
                                'err_code': 'U_out_of_range'}]
        self.conditions_vs = [{'func': 'range_state', 'chans': ['Imes'], 'up_lim': 256, 'down_lim': 0,
                               'err_code': 'I_out_of_range'},
                              {'func': 'range_state', 'chans': ['Umes'], 'up_lim': 7, 'down_lim': 2,
                               'err_code': 'U_out_of_range'}]
        self.conditions_um15 = [{'func': 'curr_state', 'chans': ['Iset', 'Imes'], 'wait_time': 3000, 'up_lim': 5000,
                                 'down_lim': 200, 'err_code': 'I_mes_problem'}]
        self.conditions_vch300 = [{'func': 'curr_state', 'chans': ['Iset', 'Imes'], 'wait_time': 3000, 'up_lim': 1000,
                                   'down_lim': 0, 'err_code': 'I_mes_problem'}]
        self.conditions_v300 = [{'func': 'curr_state', 'chans': ['Iset', 'Imes'], 'wait_time': 3000, 'up_lim': 1000,
                                 'down_lim': 0, 'err_code': 'I_mes_problem'}]
        self.conditions_pa10 = [{'func': 'curr_state', 'chans': ['Iset', 'Imes'], 'wait_time': 3000, 'up_lim': 1000,
                                 'down_lim': 0, 'err_code': 'I_mes_problem'},
                                {'func': 'range_state', 'chans': ['Umes'], 'up_lim': 10, 'down_lim': 0,
                                 'err_code': 'U_out_of_range'}]
        self.conditions_vch1000 = [{'func': 'curr_state', 'chans': ['Iset', 'Imes'], 'wait_time': 3000, 'up_limit:': 5000,
                                    'down_limit': 0, 'err_code': 'I_mes_problem'},
                                   {'func': 'is_on', 'chans': ['is_on'], 'err_code': 'PS is off'},
                                   {'func': 'ilk', 'chans': ['ilk_imax', 'ilk_inverter', 'ilk_out_prot1',
                                                             'ilk_out_prot2', 'ilk_out_prot3', 'ilk_phase', 'ilk_temp'],
                                    'wait_time': 3000, 'err_code': 'Interlock'}]

        self.conditions_dict = {'UM15': self.conditions_um15, 'UM4': self.conditions_um4, 'vaciva': self.conditions_vs,
                                'vac124': self.conditions_vs, 'vch300': self.conditions_vch300,
                                'v300': self.conditions_v300, 'pa10': self.conditions_pa10,
                                'vch1000': self.conditions_vch1000}
        self.state_chans_dict = {'magnet': [], 'ion_pump': []}
        self.choose_state_dict = {'UM15': 'magnet', 'UM4': 'magnet', 'vaciva': 'ion_pump', 'vac124': 'ion_pump',
                                  'vch300': 'magnet', 'v300': 'magnet', 'pa10': 'magnet', 'vch1000': 'magnet'}
        self.chans_dict = {'UM15': [], 'UM4': [], 'vaciva': [], 'vac124': [], 'vch300': [], 'v300': [], 'pa10': [],
                           'vch1000': []}
        self.devnames_dict = {'UM15': [], 'UM4': [], 'vaciva': [], 'vac124': [], 'vch300': [], 'v300': [], 'pa10': [],
                              'vch1000': []}

        self.cur = self.conn.cursor()
        self.cur.execute("select devtype.name, chan.name from chan,devtype_chans,devtype "
                         "where chan.id=devtype_chans.chan_id and devtype.id=devtype_chans.devtype_id and "
                         "devtype.name in ('magnet', 'ion_pump') group by grouping sets((devtype.name, chan.name))")
        for elem in self.cur.fetchall():
            self.state_chans_dict[elem[0]].append(elem[1])
        print(self.state_chans_dict)

        self.cur.execute("select devtype.name, chan.name from chan,devtype_chans,devtype "
                         "where chan.id=devtype_chans.chan_id and devtype.id=devtype_chans.devtype_id and "
                         "devtype.name in ('UM4', 'UM15', 'vaciva', 'vac124', 'vch300', 'v300', 'pa10', 'vch1000') group by grouping sets((devtype.name, chan.name))")
        for elem in self.cur.fetchall():
            self.chans_dict[elem[0]].append(elem[1])
        print(self.chans_dict)

        self.cur.execute("select devtype.name, namesys.name || '.' || dev.name as full_name from dev,dev_devtype,devtype, namesys "
                         "where dev.id=dev_devtype.dev_id and devtype.id=dev_devtype.devtype_id and namesys.id=dev.namesys_id and "
                         "devtype.name in ('UM4', 'UM15', 'vaciva', 'vac124', 'vch300', 'v300', 'pa10', 'vch1000') group by grouping sets((devtype.name, full_name))")
        for elem in self.cur.fetchall():
            self.devnames_dict[elem[0]].append(elem[1])
        print(self.devnames_dict)

        for elem in self.devnames_dict:
            for dname in self.devnames_dict[elem]:
                self.dev_chans_list.append(Dev(dname, self.chans_dict[elem], self.conditions_dict[elem],
                                               self.state_chans_dict[self.choose_state_dict[elem]],
                                               self.sys_info_d, self.ofr_dict))


class Dev:
    def __init__(self, dname, dtype, dcnd, dstate_chans, sys_info_d, ofr_dict):
        super(Dev, self).__init__()
        self.chans = []
        self.values = {}
        self.cnd_callback = {}
        self.sys_chans = {}
        for dchan in dstate_chans:
            chan = cda.DChan('cxhw:1' + '.' + dname.split('.')[-1] + '.' + dchan)
            self.sys_chans[dchan] = chan
        try:
            chan = cda.DChan(dname + '.' + 'rst_ilks')
            self.sys_chans['rst_ilks'] = chan
        except:
            pass

        for dchan in dtype:
            chan = cda.DChan(dname + '.' + dchan)
            chan.valueChanged.connect(self.ps_change_state)
            self.chans.append(chan)
            self.values[chan.name] = None
            for elem in dcnd:
                try:
                    for cnd_name in elem['chans']:
                        if chan.name.split('.')[-1] == cnd_name:
                            self.cnd_callback[chan.name] = getattr(Cond(dname, dchan, self.values, elem, self.sys_chans,
                                                                        sys_info_d, ofr_dict), elem['func'])(False)
                except:
                    pass

    def ps_change_state(self, chan):
        self.values[chan.name] = chan.val
        try:
            self.cnd_callback[chan.name]()
        except:
            pass


class Cond:
    def __init__(self, dname, dchan, values, cnd, sys_chans, sys_info_d, ofr_dict):
        super(Cond, self).__init__()
        self.values = values
        self.dname = dname
        self.dchan = dchan
        self.cnd = cnd
        self.sys_chans = sys_chans
        self.sys_info_d = sys_info_d
        self.ofr_dict = ofr_dict
        self.timer = QTimer()
        self.tout_run = False
        self.aout_run = 0
        self.error_code = ' '

    def error_data_send(self):
        if not self.sys_chans['fail'].val:
            time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log = str(time) + '|' + self.dname.split('.')[-1] + '|' + self.error_code
            self.sys_info_d['logs'].setValue(log)

            self.ofr_dict['empty'] = 0
            self.ofr_dict[self.dname.split('.')[-1]] = 1
            print(self.ofr_dict)
            self.sys_info_d['ofr'].setValue(json.dumps(self.ofr_dict))

            self.sys_chans['fail'].setValue(1)
            print("REAL FAIL, GUYS", self.dname, self.error_code)

    def fail_out_check(self):
        if self.sys_chans['fail'].val:
            self.sys_chans['fail'].setValue(0)
            self.ofr_dict[self.dname.split('.')[-1]] = 0
            print(self.ofr_dict)
            if not self.ofr_dict[max(self.ofr_dict.items(), key=operator.itemgetter(1))[0]]:
                self.ofr_dict['empty'] = 1
            self.sys_info_d['ofr'].setValue(json.dumps(self.ofr_dict))
            print("UNCHECKED FAIL", self.dname)

    # def curr_timer_run(self):
    #     val_1 = self.values[self.dname + '.' + self.cnd['chans'][0]]
    #     val_2 = self.values[self.dname + '.' + self.cnd['chans'][1]]
    #     print('on_update', self.dname, 'FAIL', val_2, val_1)
    #     if abs(val_1) and abs(val_2) > 200:
    #         if abs(val_2 - val_1) > 0.1 * val_1:
    #             self.error_data_send()
    #     self.tout_run = False

    def curr_state(self, in_call):
        self.error_code = self.cnd['err_code']
        val_1 = self.values[self.dname + '.' + self.cnd['chans'][0]]
        val_2 = self.values[self.dname + '.' + self.cnd['chans'][1]]
        if not in_call:    # Not-timer called curr_state
            if val_1 and val_2:
                if self.cnd['up_lim'] > abs(val_1) and abs(val_2) >= self.cnd['down_lim']:
                    if abs(val_2 - val_1) > 0.05 * val_1:
                        if not self.tout_run:
                            self.tout_run = True
                            self.timer.singleShot(self.cnd['wait_time'], functools.partial(self.curr_state, True))
                    else:
                        self.fail_out_check()
        else:    # Timer called curr_state
            if abs(val_1) and abs(val_2) > 200:
                if abs(val_2 - val_1) > 0.05 * val_1:
                    self.error_data_send()
            self.tout_run = False

    def range_state(self, in_call):
        self.error_code = self.cnd['err_code']
        val_1 = self.values[self.dname + '.' + self.cnd['chans'][0]]
        if self.cnd['up_lim'] > abs(val_1) >= self.cnd['down_lim']:
            self.fail_out_check()
        else:
            self.error_data_send()
            print('r_state')

    def is_on(self, in_call):
        self.error_code = self.cnd['err_code']
        if self.values[self.dname + '.' + self.cnd['chans'][0]]:
            self.fail_out_check()
        else:
            self.error_data_send()

    def ilk(self, in_call):
        if not in_call:
            if self.values[self.dname + '.' + self.dchan]:
                self.aout_run = 1
                self.timer.singleShot(self.cnd['wait_time'], self.reset_ilks)
        if in_call:
            self.aout_run = 0
            if self.values[self.dname + '.' + self.dchan]:
                self.error_code = self.dchan + '|' + self.cnd['err_code'] + '|' + 'auto_is_powerless'
                self.error_data_send()
            else:
                self.error_code = self.dchan + '|' + self.cnd['err_code'] + '|' + 'auto_is_turned_on'
                self.error_data_send()

    def reset_ilks(self):
        if self.aout_run == 1:
            self.sys_chans['rst_ikls'].setValue(1)
            self.timer.singleShot(self.cnd['wait_time'], functools.partial(self.ilk, True))
        else:
            self.error_data_send()


app = QApplication(['IcWatcher'])
w = IcWatcher()
sys.exit(app.exec_())