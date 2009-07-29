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

