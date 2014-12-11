import unittest
from zope.testing.cleanup import cleanUp

class TestWorkflowDirective(unittest.TestCase):
    def setUp(self):
        cleanUp()

    def tearDown(self):
        cleanUp()

    def _getTargetClass(self):
        from repoze.workflow.zcml import WorkflowDirective
        return WorkflowDirective

    def _makeOne(self, context=None, type=None, name=None, state_attr=None,
                 initial_state=None, content_types=()):
        if context is None:
            context = DummyContext()
        return self._getTargetClass()(context, type, name, state_attr,
                                      initial_state, content_types)

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
        from repoze.workflow.interfaces import IWorkflow
        from repoze.workflow.workflow import Workflow
        from repoze.workflow.workflow import IWorkflowList
        class IDummy(Interface):
            pass
        class IDummy2(Interface):
            pass
        directive = self._makeOne(initial_state='public', type='security',
                                  content_types=(IDummy, IDummy2))
        directive.states = [DummyState('private', title='Private', a=1),
                            DummyState('public', b=2)
                           ]
        directive.transitions = [DummyTransition('make_public'),
                                 DummyTransition('make_private',
                                                 title='Retract'),
                                ]
        directive.after()
        actions = directive.context.actions
        self.assertEqual(len(actions), 2)

        action = actions[0]
        self.assertEqual(action['info'], None)
        self.assertEqual(action['kw'], {})
        self.assertEqual(action['args'], (IDummy,))
        self.assertEqual(action['includepath'], ())
        self.assertEqual(action['order'], 0)
        self.assertEqual(action['discriminator'],
                         (IWorkflow, IDummy, None, 'security', None))
        callback = action['callable']
        self.assertEqual(type(callback), types.FunctionType)
        callback(IDummy)
        sm = getSiteManager()
        wflist = sm.adapters.lookup((IDummy,), IWorkflowList, name='security')
        self.assertEqual(len(wflist), 1)
        wf_dict = wflist[0]
        self.assertEqual(wf_dict['elector'], None)
        self.assertEqual(wf_dict['workflow'].__class__, Workflow)
        workflow = wf_dict['workflow']
        self.assertEqual(
            workflow._state_data,
            {'public':
                {'callback': None, 'title': 'public', 'b': 2},
             'private':
                {'callback': None, 'title': 'Private', 'a': 1},
             })
        self.assertEqual(
            workflow._transition_data,
            {'make_public':
             {'from_state': 'private', 'callback': None,
              'guards': [], 'name': 'make_public', 
              'to_state': 'public', 'permission':None, 
              'title': 'make_public'},
             'make_private':
             {'from_state': 'private', 'callback': None,
              'guards': [], 'name': 'make_private', 
              'to_state': 'public', 'permission':None, 
              'title': 'Retract'},
             })
        self.assertEqual(workflow.initial_state, 'public')

        action = actions[1]
        self.assertEqual(action['info'], None)
        self.assertEqual(action['kw'], {})
        self.assertEqual(action['args'], (IDummy2,))
        self.assertEqual(action['includepath'], ())
        self.assertEqual(action['order'], 0)
        self.assertEqual(action['discriminator'],
                                (IWorkflow, IDummy2, None, 'security', None))
        callback = action['callable']
        self.assertEqual(type(callback), types.FunctionType)
        callback(IDummy2)
        sm = getSiteManager()
        wflist = sm.adapters.lookup((IDummy2,), IWorkflowList, name='security')
        self.assertEqual(len(wflist), 1)
        wf_dict = wflist[0]
        self.assertEqual(wf_dict['elector'], None)
        self.assertEqual(wf_dict['workflow'].__class__, Workflow)
        workflow = wf_dict['workflow']
        self.assertEqual(
            workflow._state_data,
            {'public':
                {'callback': None, 'title': 'public', 'b': 2},
             'private':
                {'callback': None, 'title': 'Private', 'a': 1},
             })
        self.assertEqual(
            workflow._transition_data,
            {'make_public':
             {'from_state': 'private', 'callback': None,
              'guards': [], 'name': 'make_public', 
              'to_state': 'public', 'permission':None, 
              'title': 'make_public'},
             'make_private':
             {'from_state': 'private', 'callback': None,
              'guards': [], 'name': 'make_private', 
              'to_state': 'public', 'permission':None, 
              'title': 'Retract'},
             }
            )
        self.assertEqual(workflow.initial_state, 'public')

    def test_after_warns_if_no_content_types(self):
        import warnings
        directive = self._makeOne(initial_state='public', type='security')
        directive.states = [ DummyState('private', a=1),
                             DummyState('public', b=2) ]
        directive.transitions = [ DummyTransition('make_public'),
                                  DummyTransition('make_private'),
                                  ]
        with warnings.catch_warnings(record=True) as log:
            directive.after()
        self .assertEqual(len(log), 1)
        self .assertEqual(log[0].category, UserWarning)

    def test_after_raises_error_during_transition_add(self):
        from zope.interface import Interface
        from zope.configuration.exceptions import ConfigurationError
        class IDummy(Interface):
            pass
        directive = self._makeOne(initial_state='public',
                                  content_types=(IDummy,))
        directive.states = [ DummyState('s1', a=1), DummyState('s2', b=2) ]
        directive.transitions = [ DummyTransition('make_public'),
                                  DummyTransition('make_public'),
                                  ]
        directive.after()
        actions = directive.context.actions
        action = actions[0]
        callback = action['callable']
        self.assertRaises(ConfigurationError, callback, IDummy)

    def test_after_raises_error_during_state_add(self):
        from zope.interface import Interface
        from zope.configuration.exceptions import ConfigurationError
        class IDummy(Interface):
            pass
        directive = self._makeOne(initial_state='public',
                                  content_types=(IDummy,))
        directive.states = [ DummyState('public', a=1),
                             DummyState('public', b=2) ]
        directive.after()
        actions = directive.context.actions
        action = actions[0]
        callback = action['callable']
        self.assertRaises(ConfigurationError, callback, IDummy)

    def test_after_raises_error_during_check(self):
        from zope.interface import Interface
        from zope.configuration.exceptions import ConfigurationError
        class IDummy(Interface):
            pass
        directive = self._makeOne(initial_state='public',
                                  content_types=(IDummy,))
        directive.states = [ DummyState('only', a=1)]
        directive.after()
        actions = directive.context.actions
        action = actions[0]
        callback = action['callable']
        self.assertRaises(ConfigurationError, callback, IDummy)

