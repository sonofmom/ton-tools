import time
import Libraries.tools.general as gt

class Logger:
    def __init__(self, verbosity):
        self.verbosity = verbosity

    def log(self, facility, level, message):
        levels = ['NONE', 'ERROR', 'INFO', 'DEBUG']
        if level <= self.verbosity:
            print("{} [{}|{}]: {}".format(gt.get_datetime_string(time.time()),
                                                    facility,
                                                    levels[level],
                                                    message))

