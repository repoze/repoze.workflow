from zope.interface import implements
from zope.interface import classImplements

from repoze.bfg.security import has_permission
from repoze.bfg.workflow.statemachine import StateMachineError
from repoze.bfg.workflow.interfaces import IWorkflow
from repoze.bfg.workflow.interfaces import IWorkflowFactory

class Workflow:
    classImplements(IWorkflowFactory)
    implements(IWorkflow)
    def __init__(self, context, machine):
        self.context = context
        self.machine = machine # r.b.workflow.statemachine.StateMachine instance

    def execute(self, request, transition_name):
        def permission_guard(context, transition):
            permission = transition.get('permission')
            if request is not None and permission is not None:
                if not has_permission(permission, context, request):
                    raise StateMachineError(
                        '%s permission required for transition %r' % (
                        permission, transition_name)
                        )
        self.machine.execute(self.context, transition_name,
                             guards=(permission_guard,))

    def transitions(self, request, from_state=None):
        transitions = self.machine.transitions(self.context, from_state)
        L = []
        for transition in transitions:
            if 'permission' in transition:
                if not has_permission(transition['permission'],
                                      self.context, request):
                    continue
            L.append(transition)
        return L

    def state_info(self, request, from_state=None):
        states = self.machine.state_info(self.context, from_state)
        for state in states:
            L = []
            for transition in state['transitions']:
                if 'permission' in transition:
                    if not has_permission(transition['permission'],
                                          self.context, request):
                        continue
                L.append(transition)
            state['transitions'] = L
        return states
    
            
            
