from repoze.bfg.workflow.zcml import register_workflow

def registerDummyWorkflow(name, workflow=None, content_type=None,
                          container_type=None):
    if workflow is None:
        workflow = DummyWorkflow()
    register_workflow(workflow, name, content_type, container_type)

    return workflow

class DummyWorkflow:
    state_attr = 'state'
    initial_state = 'initial'
    def __init__(self):
        self.executed = []
        self.transitioned = []
        self.initialized = []

    def state_of(self, context):
        return 'state'

    def initialize(self, context):
        self.initialized.append(context)

    def execute(self, context, request, transition_name, guards=()):
        self.executed.append({'context':context, 'name':transition_name,
                              'guards':guards, 'request':request})

    def transitions(self, context, request, from_state=None):
        return []

    def state_info(self, context, request, from_state=None):
        return []

    def transition_to_state(self, context, request, to_state):
        self.transitioned.append({'to_state':to_state, 'context':context,
                                  'request':request})

    