class TestTransitionDirective(unittest.TestCase):
    def setUp(self):
        cleanUp()

    def tearDown(self):
        cleanUp()

    def _getTargetClass(self):
        from repoze.workflow.zcml import TransitionDirective
        return TransitionDirective

    def _makeOne(self, context=None, name=None, from_state=None,
                 to_state=None, callback=None, permission=None):
        return self._getTargetClass()(context, name, from_state,
                                      to_state, callback, permission)

    def test_ctor(self):
        directive = self._makeOne('context', 'name', 'from_state',
                                  'to_state', 'callback', 'permission')
        self.assertEqual(directive.context, 'context')
        self.assertEqual(directive.name, 'name')
        self.assertEqual(directive.callback, 'callback')
        self.assertEqual(directive.from_state, 'from_state')
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
        cleanUp()

    def tearDown(self):
        cleanUp()

    def _getTargetClass(self):
        from repoze.workflow.zcml import StateDirective
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
        from repoze.workflow.zcml import key_value_pair
        key_value_pair(context, key, value)

    def test_it_no_extras(self):
        context = DummyContext()
        context.context = DummyContext()
        self._callFUT(context, 'key', 'value')
        self.assertEqual(context.context.extras, {'key':'value'})

class TestGuard(unittest.TestCase):
    def _callFUT(self, context, func):
        from repoze.workflow.zcml import guard_function
        guard_function(context, func)

    def test_it_no_extras(self):
        context = DummyTransition('dummy')
        def example(context, transition):  # pragma: NO COVER
            return None
        self._callFUT(context, example)
        self.assertEqual(context.guards, [example])

class TestAlias(unittest.TestCase):
    def _callFUT(self, context, name):
        from repoze.workflow.zcml import alias
        alias(context, name)

    def test_it(self):
        context = DummyContext()
        context.context = DummyContext()
        self._callFUT(context, 'thename')
        self.assertEqual(context.context.aliases, ['thename'])

