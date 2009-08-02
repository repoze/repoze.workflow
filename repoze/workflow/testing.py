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
    def __init__(self):
        self.executed = []
        self.transitioned = []
        self.initialized = []
        self.states_added = []
        self.transitions_added = []
        self.resetted = []

    def has_state(self, content):
        return True
        
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

    def state_of(self, context):
        return 'state'

    def initialize(self, context):
        self.initialized.append(context)
        return self.initial_state

    def reset(self, context):
        self.resetted.append(context)
        return self.initial_state

    def transition(self, context, request, transition_name, guards=()):
        self.executed.append({'context':context, 'name':transition_name,
                              'guards':guards, 'request':request})

    def transition_to_state(self, context, request, to_state, guards=()):
        self.transitioned.append({'to_state':to_state, 'context':context,
                                  'request':request, 'guards':guards})

    def get_transitions(self, context, request, from_state=None):
        return []

    def state_info(self, context, request, from_state=None):
        return []


    
