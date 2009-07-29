from zope.interface import Interface

class IWorkflowFactory(Interface):
    def __call__(self, context, machine):
        """ Return an object which implements IWorkflow """

class IWorkflow(Interface):
    def execute(context, request, transition_name, guards=()):
        """ Execute a transition.
        """

    def transitions(context, request, from_state=None):
        """ Return a sequence of transition dictionaries """

class IWorkflowLookup(Interface):
    """ Marker interface used internally by get_workflow and the ZCML
    machinery.  An item registered as an IWorkflowLookup utility in
    the component registry is a dictionary that contains lists of
    workflow info dictionaries keyed by content type. """
    
    
class IDefaultWorkflow(Interface):
    """ Marker interface used internally for workflows that aren't
    associated with a particular content type"""
    
