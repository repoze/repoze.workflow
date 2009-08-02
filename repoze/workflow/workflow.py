from repoze.workflow.interfaces import IWorkflow
from repoze.workflow.interfaces import IWorkflowFactory
from repoze.workflow.interfaces import IWorkflowList
from repoze.workflow.interfaces import IDefaultWorkflow

from zope.interface import implements
from zope.interface import classImplements
from zope.component import getSiteManager

_marker = object()

class WorkflowError(Exception):
    """ Invalid input to finite state machine"""

class Workflow(object):
    """ Finite state machine featuring transition actions.
    """
    classImplements(IWorkflowFactory)
    implements(IWorkflow)
    
    def __init__(self, state_attr, initial_state, permission_checker=None,
                 name='', description=''):
        """
        o state_attr - attribute name where a given object's current
                       state will be stored (object is responsible for
                       persisting)
                       
        """
        self._transition_data = {}
        self._transition_order = []
        self._state_data = {}
        self._state_order = []
        self._state_aliases = {}
        self.state_attr = state_attr
        self.initial_state = initial_state
        self.permission_checker = permission_checker
        self.name = name
        self.description = description

    def __call__(self, context):
        return self # allow ourselves to act as an adapter

    def add_state(self, state_name, callback=None, aliases=(), **kw):
        """ Add a state to the FSM.  ``**kw`` must not contain the key
        ``callback``.  This name is reserved for internal use."""
        if state_name in self._state_order:
            raise WorkflowError('State %s already defined' % state_name)
        if state_name in self._state_aliases:
            raise WorkflowError('State %s already aliased' % state_name)
        kw['callback'] = callback
        self._state_data[state_name] = kw
        self._state_order.append(state_name)
        for alias in aliases:
            self._state_aliases[alias] = state_name

    def add_transition(self, transition_name, from_state, to_state,
                       callback=None, permission=None, **kw):
        """ Add a transition to the FSM.  ``**kw`` must not contain
        any of the keys ``from_state``, ``name``, ``to_state``, or
        ``callback``; these are reserved for internal use."""
        if transition_name in self._transition_order:
            raise WorkflowError('Duplicate transition name %s' %
                                    transition_name)
        if not from_state in self._state_order:
            raise WorkflowError('No such state %r' % from_state)
        if not to_state in self._state_order:
            raise WorkflowError('No such state %r' % to_state)
        if permission is not None and self.permission_checker is None:
            raise WorkflowError(
                'Permission %r defined without permission checker on '
                'workflow' % permission)
        transition = kw
        transition['name'] = transition_name
        transition['from_state'] = from_state
        transition['to_state'] = to_state
        transition['callback'] = callback
        transition['permission'] = permission
        self._transition_data[transition_name] = transition
        self._transition_order.append(transition_name)

    def check(self):
        if not self.initial_state in self._state_order:
            raise WorkflowError('Workflow must define its initial state %r'
                                % self.initial_state)

    def _transition(self, context, transition_name, guards=()):
        """ Execute a transition via a transition name """
        state = self.state_of(context)

        si = (state, transition_name)

        transition = None
        for tname in self._transition_order:
            t = self._transition_data[tname]
            match = (t['from_state'], t['name'])
            if si == match:
                transition = t
                break

        if transition is None:
            raise WorkflowError(
                'No transition from %r using transition name %r'
                % (state, transition_name))

        if guards:
            for guard in guards:
                guard(context, transition)

        from_state = transition['from_state']
        to_state = transition['to_state']

        transition_callback = transition['callback']
        if transition_callback is not None:
            transition_callback(context, transition)

        state_callback = self._state_data[to_state]['callback']
        if state_callback is not None:
            state_callback(context, transition)

        setattr(context, self.state_attr, to_state)

    def _state_of(self, context):
        state = getattr(context, self.state_attr, None)
        state_name = self._state_aliases.get(state, state)
        return state_name

    def state_of(self, context):
        if context is None: # for add forms
            return self.initial_state
        state = self._state_of(context)
        if state is None:
            state = self.initialize(context)
        return state

    def has_state(self, context):
        return self._state_of(context) is not None

    def _get_transitions(self, context, from_state=None):
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
                    self._transition(context, transition['name'], guards)
                    return
        raise WorkflowError('No transition from state %r to state %r'
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

    def state_info(self, context, request, from_state=None):
        states = self._state_info(context, from_state)
        for state in states:
            L = []
            for transition in state['transitions']:
                permission = transition.get('permission')
                if permission is not None:
                    if not self.permission_checker(permission, context,request):
                        continue
                L.append(transition)
            state['transitions'] = L
        return states

    def initialize(self, context):
        callback = self._state_data[self.initial_state]['callback']
        if callback is not None:
            callback(context, {})
        setattr(context, self.state_attr, self.initial_state)
        return self.initial_state

    def reset(self, context):
        state = self._state_of(context)
        if state is None:
            self.initialize(context)
            return self.initial_state
        else:
            callback = self._state_data[state]['callback']
            callback(context, {})
            setattr(context, self.state_attr, state)
            return getattr(context, self.state_attr)

    def transition(self, context, request, transition_name, guards=()):
        if self.permission_checker:
            guards = list(guards)
            permission_guard = PermissionGuard(request, transition_name,
                                               self.permission_checker)
            guards.append(permission_guard)
        self._transition(context, transition_name, guards=guards)

    def transition_to_state(self, context, request, to_state, guards=()):
        if self.permission_checker:
            guards = list(guards)
            permission_guard = PermissionGuard(request, to_state,
                                               self.permission_checker)
            guards.append(permission_guard)
        self._transition_to_state(context, to_state, guards=guards)

    def get_transitions(self, context, request, from_state=None):
        transitions = self._get_transitions(context, from_state)
        L = []
        for transition in transitions:
            permission = transition.get('permission')
            if permission is not None:
                if self.permission_checker:
                    if not self.permission_checker(permission, context,request):
                        continue
            L.append(transition)
        return L

class PermissionGuard:
    def __init__(self, request, name, checker):
        self.request = request
        self.name = name
        self.checker = checker

    def __call__(self, context, transition):
        permission = transition.get('permission')
        if self.request is not None and permission is not None:
            if not self.checker(permission, context, self.request):
                raise WorkflowError(
                    '%s permission required for transition using %r' % (
                    permission, self.name)
                    )
                    
def process_wf_list(wf_list, context):
    fallback = None
    for wf_def in wf_list:
        elector = wf_def['elector']
        workflow = wf_def['workflow']
        if elector is None:
            fallback = workflow
        elif context is not None:
            if elector(context):
                return workflow
    return fallback

def get_workflow(content_type, type, context=None,
                 process_wf_list=process_wf_list): # process_wf_list is for test
    """ Return a workflow based on a content_type, the workflow type,
    and (optionally) a context.  The context is used as an argument to
    electors for placeful workflows."""
    sm = getSiteManager()
    look = sm.adapters.lookup

    if content_type not in (None, IDefaultWorkflow):
        wf_list = look((content_type,), IWorkflowList, name=type, default=None)
        if wf_list is not None:
            wf = process_wf_list(wf_list, context)
            if wf is not None:
                return wf

    wf_list = look((IDefaultWorkflow,), IWorkflowList, name=type, default=None)
    if wf_list is not None:
        return process_wf_list(wf_list, context)

