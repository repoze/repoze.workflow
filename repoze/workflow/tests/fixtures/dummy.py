from zope.interface import Interface
from zope.interface import implementer

from repoze.workflow import WorkflowError

class IContent(Interface):
    pass

class IContent2(Interface):
    pass

@implementer(IContent)
class Content(object):
    pass

def callback(context, transition):
    """ """

def never(context, transition):  # pragma: NO COVER
    raise WorkflowError("This is never allowed")

def elector(context): return True

def has_permission(permission, context, request):
    """ """
