import unittest
from repoze.bfg import testing

class TestWorkflow(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.bfg.workflow.workflow import Workflow
        return Workflow

    def _makeOne(self, context=None, machine=None):
        if context is None:
            context = DummyContext()
        if machine is None:
            machine = DummyMachine()
        return self._getTargetClass()(context, machine)
            
    def test_class_conforms_to_IWorkflow(self):
        from zope.interface.verify import verifyClass
        from repoze.bfg.workflow.interfaces import IWorkflow
        verifyClass(IWorkflow, self._getTargetClass())

    def test_instance_conforms_to_IWorkflow(self):
        from zope.interface.verify import verifyObject
        from repoze.bfg.workflow.interfaces import IWorkflow
        verifyObject(IWorkflow, self._makeOne())

    def test_execute_permissive(self):
        workflow = self._makeOne()
        testing.registerDummySecurityPolicy(permissive=True)
        request = testing.DummyRequest()
        workflow.execute(request, 'publish')
        machine = workflow.machine
        self.assertEqual(len(machine.executed), 1)
        executed = machine.executed[0]
        self.assertEqual(executed['context'], workflow.context)
        self.assertEqual(executed['transition_id'], 'publish')
        permitted = executed['guards'][0]
        result = permitted(None, {'permission':'view'})
        self.assertEqual(result, None)

    def test_execute_not_permissive(self):
        from repoze.bfg.workflow.statemachine import StateMachineError
        workflow = self._makeOne()
        testing.registerDummySecurityPolicy(permissive=False)
        request = testing.DummyRequest()
        workflow.execute(request, 'publish')
        machine = workflow.machine
        self.assertEqual(len(machine.executed), 1)
        executed = machine.executed[0]
        self.assertEqual(executed['context'], workflow.context)
        self.assertEqual(executed['transition_id'], 'publish')
        permitted = executed['guards'][0]
        self.assertRaises(StateMachineError, permitted, None,
                          {'permission':'view'})

    def test_execute_request_is_None(self):
        workflow = self._makeOne()
        testing.registerDummySecurityPolicy(permissive=False)
        workflow.execute(None, 'publish')
        machine = workflow.machine
        self.assertEqual(len(machine.executed), 1)
        executed = machine.executed[0]
        self.assertEqual(executed['context'], workflow.context)
        self.assertEqual(executed['transition_id'], 'publish')
        permitted = executed['guards'][0]
        result = permitted(None, {'permission':'view'})
        self.assertEqual(result, None)

    def test_execute_permission_is_None(self):
        workflow = self._makeOne()
        testing.registerDummySecurityPolicy(permissive=False)
        request = testing.DummyRequest()
        workflow.execute(request, 'publish')
        machine = workflow.machine
        self.assertEqual(len(machine.executed), 1)
        executed = machine.executed[0]
        self.assertEqual(executed['context'], workflow.context)
        self.assertEqual(executed['transition_id'], 'publish')
        permitted = executed['guards'][0]
        result = permitted(None, {})
        self.assertEqual(result, None)

    def test_transition_to_state_permissive(self):
        workflow = self._makeOne()
        testing.registerDummySecurityPolicy(permissive=True)
        request = testing.DummyRequest()
        workflow.transition_to_state(request, 'published')
        machine = workflow.machine
        self.assertEqual(len(machine.transitioned_to_state), 1)
        transitioned = machine.transitioned_to_state[0]
        self.assertEqual(transitioned['context'], workflow.context)
        self.assertEqual(transitioned['to_state'], 'published')
        permitted = transitioned['guards'][0]
        result = permitted(None, {'permission':'view'})
        self.assertEqual(result, None)

    def test_transition_to_state_not_permissive(self):
        from repoze.bfg.workflow.statemachine import StateMachineError
        workflow = self._makeOne()
        testing.registerDummySecurityPolicy(permissive=False)
        request = testing.DummyRequest()
        workflow.transition_to_state(request, 'published')
        machine = workflow.machine
        self.assertEqual(len(machine.transitioned_to_state), 1)
        transitioned = machine.transitioned_to_state[0]
        self.assertEqual(transitioned['context'], workflow.context)
        self.assertEqual(transitioned['to_state'], 'published')
        permitted = transitioned['guards'][0]
        self.assertRaises(StateMachineError, permitted, None,
                          {'permission':'view'})

    def test_transition_to_state_request_is_None(self):
        workflow = self._makeOne()
        testing.registerDummySecurityPolicy(permissive=False)
        workflow.transition_to_state(None, 'published')
        machine = workflow.machine
        self.assertEqual(len(machine.transitioned_to_state), 1)
        transitioned = machine.transitioned_to_state[0]
        self.assertEqual(transitioned['context'], workflow.context)
        self.assertEqual(transitioned['to_state'], 'published')
        permitted = transitioned['guards'][0]
        result = permitted(None, {'permission':'view'})
        self.assertEqual(result, None)

    def test_transition_to_state_permission_is_None(self):
        workflow = self._makeOne()
        testing.registerDummySecurityPolicy(permissive=False)
        request = testing.DummyRequest()
        workflow.transition_to_state(request, 'published')
        machine = workflow.machine
        self.assertEqual(len(machine.transitioned_to_state), 1)
        transitioned = machine.transitioned_to_state[0]
        self.assertEqual(transitioned['context'], workflow.context)
        self.assertEqual(transitioned['to_state'], 'published')
        permitted = transitioned['guards'][0]
        result = permitted(None, {})
        self.assertEqual(result, None)

    def test_transitions_permissive(self):
        machine = DummyMachine([{'permission':'view'}, {}])
        workflow = self._makeOne(machine=machine)
        testing.registerDummySecurityPolicy(permissive=True)
        request = testing.DummyRequest()
        transitions = workflow.transitions(request, 'private')
        self.assertEqual(len(transitions), 2)

    def test_transitions_nonpermissive(self):
        machine = DummyMachine([{'permission':'view'}, {}])
        workflow = self._makeOne(machine=machine)
        testing.registerDummySecurityPolicy(permissive=False)
        request = testing.DummyRequest()
        transitions = workflow.transitions(request, 'private')
        self.assertEqual(len(transitions), 1)

    def test_state_info_permissive(self):
        state_info = []
        state_info.append({'transitions':[{'permission':'view'}, {}]})
        state_info.append({'transitions':[{'permission':'view'}, {}]})
        machine = DummyMachine(state_info=state_info)
        workflow = self._makeOne(machine=machine)
        request = testing.DummyRequest()
        testing.registerDummySecurityPolicy(permissive=True)
        result = workflow.state_info(request, 'whatever')
        self.assertEqual(result, state_info)

    def test_state_info_nonpermissive(self):
        state_info = []
        state_info.append({'transitions':[{'permission':'view'}, {}]})
        state_info.append({'transitions':[{'permission':'view'}, {}]})
        machine = DummyMachine(state_info=state_info)
        workflow = self._makeOne(machine=machine)
        request = testing.DummyRequest()
        testing.registerDummySecurityPolicy(permissive=False)
        result = workflow.state_info(request, 'whatever')
        self.assertEqual(result, [{'transitions': [{}]}, {'transitions': [{}]}])

    def test_initialize(self):
        machine = DummyMachine()
        workflow = self._makeOne(machine=machine)
        workflow.initialize()
        self.assertEqual(workflow.context.initialized, True)

    def test_initial_state(self):
        machine = DummyMachine(initial_state='public')
        workflow = self._makeOne(machine=machine)
        self.assertEqual(workflow.initial_state, 'public')
        
    def test_state_attr(self):
        machine = DummyMachine(state_attr='thestate')
        workflow = self._makeOne(machine=machine)
        self.assertEqual(workflow.state_attr, 'thestate')

    def test_state_of(self):
        machine = DummyMachine()
        workflow = self._makeOne(machine=machine)
        ob = DummyContext()
        self.assertEqual(workflow.state_of(ob), 'state')

class DummyContext:
    pass

class DummyMachine:
    def __init__(self, transitions=None, state_info=None, initial_state=None,
                 state_attr=None):
        if transitions is None:
            transitions = {}
        if state_info is None:
            state_info = []
        self._transitions = transitions
        self._state_info = state_info
        self.initial_state = initial_state
        self.state_attr = state_attr
        self.executed = []
        self.transitioned_to_state = []

    def execute(self, context, transition_id, guards=()):
        self.executed.append({'context':context,
                              'transition_id':transition_id,
                              'guards':guards})

    def transition_to_state(self, context, to_state, guards=()):
        self.transitioned_to_state.append({'context':context,
                                           'to_state':to_state,
                                           'guards':guards})

    def transitions(self, context, from_state=None):
        return self._transitions

    def state_info(self, context, from_state=None):
        return self._state_info

    def initialize(self, context):
        context.initialized = True

    def state_of(self, context):
        return 'state'
    
        
                              
