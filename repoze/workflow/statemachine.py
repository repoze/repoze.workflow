""" Finite state machine, useful for workflow-like features, based on
Skip Montanaro's FSM from
http://wiki.python.org/moin/FiniteStateMachine (ancient but simple #
and useful!)"""

from persistent import Persistent

_marker = ()

class StateMachineError(Exception):
    """ Invalid input to finite state machine"""

class StateMachine(Persistent):
    """ Persistent finite state machine featuring transition actions.

    The class stores a dictionary of (state, transition_id) keys, and
    (state, transition_fn) values.

    When a (state, transition_id) search is performed:
    * an exact match is checked first,
    * (state, None) is checked next.

    The transition function must be of the following form:
    * function(current_state, new_state, transition_id, context)
    """

    def __init__(self, state_attr, initial_state=None):
        self.states = {}
        self.state_attr = state_attr
        self.initial_state = initial_state

    def add(self, state, transition_id, newstate, transition_fn):
        """Add a transition to the FSM."""
        self.states[(state, transition_id)] = (newstate, transition_fn)
        self._p_changed = True

    def execute(self, context, transition_id):
        """Perform a transition and execute an action."""
        state = getattr(context, self.state_attr, _marker) 
        if state is _marker:
            state = self.initial_state
        si = (state, transition_id)
        sn = (state, None)
        newstate = None
        # exact state match?
        if si in self.states:
            newstate, transition_fn = self.states[si]
        # no exact match, how about a None (catch-all) match?
        elif sn in self.states:
            newstate, transition_fn = self.states[sn]
        if newstate is None:
            raise StateMachineError(
                'No transition from %r using transition %r' % (state, transition_id))
        transition_fn(state, newstate, transition_id, context)
        setattr(context, self.state_attr, newstate)

    def state_of(self, context):
        state = getattr(context, self.state_attr, self.initial_state)
        return state

    def transitions(self, context, from_state=None):
        if from_state is None:
            from_state = self.state_of(context)
        transitions = [t_id for (state, t_id) in self.states.keys()
                       if state == from_state and t_id is not None]
        return transitions

    def before_transition(self):
        """
        Hook method to be overridden by subclasses (or injected
        directly onto an instance) to allow for before transition
        actions (such as firing an event).
        """
        pass

    def after_transition(self):
        """
        Hook method to be overridden by subclasses (or injected
        directly onto an instance) to allow for after transition
        actions (such as firing an event).
        """
        pass
