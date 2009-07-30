from zope.interface import Interface

class IWorkflowFactory(Interface):
    def __call__(self, context, machine):
        """ Return an object which implements IWorkflow """

class IWorkflow(Interface):
    def add_state(name, callback=None, **kw):
        """ Add a new state.  ``callback`` is a callback that will be
        called when a piece of content enters this state."""

    def add_transition(name, from_state, to_state, callback=None, **kw):
        """ Add a new transition.  ``callback`` is the callback that
        will be called when this transition is made (before it enters
        the next state)."""

    def check():
        """ Check the consistency of the workflow state machine. Raise
        an error if it's inconsistent."""

    def state_of(context):
        """ Return the current state of the content object ``context``
        or None if the content object has not particpated yet in this
        workflow."""

    def initialize(context):
        """ Initialize the content object to the initial state of this
        workflow."""

    def transition(context, request, transition_name, guards=()):
        """ Execute a transition using a transition name.
        """
    def transition_to_state(context, reuqest, to_state, guards=()):
        """ Execute a transition to another state using a state name
        (``to_state``)"""

    def get_transitions(context, request, from_state=None):
        """ Return a sequence of transition dictionaries """

    def state_info(context, request, from_state=None):
        """ Return a sequence of state info dictionaries """

class IWorkflowList(Interface):
    """ Marker interface used internally by get_workflow and the ZCML
    machinery.  An item registered as an IWorkflowList utility in
    the component registry is a dictionary that contains lists of
    workflow info dictionaries keyed by content type. """
    
    
class IDefaultWorkflow(Interface):
    """ Marker interface used internally for workflows that aren't
    associated with a particular content type"""
    
