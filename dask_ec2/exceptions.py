from __future__ import print_function, division, absolute_import


class DaskEc2Exception(Exception):
    pass


class RetriesExceededException(DaskEc2Exception):

    def __init__(self, function, last_exception=None, message="Retries limit exceeded"):
        super(RetriesExceededException, self).__init__(message)
        self.function = function
        self.last_exception = last_exception
