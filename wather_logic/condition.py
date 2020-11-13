#!/usr/bin/env python3

from PyQt5.QtCore import QTimer

import json
import datetime
import functools


class Cond:
    def __init__(self, dname, dchan, values, cnd, sys_chans, sys_info_d, ofr_list, fail_count, ps_error):
        super(Cond, self).__init__()
        # 0 position is curr_state, 1 is range_state, 2 is is_on, 3 is ilk
        self.fail_count = fail_count
        self.values = values
        self.dname = dname
        self.dchan = dchan
        self.cnd = cnd
        self.sys_chans = sys_chans
        self.sys_info_d = sys_info_d
        self.ofr_list = ofr_list
        self.tout_run = False
        self.error_code = ' '
        self.sys_info_d['ofr'].setValue(json.dumps([]))
        self.ps_error = ps_error

    def log_manager(self, source):
        """
        func collects the fail statuses from whole power supply parts
        :return:  sent collected info and general status PS FAIL to CX-server, if some fail=1 add the PS to
        *Out_of_running* list or remove from it if fail=0
        """
        if self.fail_count[source]:
            if not (self.dname.split('.')[-1] in self.ofr_list):
                time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.ofr_list.append(self.dname.split('.')[-1])
                log = str(time) + '|' + self.dname.split('.')[-1] + '|' + self.error_code
                self.sys_chans['fail'].setValue(1)
                self.sys_info_d['ofr'].setValue(json.dumps(self.ofr_list))
                self.sys_info_d['logs'].setValue(log)

                if self.dname.split('.')[-1] == 'WG1_2':
                    if self.error_code == 'U_out_of_range':
                        print('WG1_2_err', self.ps_error, self.ofr_list, self.fail_count)
            elif self.dname.split('.')[-1] == 'WG1_2':
                if self.error_code == 'U_out_of_range':
                    print('WG1_2_still_out', self.ps_error, self.ofr_list, self.fail_count)
        s = 0
        for k, v in self.fail_count.items():
            s += v
        if not s:
            if self.dname.split('.')[-1] in self.ofr_list:
                time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.ofr_list.delete(self.dname.split('.')[-1])
                log = str(time) + '|' + self.dname.split('.')[-1] + '|' + 'PS IS RUNNING'
                self.sys_chans['fail'].setValue(0)
                self.sys_info_d['ofr'].setValue(json.dumps(self.ofr_list))
                self.sys_info_d['logs'].setValue(log)
        else:
            log = ''
            for k, v in self.fail_count.items():
                if v:
                    log = log + k + '|'
            log = log[:-1]
            # self.sys_chans['errcode'].setValue(json.dumps(log))

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
        if not in_call:    # Non-timer called curr_state
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
        else:
            self.fail_count['range_state'] = 1
        self.log_manager('range_state')

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
