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

    def test_transitions_permissive(self):
        machine = DummyMachine([{'permission':'view'}])
        workflow = self._makeOne(machine=machine)
        testing.registerDummySecurityPolicy(permissive=True)
        request = testing.DummyRequest()
        transitions = workflow.transitions(request, 'private')
        self.assertEqual(len(transitions), 1)
        self.assertEqual(transitions[0]['permission'], 'view')

    def test_transitions_nonpermissive(self):
        machine = DummyMachine([{'permission':'view'}])
        workflow = self._makeOne(machine=machine)
        testing.registerDummySecurityPolicy(permissive=False)
        request = testing.DummyRequest()
        transitions = workflow.transitions(request, 'private')
        self.assertEqual(len(transitions), 0)

class DummyContext:
    pass

class DummyMachine:
    def __init__(self, transitions=None):
        self.executed = []
        if transitions is None:
            transitions = {}
        self._transitions = transitions

    def execute(self, context, transition_id, guards=()):
        self.executed.append({'context':context,
                              'transition_id':transition_id,
                              'guards':guards})

    def transitions(self, context, from_state=None):
        return self._transitions
    
        
                              
