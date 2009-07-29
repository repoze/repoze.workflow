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

    def _makeOne(self, context=None, initial_state=None, name=None,
                 state_attr=None, content_type=None):
        if context is None:
            context = DummyContext()
        return self._getTargetClass()(context, initial_state, name, state_attr,
                                      content_type)

    def test_ctor_with_state_attr(self):
        workflow = self._makeOne(name='public', state_attr='public2')
        self.assertEqual(workflow.state_attr, 'public2')
        
    def test_ctor_no_state_attr(self):
        workflow = self._makeOne(name='public')
        self.assertEqual(workflow.state_attr, 'public')

    def test_after(self):
        import types
        from zope.interface import Interface
        from zope.component import getSiteManager
        from zope.component import getUtility
        from repoze.bfg.workflow.interfaces import IWorkflow
        from repoze.bfg.workflow.workflow import Workflow
        from repoze.bfg.workflow.workflow import IWorkflowLookup
        class IDummy(Interface):
            pass
        directive = self._makeOne(initial_state='public',
                                  content_type=IDummy)
        directive.states = [ DummyState('s1', a=1), DummyState('s2', b=2) ]
        directive.transitions = [ DummyTransition('make_public'),
                                  DummyTransition('make_private'),
                                  ]
        directive.after()
        actions = directive.context.actions
        self.assertEqual(len(actions), 1)
        action = actions[0]
        self.assertEqual(action[0], (IWorkflow, IDummy, None, ''))
        callback = action[1]
        self.assertEqual(type(callback), types.FunctionType)
        callback()
        sm = getSiteManager()
        wflist = sm.adapters.lookup((IDummy,), IWorkflowLookup, name="")
        self.assertEqual(len(wflist), 1)
        wf_dict = wflist[0]
        self.assertEqual(wf_dict['container_type'], None)
        self.assertEqual(wf_dict['workflow'].__class__, Workflow)
        workflow = wf_dict['workflow']
        self.assertEqual(
            workflow._transition_data,
            {'make_public':
             {'from_state': 'private', 'callback': None,
              'name': 'make_public', 'to_state': 'public'},
             'make_private':
             {'from_state': 'private', 'callback': None,
              'name': 'make_private', 'to_state': 'public'},
             }
            )
        self.assertEqual(workflow.initial_state, 'public')
        

class TestTransitionDirective(unittest.TestCase):
    def setUp(self):
        testing.cleanUp()

    def tearDown(self):
        testing.cleanUp()

    def _getTargetClass(self):
        from repoze.bfg.workflow.zcml import TransitionDirective
        return TransitionDirective

    def _makeOne(self, context=None, name=None, callback=None, from_state=None,
                 to_state=None, permission=None):
        return self._getTargetClass()(context, name, callback, from_state,
                                      to_state, permission)

    def test_ctor(self):
        directive = self._makeOne('context', 'name', 'callback', 'from_state',
                                  'to_state', 'permission')
        self.assertEqual(directive.context, 'context')
        self.assertEqual(directive.name, 'name')
        self.assertEqual(directive.callback, 'callback')
        self.assertEqual(directive.from_state, 'from_state')
        self.assertEqual(directive.to_state, 'to_state')
        self.assertEqual(directive.permission, 'permission')
        self.assertEqual(directive.extras, {})

    def test_ctor_no_from_state(self):
        directive = self._makeOne('context', 'name', 'callback', '',
                                  'to_state', 'permission')
        self.assertEqual(directive.context, 'context')
        self.assertEqual(directive.name, 'name')
        self.assertEqual(directive.callback, 'callback')
        self.assertEqual(directive.from_state, None)
        self.assertEqual(directive.to_state, 'to_state')
        self.assertEqual(directive.permission, 'permission')
        self.assertEqual(directive.extras, {})

    def test_after(self):
        context = DummyContext(transitions=[])
        directive = self._makeOne(context)
        directive.after()
        self.assertEqual(context.transitions, [directive])

class TestStateDirective(unittest.TestCase):
    def setUp(self):
        testing.cleanUp()

    def tearDown(self):
        testing.cleanUp()

    def _getTargetClass(self):
        from repoze.bfg.workflow.zcml import StateDirective
        return StateDirective

    def _makeOne(self, context=None, name=None):
        return self._getTargetClass()(context, name)

    def test_ctor(self):
        directive = self._makeOne('context', 'name')
        self.assertEqual(directive.context, 'context')
        self.assertEqual(directive.name, 'name')

    def test_after(self):
        context = DummyContext(states=[])
        directive = self._makeOne(context)
        directive.after()
        self.assertEqual(context.states, [directive])

class TestKeyValuePair(unittest.TestCase):
    def _callFUT(self, context, key, value):
        from repoze.bfg.workflow.zcml import key_value_pair
        key_value_pair(context, key, value)

    def test_it_no_extras(self):
        context = DummyContext()
        context.context = DummyContext()
        self._callFUT(context, 'key', 'value')
        self.assertEqual(context.context.extras, {'key':'value'})

class TestFixtureApp(unittest.TestCase):
    def setUp(self):
        testing.cleanUp()

    def tearDown(self):
        testing.cleanUp()

    def test_execute_actions(self):
        from zope.configuration import xmlconfig
        from zope.component import getSiteManager
        from repoze.bfg.workflow.interfaces import IWorkflowLookup
        from repoze.bfg.workflow.workflow import Workflow
        from repoze.bfg.workflow.tests.fixtures.dummy import callback
        import repoze.bfg.workflow.tests.fixtures as package
        from repoze.bfg.workflow.tests.fixtures.dummy import IContent
        xmlconfig.file('configure.zcml', package, execute=True)
        sm = getSiteManager()
        wf_list = sm.adapters.lookup((IContent,),
                                     IWorkflowLookup, name='theworkflow')
        self.assertEqual(len(wf_list), 1)
        workflow_data = wf_list[0]
        self.assertEqual(workflow_data['container_type'], None)
        workflow = workflow_data['workflow']
        self.assertEqual(workflow.__class__, Workflow)
        self.assertEqual(
            workflow._state_order,
            ['private', 'public'],
            )
        self.assertEqual(
            workflow._state_data,
            {u'public': {'description': u'Everybody can see it',
                         'title': u'Public'},
             u'private': {'description': u'Nobody can see it',
                          'title': u'Private'}},
            )
        transitions = workflow._transition_data
        self.assertEqual(len(transitions), 3)
        self.assertEqual(transitions['initialize'],
             {'from_state': None, 'callback': callback,
              'name': 'initialize', 'to_state': u'private'},)
        self.assertEqual(transitions['to_public'],
            {'from_state': u'private', 'callback': callback,
              'name': u'to_public', 'to_state': u'public'},)
        self.assertEqual(transitions['to_private'],
             {'from_state': u'public', 'callback': callback,
              'name': 'to_private', 'to_state': u'private'}
            )

class DummyContext:
    info = None
    def __init__(self, **kw):
        self.actions = []
        self.__dict__.update(kw)

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

                  