class TestFixtureApp(unittest.TestCase):
    def setUp(self):
        cleanUp()

    def tearDown(self):
        cleanUp()

    def test_execute_actions(self):
        from zope.configuration import xmlconfig
        from zope.component import getSiteManager
        from repoze.workflow.interfaces import IWorkflowList
        from repoze.workflow.workflow import Workflow
        from repoze.workflow.tests.fixtures.dummy import callback
        import repoze.workflow.tests.fixtures as package
        from repoze.workflow.tests.fixtures import dummy
        from repoze.workflow.tests.fixtures.dummy import IContent
        from repoze.workflow.tests.fixtures.dummy import elector
        from repoze.workflow.tests.fixtures.dummy import has_permission
        from repoze.workflow._compat import text_ as _u
        xmlconfig.file('configure.zcml', package, execute=True)
        sm = getSiteManager()
        wf_list = sm.adapters.lookup((IContent,),
                                     IWorkflowList, name='security')
        self.assertEqual(len(wf_list), 1)
        workflow_data = wf_list[0]
        self.assertEqual(workflow_data['elector'], elector)
        workflow = workflow_data['workflow']
        self.assertEqual(workflow.__class__, Workflow)
        self.assertEqual(workflow.name, 'the workflow')
        self.assertEqual(workflow.description, 'The workflow which is of the '
                         'testing fixtures package')
        self.assertEqual(workflow.permission_checker, has_permission)
        self.assertEqual(
            workflow._state_aliases,
            {'supersecret':'private'},
            )
        self.assertEqual(
            workflow._state_data,
            {_u('public'):
                {'callback':callback,
                 'description': _u('Everybody can see it'),
                 'title': _u('Public'),
                },
             _u('private'):
                {'callback':callback,
                 'description': _u('Nobody can see it'),
                 'title': _u('Private'),
                },
            })
        transitions = workflow._transition_data
        self.assertEqual(len(transitions), 3)
        self.assertEqual(transitions['private_to_public'],
            {'from_state': _u('private'),
             'callback': callback,
             'guards': [],
             'name': _u('private_to_public'),
             'to_state': _u('public'),
             'permission':'moderate',
             'title': 'private_to_public',
            }),
        self.assertEqual(transitions['unavailable_public_to_private'],
            {'from_state': _u('public'),
             'callback': callback,
             'guards': [dummy.never],
             'name': _u('unavailable_public_to_private'),
             'to_state': _u('private'),
             'permission':_u('moderate'),
             'title': _u('unavailable_public_to_private'),
            }),
        self.assertEqual(transitions['public_to_private'],
             {'from_state': _u('public'),
              'callback': callback,
              'guards': [],
              'name': 'public_to_private',
              'to_state': _u('private'),
              'permission':'moderate',
              'title': 'public_to_private'}
            )

class TestRegisterWorkflow(unittest.TestCase):
    def setUp(self):
        cleanUp()

    def tearDown(self):
        cleanUp()

    def _callFUT(self, workflow, type, content_type, elector=None, info=None):
        from repoze.workflow.zcml import register_workflow
        return register_workflow(workflow, type, content_type, elector, info)

    def test_register_None_as_content_type(self):
        from repoze.workflow.interfaces import IWorkflowList
        from repoze.workflow.interfaces import IDefaultWorkflow
        from zope.component import getSiteManager

        workflow = object()
        self._callFUT(workflow, 'security', None)
        sm = getSiteManager()
        
        wf_list = sm.adapters.lookup((IDefaultWorkflow,), IWorkflowList,
                                     name='security')
        self.assertEqual(wf_list, [{'elector':None, 'workflow':workflow}])
        
    def test_register_iface_as_content_type(self):
        from repoze.workflow.interfaces import IWorkflowList
        from zope.component import getSiteManager
        from zope.interface import Interface
        class IFoo(Interface):
            pass
        workflow = object()
        self._callFUT(workflow, 'security', IFoo)
        sm = getSiteManager()
        
        wf_list = sm.adapters.lookup((IFoo,), IWorkflowList,
                                     name='security')
        self.assertEqual(wf_list, [{'elector':None, 'workflow':workflow}])
        
    def test_register_class_as_content_type(self):
        from repoze.workflow.interfaces import IWorkflowList
        from zope.component import getSiteManager
        from zope.interface import providedBy
        from zope.interface import Interface
        class Foo:
            pass
        class IBar(Interface):
            pass
        workflow = object()
        self._callFUT(workflow, 'security', Foo)
        sm = getSiteManager()
        pb = providedBy(Foo)
        wf_list = sm.adapters.lookup((pb,), IWorkflowList, name='security')
        self.assertEqual(wf_list, [{'elector':None, 'workflow':workflow}])
        other = sm.adapters.lookup((IBar,), IWorkflowList, name='security')
        self.assertEqual(other, None)

class DummyContext:
    info = None
    def __init__(self, **kw):
        self.actions = []
        self.__dict__.update(kw)

class DummyState:
    def __init__(self, name, callback=None, aliases=(), title=None, **extras):
        self.name = name
        self.title = title
        self.callback = callback
        self.extras = extras
        self.aliases = aliases
        
class DummyTransition:
    def __init__(self, name, from_state='private', to_state='public',
                 callback=None, permission=None, title=None, **extras):
        self.name = name
        self.from_state = from_state
        self.to_state = to_state
        self.callback = callback
        self.permission = permission
        self.title = title
        self.extras = extras
        self.guards = []
