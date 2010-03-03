from zope.interface import Interface
from zope.interface import implements

from repoze.workflow import Workflow # imported

class IContent(Interface):
    pass

class IContent2(Interface):
    pass

class Content(object):
    implements(IContent)

def callback(context, transition):
    """ """

def elector(context): return True

def has_permission(permission, context, request):
    """ """
