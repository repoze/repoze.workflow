from zope.interface import Interface
from zope.interface import implementer

from repoze.workflow import Workflow # imported

class IContent(Interface):
    pass

class IContent2(Interface):
    pass

@implementer(IContent)
class Content(object):
    pass

def callback(context, transition):
    """ """

def elector(context): return True

def has_permission(permission, context, request):
    """ """
