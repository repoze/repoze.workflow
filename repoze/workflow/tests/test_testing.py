import unittest

class TestRegisterDummyWorkflow(unittest.TestCase):
    def _callFUT(self, name, workflow=None):
        from repoze.workflow.testing import registerDummyWorkflow
        return registerDummyWorkflow(name, workflow)

    def test_it_default_workflow(self):
        workflow = self._callFUT('workflow')
        self.assertEqual(workflow.state_attr, 'state')

    def test_it_custom_workflow(self):
        class Dummy: pass
        dummy = Dummy()
        workflow = self._callFUT('workflow', dummy)
        self.assertEqual(workflow, dummy)

class TestDummyWorkflow(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.workflow.testing import DummyWorkflow
        return DummyWorkflow

    def _makeOne(self):
        return self._getTargetClass()()

    def test_class_conforms_to_IWorkflow(self):
        from zope.interface.verify import verifyClass
        from repoze.workflow.interfaces import IWorkflow
        verifyClass(IWorkflow, self._getTargetClass())

    def test_instance_conforms_to_IWorkflow(self):
        from zope.interface.verify import verifyObject
        from repoze.workflow.interfaces import IWorkflow
        verifyObject(IWorkflow, self._makeOne())

    def test_state_of(self):
        workflow = self._makeOne()
        self.assertEqual(workflow.state_of(None), 'state')

    def test_initialize(self):
        workflow = self._makeOne()
        workflow.initialize(None)
        self.assertEqual(workflow.initialized, [None])

    def test_transition(self):
        workflow = self._makeOne()
        workflow.transition(None, None, None)
        self.assertEqual(workflow.executed, [{'context':None,
                                              'request':None,
                                              'name':None,
                                              'guards':()}])

    def test_get_transitions(self):
        workflow = self._makeOne()
        self.assertEqual(workflow.get_transitions(None, None), [])
        
    def state_info(self):
        workflow = self._makeOne()
        self.assertEqual(workflow.state_info(None, None), [])
        
    def transition_to_state(self):
        workflow = self._makeOne()
        workflow.transition_to_state(None, None, None)
        self.assertEqual(workflow.transitioned, [{'context':None,
                                                  'to_state':None,
                                                  'request':None}])

    def test_reset(self):
        workflow = self._makeOne()
        workflow.reset(None)
        self.assertEqual(workflow.resetted, [None])
        
        
        
        
        
