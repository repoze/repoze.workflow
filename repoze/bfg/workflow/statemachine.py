""" Finite state machine, useful for workflow-like features, based on
Skip Montanaro's FSM from
http://wiki.python.org/moin/FiniteStateMachine (ancient but simple #
and useful!)"""
from repoze.bfg.workflow.interfaces import IStateMachine
from zope.interface import implements

_marker = object()

class StateMachineError(Exception):
    """ Invalid input to finite state machine"""

class StateMachine(object):
    """ Finite state machine featuring transition actions.

    The class stores a sequence of transition dictionaries.

    When a (state, transition_id) search is performed via ``execute``:

      * an exact match is checked first,
      * (state, None) is checked next.

    The callback must be of the following form:
    * callback(context, transition_info)

    ``transition_info`` passed to the transition funciton is a
    dictionary containing transition information.

    It is recommended that all transition functions be module level
    callables to facilitate issues related to StateMachine
    persistence.
    """
    implements(IStateMachine)
    
    def __init__(self, state_attr, transitions=None, initial_state=None):
        """
        o state_attr - attribute name where a given object's current
                       state will be stored (object is responsible for
                       persisting)
                       
        o transitions - initial list of transition dictionaries

        o initial_state - initial state for any object using this
                          state machine
        """
        if transitions is None:
            transitions = []
        self._transitions = transitions
        self._states = {}
        self.state_attr = state_attr
        self.initial_state = initial_state

    def add_state_info(self, state_id, **kw):
        if not state_id in self._states:
            self._states[state_id] = {}
        self._states[state_id].update(kw)

    def add_transition(self, transition_id, from_state, to_state,
                       callback, **kw):
        """ Add a transition to the FSM.  ``**kw`` must not contain
        any of the keys ``from_state``, ``id``, ``to_state``, or
        ``callback``; these are reserved for internal use."""
        if not from_state in self._states:
            self._states[from_state] = {}
        if not to_state in self._states:
            self._states[to_state] = {}
        transition = kw
        transition['id'] = transition_id
        transition['from_state'] = from_state
        transition['to_state'] = to_state
        transition['callback'] = callback
        self._transitions.append(transition)

    def execute(self, context, transition_id, guards=()):
        """ Execute a transition """
        state = getattr(context, self.state_attr, _marker) 
        if state is _marker:
            state = self.initial_state
        si = (state, transition_id)

        found = None
        for transition in self._transitions:
            match = (transition['from_state'], transition['id'])
            if match == si:
                found = transition
                break

        if found is None:
            raise StateMachineError(
                'No transition from %r using transition %r'
                % (state, transition_id))

        if guards:
            for guard in guards:
                guard(context, found)

        callback = found['callback']
        if callback is not None:
            callback(context, found)
        to_state = found['to_state']
        setattr(context, self.state_attr, to_state)

    def state_of(self, context):
        state = getattr(context, self.state_attr, self.initial_state)
        return state

    def transitions(self, context, from_state=None):
        if from_state is None:
            from_state = self.state_of(context)
        transitions = [transition for transition in self._transitions
                       if from_state == transition['from_state']]
        return transitions

