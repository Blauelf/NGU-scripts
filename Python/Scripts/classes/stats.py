"""Handles various statistics."""
from classes.navigation import Navigation
from classes.discord import Discord

import ngucon as ncon
import re
import time
import datetime
import shutil

class Stats(Navigation):
    """Handles various statistics."""

    total_xp = 0
    xp = 0
    pp = 0
    start_time = time.time()
    OCR_failures = 0

    def ocr_value(self, value):
        """Store start EXP via OCR."""
        try:
            if value == "TOTAL XP":
                self.misc()
                Stats.total_xp = int(float(self.ocr(ncon.OCR_EXPX1, ncon.OCR_EXPY1, ncon.OCR_EXPX2, ncon.OCR_EXPY2)))
                # print("OCR Captured TOTAL XP: {:,}".format(Stats.total_xp))
                Stats.OCR_failures = 0
                return Stats.total_xp
            elif value == "XP":
                self.exp()
                Stats.xp = int(self.remove_letters(self.ocr(ncon.EXPX1, ncon.EXPY1, ncon.EXPX2, ncon.EXPY2)))
                # print("OCR Captured Current XP: {:,}".format(Stats.xp))
                Stats.OCR_failures = 0
                return Stats.xp
            elif value == "PP":
                self.perks()
                Stats.pp = int(self.remove_letters(self.ocr(ncon.PPX1, ncon.PPY1, ncon.PPX2, ncon.PPY2)))
                # print("OCR Captured Current PP: {:,}".format(Stats.pp))
                Stats.OCR_failures = 0
                return Stats.pp
        except ValueError:
            Stats.OCR_failures += 1
            if Stats.OCR_failures <= 3:
                print("OCR couldn't detect {}, retrying.".format(value))
                self.ocr_value(value)
                return
            else:
                print("Something went wrong with the OCR")
                return

class EstimateRate(Stats):

    def __init__(self, duration, mode='moving_average'):
        self.mode = mode
        self.last_timestamp = time.time()
        self.last_xp = self.ocr_value("XP")
        self.last_pp = self.ocr_value("PP")
        # Differential time log and value
        self.dtime_log = []
        self.dxp_log = []
        self.dpp_log = []
        # Num runs to keep for moving average
        self.__keep_runs = 60 // duration
        self.__iteration = 0
        self.__elapsed = 0
        self.__alg = {
            'moving_average': self.__moving_average,
            'average': self.__average
        }

    def __average(self):
        """Returns the average rates"""
        avg_xp = sum(self.dxp_log) / sum(self.dtime_log)
        avg_pp = sum(self.dpp_log) / sum(self.dtime_log)
        return avg_xp, avg_pp

    def __moving_average(self):
        """Returns the moving average rates"""
        if len(self.dtime_log) > self.__keep_runs:
            self.dtime_log.pop(0)
            self.dxp_log.pop(0)
            self.dpp_log.pop(0)
        avg_xp = sum(self.dxp_log) / sum(self.dtime_log)
        avg_pp = sum(self.dpp_log) / sum(self.dtime_log)
        return avg_xp, avg_pp

    def rates(self):
        try:
            xpr, ppr = self.__alg[self.mode]()
            return round(3600*xpr), round(3600*ppr)
        except ZeroDivisionError:
            return 0, 0

    def stop_watch(self):
        """This method needs to be called for time estimation"""
        self.__iteration += 1
        cxp = self.ocr_value("XP")
        cpp = self.ocr_value("PP")
        dtime = time.time() - self.last_timestamp
        dxp = cxp - self.last_xp
        dpp = cpp - self.last_pp
        self.last_timestamp = time.time()
        self.last_xp = cxp
        self.last_pp = cpp
        self.dtime_log.append(dtime)
        self.dxp_log.append(dxp)
        self.dpp_log.append(dpp)
        print("This run: {:^8}{:^3}This run: {:^8}".format(Tracker.human_format(dxp), "|", Tracker.human_format(dpp)))

    def update_xp(self):
        """This method is used to update last xp after upgrade spends"""
        self.last_xp = Stats.xp


class Tracker():
    """
    The Tracker object collects time and value measurements for stats

    Usage: Initialize the class by calling tracker = Tracker(duration),
           then at the end of each run invoke tracker.progress() to update stats.
    """

    def __init__(self, duration, mode='moving_average'):
        self.__start_time = time.time()
        self.__iteration = 1
        self.__estimaterate = EstimateRate(duration, mode)
        #print(f"{'-' * 15} Run # {self.__iteration} {'-' * 15}")
        print("{0:{fill}{align}40}".format(f" {self.__iteration} ", fill="-", align="^"))
        print("{:^18}{:^3}{:^18}".format("XP", "|", "PP"))
        print("-" * 40)
        self.__show_progress()

    def __update_progress(self):
        self.__iteration += 1

    def __show_progress(self):
        if self.__iteration == 1:
            print('Starting: {:^8}{:^3}Starting: {:^8}'.format(self.human_format(Stats.xp), "|", self.human_format(Stats.pp)))
        else:
            elapsed = self.elapsed_time()
            xph, pph = self.__estimaterate.rates()
            report_time = "\n{0:^40}\n".format(elapsed)
            print('Current:  {:^8}{:^3}Current:  {:^8}'.format(self.human_format(Stats.xp), "|", self.human_format(Stats.pp)))
            print('Per hour: {:^8}{:^3}Per hour: {:^8}'.format(self.human_format(xph), "|", self.human_format(pph)))
            print(report_time)

    def elapsed_time(self):
        """Print the total elapsed time."""
        elapsed = round(time.time() - self.__start_time)
        elapsed_time = str(datetime.timedelta(seconds=elapsed))
        return elapsed_time

    def progress(self):
            self.__estimaterate.stop_watch()
            self.__update_progress()
            self.__show_progress()
            print("{0:{fill}{align}40}".format(f" {self.__iteration} ", fill="-", align="^"))
            print("{:^18}{:^3}{:^18}".format("XP", "|", "PP"))
            print("-" * 40)

    def adjustxp(self):
            self.__estimaterate.update_xp()

    @classmethod
    def human_format(self, num):
        num = float('{:.3g}'.format(num))
        magnitude = 0
        while abs(num) >= 1000:
            magnitude += 1
            num /= 1000.0
        return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])

