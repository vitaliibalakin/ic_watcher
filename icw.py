#!/usr/bin/env python3

# from PyQt5.QtWidgets import QApplication

from aQt.QtCore import QTimer

import sys
import json
import datetime
import psycopg2
import signal
import functools
import operator
import numpy as np
import pycx4.qcda as cda

from aux.service_daemon import QtService

signal.signal(signal.SIGINT, signal.SIG_DFL)


class IcWatcher:
    """
    watching for DR elements status
    """
    def __init__(self):
        super(IcWatcher, self).__init__()
        try:
            self.conn = psycopg2.connect(dbname='icdata', user='postgres', host='pg10-srv', password='')
            print("Connected to DB")
        except:
            print("No access to DB")

        self.sys_info_d = {'logs': cda.StrChan('cxhw:1.ic_watcher.logs', max_nelems=1024, on_update=1),
                           'ofr': cda.StrChan('cxhw:1.ic_watcher.ofr', max_nelems=1024, on_update=1)}
        self.ofr_list = []

        self.dev_chans_list = []

        self.conditions_um4 = [{'func': 'curr_state', 'chans': ['Iset', 'Imes'], 'wait_time': 3000, 'up_lim': 8000,
                                'down_lim': 200, 'err_code': 'I_mes_problem'},
                               {'func': 'range_state', 'chans': ['Umes'], 'up_lim': 13, 'down_lim': 0,
                                'err_code': 'U_out_of_range'}]
        self.conditions_vs = [{'func': 'range_state', 'chans': ['Imes'], 'up_lim': 256, 'down_lim': 0,
                               'err_code': 'I_out_of_range'},
                              {'func': 'range_state', 'chans': ['Umes'], 'up_lim': 7, 'down_lim': 2,
                               'err_code': 'U_out_of_range'}]
        self.conditions_um15 = [{'func': 'curr_state', 'chans': ['Iset', 'Imes'], 'wait_time': 3000, 'up_lim': 8000,
                                 'down_lim': 200, 'err_code': 'I_mes_problem'}]
        self.conditions_vch300 = [{'func': 'curr_state', 'chans': ['Iset', 'Imes'], 'wait_time': 3000, 'up_lim': 1000,
                                   'down_lim': 0, 'err_code': 'I_mes_problem'}]
        self.conditions_v300 = [{'func': 'curr_state', 'chans': ['Iset', 'Imes'], 'wait_time': 3000, 'up_lim': 1000,
                                 'down_lim': 0, 'err_code': 'I_mes_problem'}]
        self.conditions_pa10 = [{'func': 'curr_state', 'chans': ['Iset', 'Imes'], 'wait_time': 3000, 'up_lim': 1000,
                                 'down_lim': 0, 'err_code': 'I_mes_problem'},
                                {'func': 'range_state', 'chans': ['Umes'], 'up_lim': 13, 'down_lim': 0,
                                 'err_code': 'U_out_of_range'}]
        self.conditions_vch1000 = [
            {'func': 'curr_state', 'chans': ['Iset', 'dcct1'], 'wait_time': 3000, 'up_lim': 5000,
             'down_lim': 0, 'err_code': 'I_mes_problem'},
            {'func': 'is_on', 'chans': ['is_on'], 'err_code': 'PS is off'},
            {'func': 'ilk', 'chans': ['ilk_imax', 'ilk_inverter', 'ilk_out_prot1',
                                      'ilk_out_prot2', 'ilk_out_prot3', 'ilk_phase', 'ilk_temp'],
             'wait_time': 3000, 'err_code': 'Interlock'}]
        self.conditions_ist = [
            {'func': 'curr_state', 'chans': ['Iset', 'dcct1'], 'wait_time': 3000, 'up_lim': 5000,
             'down_lim': 0, 'err_code': 'I_mes_problem'},
            {'func': 'is_on', 'chans': ['is_on'], 'err_code': 'is_on'},
            {'func': 'ilk', 'chans': ['ilk_imax', 'ilk_umax', 'ilk_out_prot', 'ilk_phase', 'ilk_temp', 'ilk_water',
                                      'ilk_battery'], 'wait_time': 3000, 'err_code': 'Interlock'}]

        self.conditions_dict = {'UM15': self.conditions_um15, 'UM4': self.conditions_um4, 'vaciva': self.conditions_vs,
                                'vac124': self.conditions_vs, 'vch300': self.conditions_vch300,
                                'v300': self.conditions_v300, 'pa10': self.conditions_pa10,
                                'vch1000': self.conditions_vch1000, 'ist': self.conditions_ist}
        self.state_chans_dict = {'magnet': [], 'ion_pump': []}
        self.choose_state_dict = {'UM15': 'magnet', 'UM4': 'magnet', 'vaciva': 'ion_pump', 'vac124': 'ion_pump',
                                  'vch300': 'magnet', 'v300': 'magnet', 'pa10': 'magnet', 'vch1000': 'magnet',
                                  'ist': 'magnet'}
        self.chans_dict = {'UM15': [], 'UM4': [], 'vaciva': [], 'vac124': [], 'vch300': [], 'v300': [], 'pa10': [],
                           'vch1000': [], 'ist': []}
        self.devnames_dict = {'UM15': [], 'UM4': [], 'vaciva': [], 'vac124': [], 'vch300': [], 'v300': [], 'pa10': [],
                              'vch1000': [], 'ist': []}

        self.cur = self.conn.cursor()
        self.cur.execute("select devtype.name, chan.name from chan,devtype_chans,devtype "
                         "where chan.id=devtype_chans.chan_id and devtype.id=devtype_chans.devtype_id and "
                         "devtype.name in ('magnet', 'ion_pump') group by grouping sets((devtype.name, chan.name))")
        for elem in self.cur.fetchall():
            self.state_chans_dict[elem[0]].append(elem[1])
        print('state_chans_dict', self.state_chans_dict)

        self.cur.execute("select devtype.name, chan.name from chan,devtype_chans,devtype "
                         "where chan.id=devtype_chans.chan_id and devtype.id=devtype_chans.devtype_id and "
                         "devtype.name in ('UM4', 'UM15', 'vaciva', 'vac124', 'vch300', 'v300', 'pa10', 'vch1000', 'ist') group by grouping sets((devtype.name, chan.name))")
        # 'UM4', 'UM15', 'vaciva', 'vac124', 'vch300', 'v300', 'pa10', 'vch1000', 'ist'
        for elem in self.cur.fetchall():
            self.chans_dict[elem[0]].append(elem[1])
        print(self.chans_dict)

        self.cur.execute("select devtype.name, namesys.name || '.' || dev.name as full_name from dev,dev_devtype,devtype, namesys "
                         "where dev.id=dev_devtype.dev_id and devtype.id=dev_devtype.devtype_id and namesys.id=dev.namesys_id and "
                         "devtype.name in ('UM4', 'UM15', 'vaciva', 'vac124', 'vch300', 'v300', 'pa10', 'vch1000', 'ist') group by grouping sets((devtype.name, full_name))")
        for elem in self.cur.fetchall():
            self.devnames_dict[elem[0]].append(elem[1])
        # self.devnames_dict['ist'].append('canhw:11.vit_sim_ist')
        print('devname_dict', self.devnames_dict)

        for elem in self.devnames_dict:
            for dname in self.devnames_dict[elem]:
                self.dev_chans_list.append(Dev(dname, self.chans_dict[elem], self.conditions_dict[elem],
                                               self.state_chans_dict[self.choose_state_dict[elem]],
                                               self.sys_info_d, self.ofr_list))


