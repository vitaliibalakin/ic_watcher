#!/usr/bin/env python3

import pycx4.qcda as cda

from .condition import Cond


class Dev:
    def __init__(self, dname, dtype, dcnd, dstate_chans, sys_info_d, ofr_list):
        super(Dev, self).__init__()
        self.fail_count = {'curr_state': 0, 'range_state': 0, 'is_on': 0, 'ilk': 0}
        self.chans = []
        self.values = {}
        self.cnd_callback = {}
        self.sys_chans = {}
        self.ps_error = {'time': 0, 'val': 0, 'prev': 0}

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
                                                                        sys_info_d, ofr_list, self.fail_count,
                                                                        self.ps_error), elem['func'])
                except Exception as err:
                    print('callbacks creating', err)

    def ps_change_state(self, chan):
        self.values[chan.name] = chan.val
        if chan.name in self.cnd_callback:
            self.ps_error['val'] = chan.val
            self.ps_error['time'] = chan.time
            self.ps_error['prev'] = chan.prev_time
            self.cnd_callback[chan.name](False)
