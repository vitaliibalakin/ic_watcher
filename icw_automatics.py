if in_call:
    if not flag:
        if self.fail_count[3]:
            self.error_code = self.dchan + '|' + self.cnd['err_code'] + '|' + 'auto_turned_on'
            self.fail_count[3] = 0
            self.fail_out_check()
    elif flag and self.values[self.dname + '.' + self.dchan]:
        self.error_code = self.dchan + '|' + self.cnd['err_code'] + '|' + 'auto_is_usefull'
        self.error_data_send()
    elif flag and (not self.values[self.dname + '.' + self.dchan]):
        self.error_code = self.dchan + '|' + self.cnd['err_code'] + '|' + 'auto_turned_on'
        self.error_data_send()
    else:
        print('whats up, I shouldnt be here!', flag, self.values[self.dname + '.' + self.dchan])

    def reset_ilks(self):
        # print(self.sys_chans)
        self.sys_chans['rst_ilks'].setValue(1)
        self.timer.singleShot(self.cnd['wait_time'], functools.partial(self.ilk, True))
