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

    def _makeOne(self, *arg):
        return self._getTargetClass()(*arg)

    def test_class_conforms_to_IWorkflow(self):
        from zope.interface.verify import verifyClass
        from repoze.workflow.interfaces import IWorkflow
        verifyClass(IWorkflow, self._getTargetClass())

    def test_instance_conforms_to_IWorkflow(self):
        from zope.interface.verify import verifyObject
        from repoze.workflow.interfaces import IWorkflow
        verifyObject(IWorkflow, self._makeOne())

    def test_state_of_None(self):
        workflow = self._makeOne()
        self.assertEqual(workflow.state_of(None), None)

    def test_state_of_something(self):
        workflow = self._makeOne()
        class Dummy:
            state = 'true'
        self.assertEqual(workflow.state_of(Dummy), 'true')

    def test_initialize(self):
        workflow = self._makeOne()
        state = workflow.initialize(None)
        self.assertEqual(workflow.initialized, [None])
        self.assertEqual(state, 'initial')

    def test_transition(self):
        workflow = self._makeOne()
        workflow.transition(None, None, None)
        self.assertEqual(workflow.executed, [{'content':None,
                                              'context':None,
                                              'request':None,
                                              'name':None,
                                              'guards':()}])

    def test_get_transitions(self):
        workflow = self._makeOne((), 'a')
        self.assertEqual(workflow.get_transitions(None, None), 'a')
        
    def test_state_info(self):
        workflow = self._makeOne('a')
        self.assertEqual(workflow.state_info(None, None), 'a')
        
    def test_transition_to_state(self):
        workflow = self._makeOne()
        workflow.transition_to_state(None, None, None)
        self.assertEqual(workflow.transitioned,
                         [{'guards': (),
                           'to_state': None,
                           'request': None,
                           'content': None,
                           'context': None,
                           'skip_same': True}])

    def test_reset(self):
        workflow = self._makeOne()
        state, msg = workflow.reset(None)
        self.assertEqual(workflow.resetted, [None])
        self.assertEqual(state, 'initial')
        self.assertEqual(msg, None)
        
    def test_has_state_false(self):
        workflow = self._makeOne()
        self.assertEqual(workflow.has_state(None), False)
        
    def test_has_state_true(self):
        workflow = self._makeOne()
        class Dummy:
            state = 'hello'
        self.assertEqual(workflow.has_state(Dummy), True)

    def test_check(self):
        workflow = self._makeOne()
        self.assertEqual(workflow.check(), True)

    def test_add_transition(self):
        workflow = self._makeOne()
        workflow.add_transition('name', 'from_state', 'to_state')
        self.assertEqual(len(workflow.transitions_added), 1)
        added = workflow.transitions_added[0]
        self.assertEqual(added['name'], 'name')
        
    def test_add_state(self):
        workflow = self._makeOne()
        workflow.add_state('name')
        self.assertEqual(len(workflow.states_added), 1)
        added = workflow.states_added[0]
        self.assertEqual(added['name'], 'name')
        
        
        
        
        
        
