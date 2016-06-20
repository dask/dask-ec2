import six


if six.PY2:
    from urllib2 import URLError
else:
    from urllib.error import URLError