class Dev:
    def __init__(self, dname, dtype, dcnd, dstate_chans, sys_info_d, ofr_list):
        super(Dev, self).__init__()
        self.fail_count = {'curr_state': 0, 'range_state': 0, 'is_on': 0, 'ilk': 0}
        self.chans = []
        self.values = {}
        self.cnd_callback = {}
        self.sys_chans = {}
        for dchan in dstate_chans:
            if dname == 'canhw:11.vit_sim_ist':
                chan = cda.DChan('canhw:11' + '.' + dname.split('.')[-1] + '.' + dchan)
                self.sys_chans[dchan] = chan
            else:
                chan = cda.DChan('cxhw:1' + '.' + dname.split('.')[-1] + '.' + dchan)
                self.sys_chans[dchan] = chan

        for dchan in dtype:
            chan = cda.DChan(dname + '.' + dchan)
            chan.valueChanged.connect(self.ps_change_state)
            self.chans.append(chan)
            self.values[chan.name] = None
            for elem in dcnd:
                try:
                    for cnd_name in elem['chans']:
                        if chan.name.split('.')[-1] == cnd_name:
                            # print(chan.name, cnd_name)
                            self.cnd_callback[chan.name] = getattr(Cond(dname, dchan, self.values, elem, self.sys_chans,
                                                                        sys_info_d, ofr_list, self.fail_count),
                                                                   elem['func'])
                except Exception as err:
                    print('callbacks creating', err)

    def ps_change_state(self, chan):
        self.values[chan.name] = chan.val
        if chan.name in self.cnd_callback:
            self.cnd_callback[chan.name](False)
        else:
            pass
            # print('kek')


