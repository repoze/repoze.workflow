from zope.interface import implements

from repoze.workflow.zcml import register_workflow
from repoze.workflow.interfaces import IWorkflow

def registerDummyWorkflow(name, workflow=None, content_type=None, elector=None):
    if workflow is None:
        workflow = DummyWorkflow()
    register_workflow(workflow, name, content_type, elector)

    return workflow

class DummyWorkflow:
    state_attr = 'state'
    initial_state = 'initial'
    name = 'the workflow'
    description = ''
    implements(IWorkflow)
    def __init__(self, state_info=(), transitions=()):
        self.executed = []
        self.transitioned = []
        self.initialized = []
        self.states_added = []
        self.transitions_added = []
        self.resetted = []
        self._state_info = state_info
        self._transitions = transitions

    def add_state(self, name, callback=None, **kw):
        self.states_added.append({'name':name,
                                  'callback':callback,
                                  'extra':kw})

    def add_transition(self, name, from_state, to_state, callback=None, **kw):
        self.transitions_added.append({'name':name,
                                       'from_state':from_state,
                                       'to_state':to_state,
                                       'callback':callback,
                                       'extra':kw})

    def check(self):
        return True

    def state_of(self, content):
        return getattr(content, self.state_attr, None)

    def has_state(self, content):
        return hasattr(content, self.state_attr)

    def state_info(self, content, request, context=None, from_state=None):
        return self._state_info

    def initialize(self, content):
        self.initialized.append(content)
        return self.initial_state

    def reset(self, content):
        self.resetted.append(content)
        return self.initial_state, None

    def transition(self, content, request, transition_name, context=None,
                   guards=()):
        self.executed.append({'content':content, 'name':transition_name,
                              'guards':guards, 'request':request,
                              'context':context})

    def transition_to_state(self, content, request, to_state, context=None,
                            guards=(), skip_same=True):
        self.transitioned.append({'to_state':to_state, 'content':content,
                                  'request':request, 'guards':guards,
                                  'context':context, 'skip_same':skip_same})

    def get_transitions(self, content, request, context=None, from_state=None):
        return self._transitions
        

    
