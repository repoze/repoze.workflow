""" Finite state machine, useful for workflow-like features, based on
Skip Montanaro's FSM from
http://wiki.python.org/moin/FiniteStateMachine (ancient but simple #
and useful!)"""
from repoze.bfg.workflow.interfaces import IWorkflow
from repoze.bfg.workflow.interfaces import IWorkflowFactory
from repoze.bfg.workflow.interfaces import IWorkflowLookup
from repoze.bfg.workflow.interfaces import IDefaultWorkflow

from repoze.bfg.traversal import find_interface

from zope.interface import implements
from zope.interface import classImplements
from zope.component import getSiteManager

from repoze.bfg.security import has_permission

_marker = object()

class StateMachineError(Exception):
    """ Invalid input to finite state machine"""

class Workflow(object):
    """ Finite state machine featuring transition actions.

    The class stores a sequence of transition dictionaries.

    When a (state, transition_name) search is performed via ``execute``:

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
    classImplements(IWorkflowFactory)
    implements(IWorkflow)
    
    def __init__(self, state_attr, initial_state=None, initializer=None):
        """
        o state_attr - attribute name where a given object's current
                       state will be stored (object is responsible for
                       persisting)
                       
        o transitions - initial list of transition dictionaries

        o initial_state - initial state for any object using this
                          state machine

        o initializer - callback function that accepts a context
          to initialize a context object to the initial state
        """
        self._transition_data = {}
        self._transition_order = []
        self._state_data = {}
        self._state_order = []
        self.state_attr = state_attr
        self.initializer = initializer
        self.initial_state = initial_state

    def __call__(self, context):
        return self # allow ourselves to act as an adapter

    def add_state_info(self, state_name, **kw):
        if not state_name in self._state_order:
            self._state_order.append(state_name)
        if not state_name in self._state_data:
            self._state_data[state_name] = {}
        self._state_data[state_name].update(kw)

    def add_transition(self, transition_name, from_state, to_state,
                       callback, **kw):
        """ Add a transition to the FSM.  ``**kw`` must not contain
        any of the keys ``from_state``, ``name``, ``to_state``, or
        ``callback``; these are reserved for internal use."""
        if transition_name in self._transition_order:
            raise StateMachineError('Duplicate transition name %s' %
                                    transition_name)
        if from_state is not None:
            self.add_state_info(from_state)
        if to_state is not None:
            self.add_state_info(to_state)
        transition = kw
        transition['name'] = transition_name
        transition['from_state'] = from_state
        transition['to_state'] = to_state
        transition['callback'] = callback
        self._transition_data[transition_name] = transition
        self._transition_order.append(transition_name)

    def _execute(self, context, transition_name, guards=()):
        """ Execute a transition """
        state = getattr(context, self.state_attr, _marker) 
        if state is _marker:
            state = None
        si = (state, transition_name)

        found = None
        for tname in self._transition_order:
            transition = self._transition_data[tname]
            match = (transition['from_state'], transition['name'])
            if si == match:
                found = transition
                break

        if found is None:
            raise StateMachineError(
                'No transition from %r using transition %r'
                % (state, transition_name))

        if guards:
            for guard in guards:
                guard(context, found)

        callback = found['callback']
        if callback is not None:
            callback(context, found)
        to_state = found['to_state']
        setattr(context, self.state_attr, to_state)

    def state_of(self, context):
        state = getattr(context, self.state_attr, None)
        return state

    def _transitions(self, context, from_state=None):
        if from_state is None:
            from_state = self.state_of(context)

        transitions = []
        for tname in self._transition_order:
            transition = self._transition_data[tname]
            if from_state == transition['from_state']:
                transitions.append(transition)
        
        return transitions

    def _transition_to_state(self, context, to_state, guards=(),
                             skip_same=True):
        from_state = self.state_of(context)
        if (from_state == to_state) and skip_same:
            return
        state_info = self._state_info(context)
        for info in state_info:
            if info['name'] == to_state:
                transitions = info['transitions']
                if transitions:
                    transition = transitions[0]
                    self._execute(context, transition['name'], guards)
                    return
        raise StateMachineError('No transition from state %r to state %r'
                % (from_state, to_state))

    def _state_info(self, context, from_state=None):
        context_state = self.state_of(context)
        if from_state is None:
            from_state = context_state

        L = []

        for state_name in self._state_order:
            D = {'name':state_name, 'transitions':[]}
            state_data = self._state_data[state_name]
            D['data'] = state_data
            D['initial'] = state_name == self.initial_state
            D['current'] = state_name == context_state
            title = state_data.get('title', state_name)
            D['title'] = title
            for tname in self._transition_order:
                transition = self._transition_data[tname]
                if (transition['from_state'] == from_state and
                    transition['to_state'] == state_name):
                    transitions = D['transitions']
                    transitions.append(transition)
            L.append(D)

        return L

    def initialize(self, context):
        transitions = []
        for tname in self._transition_order:
            transition = self._transition_data[tname]
            if  ( (transition['from_state'] == None) and
                  (transition['to_state'] == self.initial_state) ):
                transitions.append(transition)
        if transitions:
            self._execute(context, transitions[0]['name'])
        else:
            setattr(context, self.state_attr, self.initial_state)
            
    def execute(self, context, request, transition_name, guards=()):
        permission_guard = PermissionGuard(request, transition_name)
        guards = list(guards)
        guards.append(permission_guard)
        self._execute(context, transition_name, guards=guards)

    def transitions(self, context, request, from_state=None):
        transitions = self._transitions(context, from_state)
        L = []
        for transition in transitions:
            if 'permission' in transition:
                if not has_permission(transition['permission'],
                                      context, request):
                    continue
            L.append(transition)
        return L

    def state_info(self, context, request, from_state=None):
        states = self._state_info(context, from_state)
        for state in states:
            L = []
            for transition in state['transitions']:
                if 'permission' in transition:
                    if not has_permission(transition['permission'],
                                          context, request):
                        continue
                L.append(transition)
            state['transitions'] = L
        return states

    def transition_to_state(self, context, request, to_state):
        permission_guard = PermissionGuard(request, to_state)
        self._transition_to_state(context, to_state,
                                  guards=(permission_guard,))

class PermissionGuard:
    def __init__(self, request, name):
        self.request = request
        self.name = name

    def __call__(self, context, transition):
        permission = transition.get('permission')
        if self.request is not None and permission is not None:
            if not has_permission(permission, context, self.request):
                raise StateMachineError(
                    '%s permission required for transition using %r' % (
                    permission, self.name)
                    )
                    
def get_workflow(content_type, name, context=None):
    """ Return a workflow based on a content_type, the workflow name,
    and (optionally) a context.  The context is used as a starting
    point to find a container type for placeful workflows."""
    sm = getSiteManager()
    if content_type is None:
        content_type = IDefaultWorkflow
    wf_list = sm.adapters.lookup((content_type,), IWorkflowLookup, name=name,
                                 default=None)
    if wf_list is None:
        return None

    fallback = None

    for wf_def in wf_list:
        container_type = wf_def['container_type']
        workflow = wf_def['workflow']
        if container_type is None:
            fallback = workflow
        elif context is not None:
            if find_interface(context, container_type):
                return workflow

    return fallback
            
