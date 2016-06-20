import time
import logging

from dask_ec2.exceptions import RetriesExceededException

logger = logging.getLogger(__name__)


def retry(retries=10, wait=5, catch=None):
    """
    Decorator to retry on exceptions raised
    """
    catch = catch or (Exception,)
    last_exception = None

    def real_retry(function):

        def wrapper(*args, **kwargs):
            for attempt in range(1, retries + 1):
                try:
                    ret = function(*args, **kwargs)
                    return ret
                except catch as e:
                    last_exception = e
                    logger.debug("Attempt %i/%i of function '%s' failed", attempt, retries,
                                 function.__name__)
                    time.sleep(wait)
                except Exception as e:
                    raise e
            else:
                raise RetriesExceededException(function=function, last_exception=last_exception)

        return wrapper

    return real_retry
