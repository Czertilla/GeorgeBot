import logging
import pickle
import traceback

class Exceptor:
    def __init__(self):
        self.prob_count = 0
        self.problems = {}
        self.logger = logging.getLogger(__name__)
    
    def tracebacking(self):
        self.logger.error(traceback.format_exc())

    def protect(self, func: "function"):
        def protected(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger = logging.getLogger(func.__module__)
                logger.error("%s function crushed by: \n\t%s", func.__name__, e)
                self.tracebacking()
                self.prob_count += 1
                self.problems[str(e)] = self.problems.get(str(e), 0) + 1
        return protected

                