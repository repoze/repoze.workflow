import unittest
from repoze.bfg import testing

class TestWorkflowDirective(unittest.TestCase):
    def setUp(self):
        testing.cleanUp()

    def tearDown(self):
        testing.cleanUp()

    def _getTargetClass(self):
        from repoze.bfg.workflow.zcml import WorkflowDirective
        return WorkflowDirective

    def _makeOne(self, context=None, name=None, for_=None, initial_state=None,
                 state_attr=None, class_=None):
        if context is None:
            context = DummyContext()
        return self._getTargetClass()(context, name, for_, initial_state,
                                      state_attr, class_)

    def test_ctor_with_state_attr(self):
        ctor = self._makeOne(name='public', state_attr='public2')
        self.assertEqual(ctor.state_attr, 'public2')
        
    def test_ctor_no_state_attr(self):
        ctor = self._makeOne(name='public')
        self.assertEqual(ctor.state_attr, 'public')

    def test_ctor_with_class_(self):
        ctor = self._makeOne(name='public', class_='class')
        self.assertEqual(ctor.class_, 'class')
        
    def test_ctor_no_class_(self):
        from repoze.bfg.workflow.workflow import Workflow
        ctor = self._makeOne(name='public')
        self.assertEqual(ctor.class_, Workflow)

    def test_after(self):
        machine = self._makeOne()
        machine.states = [ DummyState('s1', a=1), DummyState('s2', b=2) ]
        machine.transitions = [ DummyTransition('make_public'),
                                DummyTransition('make_private'),
                                ]
        machine.after()

class DummyContext:
    info = None
    def __init__(self):
        self.actions = []

class DummyState:
    def __init__(self, name, **extras):
        self.name = name
        self.extras = extras
        
class DummyTransition:
    def __init__(self, name, from_state='private', to_state='public',
                 callback=None, **extras):
        self.name = name
        self.from_state = from_state
        self.to_state = to_state
        self.callback = callback
        self.extras = extras

                  