class Cond:
    def __init__(self, dname, dchan, values, cnd, sys_chans, sys_info_d, ofr_list, fail_count):
        super(Cond, self).__init__()
        # 0 position is curr_state, 1 is range_state, 2 is is_on, 3 is ilk
        self.fail_count = fail_count
        self.values = values
        # print(self.values)
        self.dname = dname
        self.dchan = dchan
        self.cnd = cnd
        self.sys_chans = sys_chans
        self.sys_info_d = sys_info_d
        self.ofr_list = ofr_list
        self.tout_run = False
        self.aout_run = 0
        self.error_code = ' '
        self.sys_info_d['ofr'].setValue(json.dumps([]))
        self.time = 0

    def log_manager(self, source):
        """
        func collects the fail statuses from whole power supply parts
        :return:  sent collected info and general status PS FAIL to CX-server, if some fail=1 add the PS to
        *Out_of_running* list or remove from it if fail=0
        """
        # print(self.dname, 'error_data_send')
        # print(self.sys_chans['fail'].val)
        if self.fail_count[source]:
            if not (self.dname.split('.')[-1] in self.ofr_list):
                time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.ofr_list.append(self.dname.split('.')[-1])
                self.sys_info_d['ofr'].setValue(json.dumps(self.ofr_list))
                self.sys_chans['fail'].setValue(1)
                log = str(time) + '|' + self.dname.split('.')[-1] + '|' + self.error_code
                self.sys_info_d['logs'].setValue(log)
                if self.dname.split('.')[-1] == 'WG1_2':
                    self.time = datetime.datetime.now()
                    print('WG1_2', self.time)
        s = 0
        for k, v in self.fail_count.items():
            s += v
        if not s:
            if self.dname.split('.')[-1] in self.ofr_list:
                time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.ofr_list.remove(self.dname.split('.')[-1])
                self.sys_info_d['ofr'].setValue(json.dumps(self.ofr_list))
                self.sys_chans['fail'].setValue(0)
                log = str(time) + '|' + self.dname.split('.')[-1] + '|' + 'PS IS RUNNING'
                self.sys_info_d['logs'].setValue(log)
                if self.dname.split('.')[-1] == 'WG1_2':
                    self.time = self.time - datetime.datetime.now()
                    print('WG1_2', self.time)

    # def curr_timer_run(self):
    #     val_1 = self.values[self.dname + '.' + self.cnd['chans'][0]]
    #     val_2 = self.values[self.dname + '.' + self.cnd['chans'][1]]
    #     print('on_update', self.dname, 'FAIL', val_2, val_1)
    #     if abs(val_1) and abs(val_2) > 200:
    #         if abs(val_2 - val_1) > 0.1 * val_1:
    #             self.error_data_send()
    #     self.tout_run = False

    def curr_state(self, in_call):
        """
        func is called then power supplier current changes
        :param in_call: False, if callback calls the func; True, if timer calls
        :return: nothing, gives fail=1 if measured ps current differ then given; fail=0 instead
        """
        self.error_code = self.cnd['err_code']
        val_1 = self.values[self.dname + '.' + self.cnd['chans'][0]]
        val_2 = self.values[self.dname + '.' + self.cnd['chans'][1]]
        # print('curr_state', self.dname, in_call, val_1, val_2)
        if not in_call:    # Not-timer called curr_state
            if val_1 and val_2:
                if self.cnd['up_lim'] > abs(val_1) >= self.cnd['down_lim'] and \
                        self.cnd['up_lim'] > abs(val_2) >= self.cnd['down_lim']:
                    if abs(val_2 - val_1) > 0.05 * abs(val_1):
                        if not self.tout_run:
                            self.tout_run = True
                            QTimer().singleShot(self.cnd['wait_time'], functools.partial(self.curr_state, True))
                    else:
                        self.fail_count['curr_state'] = 0
                        self.log_manager('curr_state')
        else:    # Timer called curr_state
            if self.cnd['up_lim'] > abs(val_1) >= self.cnd['down_lim'] and \
                        self.cnd['up_lim'] > abs(val_2) >= self.cnd['down_lim']:
                if abs(val_2 - val_1) > 0.05 * abs(val_1):
                    self.fail_count['curr_state'] = 1
                    self.log_manager('curr_state')
            self.tout_run = False

    def range_state(self, in_call):
        """
        func is called then power supplier current changes
        :param in_call: False, if callback calls the func; True, if timer calls
        :return: nothing, gives fail=1 if ps current above or below the required values; fail=0 instead
        """
        self.error_code = self.cnd['err_code']
        val_1 = self.values[self.dname + '.' + self.cnd['chans'][0]]
        if self.cnd['up_lim'] >= abs(val_1) >= self.cnd['down_lim']:
            self.fail_count['range_state'] = 0
            self.log_manager('range_state')
            # print('r_state okay', self.dname + '.' + self.cnd['chans'][0], val_1)
        else:
            self.fail_count['range_state'] = 1
            self.log_manager('range_state')
            # print('r_state not okay', self.dname + '.' + self.cnd['chans'][0], val_1)

    def is_on(self, in_call):
        """
        func is called then power supplier status changes
        :param in_call: False, if callback calls the func; True, if timer calls
        :return: nothing, gives fail=1 if PS is off; fail=1 instead
        """
        # print("is_on here", self.dname, self.values[self.dname + '.' + self.cnd['chans'][0]])
        self.error_code = self.cnd['err_code']
        if self.values[self.dname + '.' + self.cnd['chans'][0]]:
            self.fail_count['is_on'] = 0
            self.log_manager('is_on')
        else:
            self.fail_count['is_on'] = 1
            self.log_manager('is_on')

    def ilk(self, in_call):
        """
        func is called then power supplier interlocks (ilks) status changes
        :param in_call: False, if callback calls the func; True, if timer calls
        :return: nothing, gives fail=1 if some ilks is on; fail=0 instead
        """
        # print('ilk', self.dname, self.dname + '.' + self.dchan, self.values[self.dname + '.' + self.dchan])
        flag = False
        for chan in self.cnd['chans']:
            flag = flag or self.values[self.dname + '.' + chan]
        if not flag:
            if self.fail_count['ilk']:
                self.error_code = self.dchan + '|' + self.cnd['err_code'] + '|' + 'user_turned_on'
                self.fail_count['ilk'] = 0
                self.log_manager('ilk')
        elif self.values[self.dname + '.' + self.dchan]:
            self.error_code = self.dchan + '|' + self.cnd['err_code']
            self.fail_count['ilk'] = 1
            self.log_manager('ilk')
        elif not self.values[self.dname + '.' + self.dchan]:
            self.error_code = self.dchan + '|' + self.cnd['err_code'] + '|' + 'user_turned_on'
            self.log_manager('ilk')
        else:
            pass
            # print('whats up, I shouldnt be here!', flag, self.values[self.dname + '.' + self.dchan])


# if __name__ == "__main__":
#     app = QApplication(['IcWatcher'])
#     w = IcWatcher()
#     sys.exit(app.exec_())


class ICWService(QtService):
    def main(self):
        self.w = IcWatcher()

    def clean(self):
        self.log_str('exiting from icw')


icw_d = ICWService("ic_watcher")
