import sys

# True if we are running on Python 3.
PY3 = sys.version_info[0] == 3

if PY3: # pragma: no cover
    text_type = str
    binary_type = bytes
else:
    text_type = unicode
    binary_type = str

def text_(s, encoding='latin-1', errors='strict'):
    """ If ``s`` is an instance of ``binary_type``, return
    ``s.decode(encoding, errors)``, otherwise return ``s``"""
    if isinstance(s, binary_type):  # pragma: no cover
        return s.decode(encoding, errors)
    return s  # pragma: no cover
