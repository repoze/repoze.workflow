# NB! Note that this module only serves as a backwards compatibility
# shim.  Neither the "workflow" module nor any of the ZCML
# configuration uses it; it represents an earlier version in the
# evolution of this software.

from repoze.workflow.interfaces import IStateMachine
from zope.interface import implements

_marker = ()

class StateMachineError(Exception):
    """ Invalid input to finite state machine"""

class StateMachine(object):
    """ Finite state machine featuring transition actions.

    The class stores a dictionary of (from_state, transition_id) keys, and
    (to_state, transition_fn) values.

    When a (state, transition_id) search is performed:
    * an exact match is checked first,
    * (state, None) is checked next.

    The transition function must be of the following form:
    * function(current_state, new_state, transition_id, context, **kw)

    It is recommended that all transition functions be module level
    callables to facilitate issues related to StateMachine
    persistence.
    """
    implements(IStateMachine)
    
    def __init__(self, state_attr, states=None, initial_state=None):
        """
        o state_attr - attribute name where a given object's current
                       state will be stored (object is responsible for
                       persisting)
                       
        o states - state dictionary

        o initial_state - initial state for any object using this
                          state machine
        """
        if states is None:
            states = {}
        self.states = states
        self.state_attr = state_attr
        self.initial_state = initial_state

    def add(self, state, transition_id, newstate, transition_fn, **kw):
        self.states[(state, transition_id)] = (newstate, transition_fn, kw)

    def execute(self, context, transition_id):
        state = getattr(context, self.state_attr, _marker) 
        if state is _marker:
            state = self.initial_state
        si = (state, transition_id)
        sn = (state, None)
        newstate = None
        # exact state match?
        if si in self.states:
            newstate, transition_fn, kw = self.states[si]
        # no exact match, how about a None (catch-all) match?
        elif sn in self.states:
            newstate, transition_fn, kw = self.states[sn]
        if newstate is None:
            raise StateMachineError(
                'No transition from %r using transition %r'
                    % (state, transition_id))
        self.before_transition(state, newstate, transition_id, context, **kw)
        transition_fn(state, newstate, transition_id, context, **kw)
        self.after_transition(state, newstate, transition_id, context, **kw)
        setattr(context, self.state_attr, newstate)

    def state_of(self, context):
        state = getattr(context, self.state_attr, self.initial_state)
        return state

    def transitions(self, context, from_state=None):
        if from_state is None:
            from_state = self.state_of(context)
        transitions = [t_id for (state, t_id) in self.states.keys()
                       if state == from_state]
        return transitions

    def transition_info(self, context, from_state=None):
        if from_state is None:
            from_state = self.state_of(context)
        L = []
        for (state,t_id), (newstate,transition_fn,kw) in self.states.items():
            if state == from_state:
                newkw = {}
                newkw.update(kw)
                newkw['transition_id'] = t_id
                newkw['from_state'] = state
                newkw['to_state'] = newstate
                L.append(newkw)
        return L

    def before_transition(self, state, newstate, transition_id, context, **kw):
        pass

    def after_transition(self, state, newstate, transition_id, context, **kw):
        pass
