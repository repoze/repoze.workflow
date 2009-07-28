from zope.interface import Interface
from zope.interface import implements

class IContent(Interface):
    pass

class Content(object):
    implements(IContent)

def callback(context, transition):
    pass
