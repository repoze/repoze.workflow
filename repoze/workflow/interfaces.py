from zope.interface import Interface

class IStateMachine(Interface):
    def add(state, transition_id, newstate, transition_fn, **kw):
        """Add a transition to the FSM."""

    def execute(context, transition_id):
        """Perform a transition and execute an action."""

    def state_of(context):
        """ Return the current state of the given object """

    def transitions(context, from_state=None):
        """ Return the available transition ids for the given object
        (from_state defaults to the object's current state)"""

    def transition_info(context, from_state=None):
        """ Return sequence of dictionaries representing the
        transition information for context (from_state defaults to the
        object's current state).  Each dictionary has the keys
        ``transition_id``, ``from_state``, ``to_state`` as well as any
        keywords passed in to the ``add`` method for this transition."""
    
    def before_transition(state, newstate, transition_id, context, **kw):
        """
        Hook method to be overridden by subclasses (or injected
        directly onto an instance) to allow for before transition
        actions (such as firing an event).

        Raise an exception here to abort the transition.
        """

    def after_transition(state, newstate, transition_id, context, **kw):
        """
        Hook method to be overridden by subclasses (or injected
        directly onto an instance) to allow for after transition
        actions (such as firing an event).
        """
        
