#!/usr/bin/env python3

import psycopg2
import signal
import pycx4.qcda as cda

from aux.service_daemon import QtService
from .device import Dev

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


class ICWService(QtService):
    def main(self):
        self.w = IcWatcher()

    def clean(self):
        self.log_str('exiting from icw')


icw_d = ICWService("ic_watcher")
