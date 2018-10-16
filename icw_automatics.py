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


class IcWatcherAutomatic:
    def __init__(self):
        super(IcWatcherAutomatic, self).__init__()
        try:
            self.conn = psycopg2.connect(dbname='icdata', user='postgres', host='pg10-srv', password='')
            print("Connected to DB")
        except:
            print("No access to DB")

        self.wait_time = 3000
        self.RUN_STATE = 1
        self.atimer_run = False

        self.sys_info_d = {'logs': cda.StrChan('cxhw:1.ic_watcher.logs', max_nelems=1024, on_update=1),
                           'ofr': cda.StrChan('cxhw:1.ic_watcher.ofr', max_nelems=1024, on_update=1)}
        self.ofr_list = []

        self.devnames_dict = {'vch1000': [], 'ist': []}
        self.state_chans = []

        self.fail_chans = []
        self.rst_list = ['rst_ilks']
        self.rst_dict = {}

        self.cur = self.conn.cursor()
        # self.cur.execute("select devtype.name, chan.name from chan,devtype_chans,devtype "
        #                  "where chan.id=devtype_chans.chan_id and devtype.id=devtype_chans.devtype_id and "
        #                  "devtype.name in ('magnet') group by grouping sets((devtype.name, chan.name))")
        # for elem in self.cur.fetchall():
        #     self.state_chans.append(elem[1])
        # print('state_chans_list', self.state_chans)
        self.cur.execute(
            "select devtype.name, namesys.name || '.' || dev.name as full_name from dev,dev_devtype,devtype, namesys "
            "where dev.id=dev_devtype.dev_id and devtype.id=dev_devtype.devtype_id and namesys.id=dev.namesys_id and "
            "devtype.name in ('vch1000', 'ist') group by grouping sets((devtype.name, full_name))")
        # for elem in self.cur.fetchall():
        #     self.devnames_dict[elem[0]].append(elem[1])
        self.devnames_dict['ist'].append('canhw:11.vit_sim_ist')
        print('devname_dict', self.devnames_dict)

        for elem in self.devnames_dict:
            for devname in self.devnames_dict[elem]:
                chan = cda.DChan('canhw:11' + '.' + devname.split('.')[-1] + '.' + 'is_on')
                self.fail_chans.append(chan)
                tmp_list = []
                for rst_chan in self.rst_list:
                    tmp_list.append(cda.DChan(devname + '.' + rst_chan))
                self.rst_dict.update({chan.name: tmp_list})
        for chan in self.fail_chans:
            chan.valueChanged.connect(self.auto_run)

    def auto_run(self, chan, in_call=0):
        """
        When chan.is_on.val became 0, runs auto on. Only 1 time
        :param chan: chan which was changed
        :param in_call: how many times auto_rus was called from timer
        :return: new power supply state
        """
        if self.RUN_STATE and (not chan.val):
            if in_call < len(self.rst_dict[chan.name]):
                self.atimer_run = True
                QTimer().singleShot(self.wait_time, functools.partial(self.reset, chan,
                                                                      self.rst_dict[chan.name][in_call], in_call))
            else:
                self.atimer_run = False
                print('automatics finished')
                chan.setValue(1)
        elif chan.val and self.atimer_run:
            self.atimer_run = False
            print('user turned on PS')
        elif chan.val:
            print('auto tuned on')
        else:
            print('whaaaat, I shouldnt be there')

    def reset(self, chan_fail, chan, in_call):
        """
        rebooting of the required channel
        :param chan_fail: power supply fail chan
        :param chan: this chan should be rebooted
        :param in_call: channel number in rst_list
        :return: nothing
        """
        if self.atimer_run:
            in_call += 1
            chan.setValue(1)
            QTimer().singleShot(1500, functools.partial(self.auto_run, chan_fail, in_call))
            print(chan.name)
        else:
            print('emergency stop auto')

    # try:
    #     chan = cda.DChan('canhw:11' + '.' + dname.split('.')[-1] + '.' + 'rst_ilks')
    #     self.sys_chans['rst_ilks'] = chan
    # except Exception as err:
    #     print(err)
    # print('sys_chan', self.sys_chans)
    #     if not flag:
    #         if self.fail_count[3]:
    #             self.error_code = self.dchan + '|' + self.cnd['err_code'] + '|' + 'auto_turned_on'
    #             self.fail_count[3] = 0
    #             self.fail_out_check()
    #     elif flag and self.values[self.dname + '.' + self.dchan]:
    #         self.error_code = self.dchan + '|' + self.cnd['err_code'] + '|' + 'auto_is_usefull'
    #         self.error_data_send()
    #     elif flag and (not self.values[self.dname + '.' + self.dchan]):
    #         self.error_code = self.dchan + '|' + self.cnd['err_code'] + '|' + 'auto_turned_on'
    #         self.error_data_send()
    #     else:
    #         print('whats up, I shouldnt be here!', flag, self.values[self.dname + '.' + self.dchan])
    #
    # def reset_ilks(self):
    #     # print(self.sys_chans)
    #     self.sys_chans['rst_ilks'].setValue(1)
    #     self.timer.singleShot(self.cnd['wait_time'], functools.partial(self.ilk, True))


if __name__ == '__main__':
    app = QApplication(['IcWatcherAutomatic'])
    w = IcWatcherAutomatic()
    sys.exit(app.exec_())