from zope.interface import Interface

class IWorkflow(Interface):
    def execute(request, transition_id):
        """ Execute a transition.
        """

    def transitions(request, from_state):
        """ Return a sequence of transition dictionaries """

class IStateMachine(Interface):
    def add_transition(transition_id, from_state, to_state, callback, **kw):
        """Add a transition to the FSM."""

    def execute(context, transition_id, guards=()):
        """Perform a transition and execute an action.  If there are
        any guards, try running them before doing the transition; a
        guard should be a callable that accepts a (context,
        transition) pair and should raise an exception if a
        condition is not met"""

    def state_of(context):
        """ Return the current state of the given object """

    def transitions(context, from_state=None):
        """ Return the available transition dictionaries for the given
        object (from_state defaults to the object's current state)"""

