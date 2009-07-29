import unittest
from repoze.bfg import testing

class WorkflowTests(unittest.TestCase):

    def _getTargetClass(self):
        from repoze.bfg.workflow import Workflow
        return Workflow

    def _makeOne(self, attr='state', initial_state=None):
        klass = self._getTargetClass()
        return klass(attr, initial_state)

    def test_class_conforms_to_IWorkflow(self):
        from zope.interface.verify import verifyClass
        from repoze.bfg.workflow.interfaces import IWorkflow
        verifyClass(IWorkflow, self._getTargetClass())

    def test_instance_conforms_to_IWorkflow(self):
        from zope.interface.verify import verifyObject
        from repoze.bfg.workflow.interfaces import IWorkflow
        verifyObject(IWorkflow, self._makeOne())

    def test_call(self):
        workflow = self._makeOne()
        self.assertEqual(workflow(None), workflow)

    def test_state_of_default(self):
        sm = self._makeOne()
        ob = ReviewedObject()
        self.assertEqual(sm.state_of(ob), None)

    def state_of_nondefault(self):
        sm = self._makeOne()
        ob = ReviewedObject()
        ob.state = 'pending'
        self.assertEqual(sm.state_of(ob), 'pending')

    def test_add_state_info_state_exists(self):
        sm = self._makeOne()
        sm._state_names = ['foo']
        sm._state_data = {'foo':{'c':5}}
        sm.add_state_info('foo', a=1, b=2)
        self.assertEqual(sm._state_order, ['foo'])
        self.assertEqual(sm._state_data, {'foo':{'a':1, 'b':2, 'c':5}})

    def test_add_state_info_state_doesntexist(self):
        sm = self._makeOne()
        sm.add_state_info('foo', a=1, b=2)
        self.assertEqual(sm._state_order, ['foo'])
        self.assertEqual(sm._state_data, {'foo':{'a':1, 'b':2}})

    def test_add_transition(self):
        sm = self._makeOne()
        sm.add_transition('make_public', 'private', 'public', None, a=1)
        sm.add_transition('make_private', 'public', 'private', None, b=2)
        self.assertEqual(len(sm._transition_data), 2)
        self.assertEqual(sm._transition_order, ['make_public', 'make_private'])
        make_public = sm._transition_data['make_public']
        self.assertEqual(make_public['name'], 'make_public')
        self.assertEqual(make_public['from_state'], 'private')
        self.assertEqual(make_public['to_state'], 'public')
        self.assertEqual(make_public['callback'], None)
        self.assertEqual(make_public['a'], 1)
        make_private = sm._transition_data['make_private']
        self.assertEqual(make_private['name'], 'make_private')
        self.assertEqual(make_private['from_state'], 'public')
        self.assertEqual(make_private['to_state'], 'private')
        self.assertEqual(make_private['callback'], None)
        self.assertEqual(make_private['b'], 2)

        self.assertEqual(len(sm._state_order), 2)

    def _add_transitions(self, sm, callback=None):
        tdata = sm._transition_data
        tdata['publish'] =  dict(name='publish',
                                 from_state='pending',
                                 to_state='published',
                                 callback=callback)
        tdata['reject'] = dict(name='reject',
                               from_state='pending',
                               to_state='private',
                               callback=callback)
        tdata['retract'] = dict(name='retract',
                                from_state='published',
                                to_state='pending',
                                callback=callback)
        tdata['submit'] = dict(name='submit',
                               from_state='private',
                               to_state='pending',
                               callback=callback)
        sm._transition_order = ['publish', 'reject', 'retract', 'submit']
        if not sm._state_order:
            sm._state_order = ['pending', 'published', 'private']
        sm._state_data.setdefault('pending', {})
        sm._state_data.setdefault('published', {})
        sm._state_data.setdefault('private', {})

    def test__transitions_default_from_state(self):
        sm = self._makeOne(initial_state='pending')
        self._add_transitions(sm)
        ob = ReviewedObject()
        ob.state = 'pending'
        result = sm._transitions(ob)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'publish')
        self.assertEqual(result[1]['name'], 'reject')

    def test__transitions_overridden_from_state(self):
        sm = self._makeOne(initial_state='pending')
        self._add_transitions(sm)
        ob = ReviewedObject()
        result = sm._transitions(ob, from_state='private')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'submit')

    def test__transitions_context_has_state(self):
        sm = self._makeOne(initial_state='pending')
        self._add_transitions(sm)
        ob = ReviewedObject()
        ob.state = 'published'
        result = sm._transitions(ob)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'retract')

    def test__execute(self):
        sm = self._makeOne(initial_state='pending')
        args = []
        def dummy(context, transition):
            args.append((context, transition))
        self._add_transitions(sm, callback=dummy)
        ob = ReviewedObject()
        ob.state = 'pending'
        sm._execute(ob, 'publish')
        self.assertEqual(ob.state, 'published')
        sm._execute(ob, 'retract')
        self.assertEqual(ob.state, 'pending')
        sm._execute(ob, 'reject')
        self.assertEqual(ob.state, 'private')
        sm._execute(ob, 'submit')
        self.assertEqual(ob.state, 'pending')

        self.assertEqual(len(args), 4)
        self.assertEqual(args[0][0], ob)
        self.assertEqual(args[0][1], {'from_state': 'pending',
                                      'callback': dummy,
                                      'to_state': 'published',
                                      'name': 'publish'})
        self.assertEqual(args[1][0], ob)
        self.assertEqual(args[1][1], {'from_state': 'published',
                                      'callback': dummy,
                                      'to_state': 'pending',
                                      'name': 'retract'})
        self.assertEqual(args[2][0], ob)
        self.assertEqual(args[2][1], {'from_state': 'pending',
                                      'callback': dummy,
                                      'to_state': 'private',
                                      'name': 'reject'})
        self.assertEqual(args[3][0], ob)
        self.assertEqual(args[3][1], {'from_state': 'private',
                                      'callback': dummy,
                                      'to_state': 'pending',
                                      'name': 'submit'})


    def test__execute_error(self):
        sm = self._makeOne(initial_state='pending')
        ob = ReviewedObject()
        from repoze.bfg.workflow import StateMachineError
        self.assertRaises(StateMachineError, sm._execute, ob, 'nosuch')

    def test__execute_guard(self):
        def guard(context, transition):
            raise ValueError
        sm = self._makeOne(initial_state='pending')
        self._add_transitions(sm)
        ob = ReviewedObject()
        ob.state = 'pending'
        self.assertRaises(ValueError, sm._execute, ob, 'publish', (guard,))

    def test__transition_to_state(self):
        sm = self._makeOne(initial_state='pending')
        args = []
        def dummy(context, transition):
            args.append((context, transition))
        self._add_transitions(sm, callback=dummy)
        ob = ReviewedObject()
        ob.state = 'pending'
        sm._transition_to_state(ob, 'published')
        self.assertEqual(ob.state, 'published')
        sm._transition_to_state(ob, 'pending')
        self.assertEqual(ob.state, 'pending')
        sm._transition_to_state(ob, 'private')
        self.assertEqual(ob.state, 'private')
        sm._transition_to_state(ob, 'pending')

        self.assertEqual(len(args), 4)
        self.assertEqual(args[0][0], ob)
        self.assertEqual(args[0][1], {'from_state': 'pending',
                                      'callback': dummy,
                                      'to_state': 'published',
                                      'name': 'publish'})
        self.assertEqual(args[1][0], ob)
        self.assertEqual(args[1][1], {'from_state': 'published',
                                      'callback': dummy,
                                      'to_state': 'pending',
                                      'name': 'retract'})
        self.assertEqual(args[2][0], ob)
        self.assertEqual(args[2][1], {'from_state': 'pending',
                                      'callback': dummy,
                                      'to_state': 'private',
                                      'name': 'reject'})
        self.assertEqual(args[3][0], ob)
        self.assertEqual(args[3][1], {'from_state': 'private',
                                      'callback': dummy,
                                      'to_state': 'pending',
                                      'name': 'submit'})

    def test__transition_to_state_error(self):
        sm = self._makeOne(initial_state='pending')
        ob = ReviewedObject()
        from repoze.bfg.workflow import StateMachineError
        self.assertRaises(StateMachineError, sm._transition_to_state, ob,
                          'nosuch')

    def test__transition_to_state_skip_same_false(self):
        sm = self._makeOne(initial_state='pending')
        ob = ReviewedObject()
        from repoze.bfg.workflow import StateMachineError
        self.assertRaises(StateMachineError, sm._transition_to_state, ob,
                          'pending', (), False)

    def test__transition_to_state_skip_same_true(self):
        sm = self._makeOne(initial_state='pending')
        ob = ReviewedObject()
        ob.state = 'pending'
        self.assertEqual(sm._transition_to_state(ob, 'pending', (), True), None)

    def test__state_info_with_title(self):
        sm = self._makeOne(initial_state='pending')
        sm.add_state_info('pending', title='Pending')
        self._add_transitions(sm)
        ob = ReviewedObject()
        ob.state = 'pending'
        result = sm._state_info(ob)
        
        state = result[0]
        self.assertEqual(state['initial'], True)
        self.assertEqual(state['current'], True)
        self.assertEqual(state['name'], 'pending')
        self.assertEqual(state['title'], 'Pending')
        self.assertEqual(state['data'], {'title':'Pending'})
        self.assertEqual(len(state['transitions']), 0)


    def test__state_info_pending(self):
        sm = self._makeOne(initial_state='pending')
        sm.add_state_info('pending', desc='Pending')
        sm.add_state_info('published', desc='Published')
        sm.add_state_info('private', desc='Private')
        self._add_transitions(sm)
        ob = ReviewedObject()
        ob.state = 'pending'
        result = sm._state_info(ob)
        self.assertEqual(len(result), 3)

        state = result[0]
        self.assertEqual(state['initial'], True)
        self.assertEqual(state['current'], True)
        self.assertEqual(state['name'], 'pending')
        self.assertEqual(state['title'], 'pending')
        self.assertEqual(state['data'], {'desc':'Pending'})
        self.assertEqual(len(state['transitions']), 0)

        state = result[1]
        self.assertEqual(state['initial'], False)
        self.assertEqual(state['current'], False)
        self.assertEqual(state['name'], 'published')
        self.assertEqual(state['title'], 'published')
        self.assertEqual(state['data'], {'desc':'Published'})
        self.assertEqual(len(state['transitions']), 1)
        self.assertEquals(state['transitions'][0]['name'], 'publish')

        state = result[2]
        self.assertEqual(state['initial'], False)
        self.assertEqual(state['current'], False)
        self.assertEqual(state['name'], 'private')
        self.assertEqual(state['title'], 'private')
        self.assertEqual(state['data'], {'desc':'Private'})
        self.assertEqual(len(state['transitions']), 1)
        self.assertEqual(state['transitions'][0]['name'], 'reject')


    def test__state_info_published(self):
        sm = self._makeOne(initial_state='pending')
        sm.add_state_info('pending', desc='Pending')
        sm.add_state_info('published', desc='Published')
        sm.add_state_info('private', desc='Private')
        self._add_transitions(sm)
        ob = ReviewedObject()
        ob.state = 'published'
        result = sm._state_info(ob)
        self.assertEqual(len(result), 3)

        state = result[0]
        self.assertEqual(state['initial'], True)
        self.assertEqual(state['current'], False)
        self.assertEqual(state['name'], 'pending')
        self.assertEqual(state['title'], 'pending')
        self.assertEqual(state['data'], {'desc':'Pending'})
        self.assertEqual(len(state['transitions']), 1)
        self.assertEquals(state['transitions'][0]['name'], 'retract')

        state = result[1]
        self.assertEqual(state['initial'], False)
        self.assertEqual(state['current'], True)
        self.assertEqual(state['name'], 'published')
        self.assertEqual(state['title'], 'published')
        self.assertEqual(state['data'], {'desc':'Published'})
        self.assertEqual(len(state['transitions']), 0)

        state = result[2]
        self.assertEqual(state['initial'], False)
        self.assertEqual(state['current'], False)
        self.assertEqual(state['name'], 'private')
        self.assertEqual(state['title'], 'private')
        self.assertEqual(state['data'], {'desc':'Private'})
        self.assertEqual(len(state['transitions']), 0)

    def test__state_info_private(self):
        sm = self._makeOne(initial_state='pending')
        sm.add_state_info('pending', desc='Pending')
        sm.add_state_info('published', desc='Published')
        sm.add_state_info('private', desc='Private')
        self._add_transitions(sm)
        ob = ReviewedObject()
        ob.state = 'private'
        result = sm._state_info(ob)
        self.assertEqual(len(result), 3)

        state = result[0]
        self.assertEqual(state['initial'], True)
        self.assertEqual(state['current'], False)
        self.assertEqual(state['name'], 'pending')
        self.assertEqual(state['title'], 'pending')
        self.assertEqual(state['data'], {'desc':'Pending'})
        self.assertEqual(len(state['transitions']), 1)
        self.assertEquals(state['transitions'][0]['name'], 'submit')

        state = result[1]
        self.assertEqual(state['initial'], False)
        self.assertEqual(state['current'], False)
        self.assertEqual(state['name'], 'published')
        self.assertEqual(state['title'], 'published')
        self.assertEqual(state['data'], {'desc':'Published'})
        self.assertEqual(len(state['transitions']), 0)

        state = result[2]
        self.assertEqual(state['initial'], False)
        self.assertEqual(state['current'], True)
        self.assertEqual(state['name'], 'private')
        self.assertEqual(state['title'], 'private')
        self.assertEqual(state['data'], {'desc':'Private'})
        self.assertEqual(len(state['transitions']), 0)

    def test_initialize_no_initializer(self):
        sm = self._makeOne(initial_state='pending')
        ob = ReviewedObject()
        sm.initialize(ob)
        self.assertEqual(ob.state, 'pending')
        
    def test_initialize_with_initializer(self):
        def initializer(context, transition):
            context.initialized = True
        sm = self._makeOne(initial_state='pending')
        sm.add_transition('initialize', None, 'pending', initializer)
        ob = ReviewedObject()
        sm.initialize(ob)
        self.assertEqual(ob.state, 'pending')
        self.assertEqual(ob.initialized, True)

    def test_execute_permissive(self):
        workflow = self._makeOne()
        executed = []
        def append(context, name, guards=()):
            D = {'context':context, 'name': name, 'guards':guards }
            executed.append(D)
        workflow._execute = lambda *arg, **kw: append(*arg, **kw)
        testing.registerDummySecurityPolicy(permissive=True)
        request = testing.DummyRequest()
        context = ReviewedObject()
        context.state = 'pending'
        workflow.execute(context, request, 'publish')
        self.assertEqual(len(executed), 1)
        executed = executed[0]
        self.assertEqual(executed['context'], context)
        self.assertEqual(executed['name'], 'publish')
        permitted = executed['guards'][0]
        result = permitted(None, {'permission':'view'})
        self.assertEqual(result, None)

    def test_execute_not_permissive(self):
        from repoze.bfg.workflow import StateMachineError
        workflow = self._makeOne()
        executed = []
        def append(context, name, guards=()):
            D = {'context':context, 'name': name, 'guards':guards }
            executed.append(D)
        workflow._execute = lambda *arg, **kw: append(*arg, **kw)
        testing.registerDummySecurityPolicy(permissive=False)
        request = testing.DummyRequest()
        context = ReviewedObject()
        context.state = 'pending'
        workflow.execute(context, request, 'publish')
        self.assertEqual(len(executed), 1)
        executed = executed[0]
        self.assertEqual(executed['context'], context)
        self.assertEqual(executed['name'], 'publish')
        permitted = executed['guards'][0]
        self.assertRaises(StateMachineError, permitted, None,
                          {'permission':'view'})

    def test_execute_request_is_None(self):
        workflow = self._makeOne()
        executed = []
        def append(context, name, guards=()):
            D = {'context':context, 'name': name, 'guards':guards }
            executed.append(D)
        workflow._execute = lambda *arg, **kw: append(*arg, **kw)
        testing.registerDummySecurityPolicy(permissive=False)
        context = ReviewedObject()
        context.state = 'pending'
        workflow.execute(context, None, 'publish')
        self.assertEqual(len(executed), 1)
        executed = executed[0]
        self.assertEqual(executed['context'], context)
        self.assertEqual(executed['name'], 'publish')
        permitted = executed['guards'][0]
        self.assertEqual(None, permitted(None, {'permission':'view'}))

    def test_execute_permission_is_None(self):
        workflow = self._makeOne()
        executed = []
        def append(context, name, guards=()):
            D = {'context':context, 'name': name, 'guards':guards }
            executed.append(D)
        workflow._execute = lambda *arg, **kw: append(*arg, **kw)
        testing.registerDummySecurityPolicy(permissive=False)
        request = testing.DummyRequest()
        context = ReviewedObject()
        context.state = 'pending'
        workflow.execute(context, request, 'publish')
        self.assertEqual(len(executed), 1)
        executed = executed[0]
        self.assertEqual(executed['context'], context)
        self.assertEqual(executed['name'], 'publish')
        permitted = executed['guards'][0]
        self.assertEqual(None, permitted(None, {}))

    def test_transition_to_state_permissive(self):
        workflow = self._makeOne()
        executed = []
        def append(context, name, guards=()):
            D = {'context':context, 'name': name, 'guards':guards }
            executed.append(D)
        workflow._transition_to_state = lambda *arg, **kw: append(*arg, **kw)
        testing.registerDummySecurityPolicy(permissive=True)
        request = testing.DummyRequest()
        context = ReviewedObject()
        context.state = 'pending'
        workflow.transition_to_state(context, request, 'published')
        self.assertEqual(len(executed), 1)
        executed = executed[0]
        self.assertEqual(executed['context'], context)
        self.assertEqual(executed['name'], 'published')
        permitted = executed['guards'][0]
        self.assertEqual(None, permitted(None, {'permission':'view'}))

    def test_transition_to_state_not_permissive(self):
        from repoze.bfg.workflow import StateMachineError
        workflow = self._makeOne()
        executed = []
        def append(context, name, guards=()):
            D = {'context':context, 'name': name, 'guards':guards }
            executed.append(D)
        workflow._transition_to_state = lambda *arg, **kw: append(*arg, **kw)
        testing.registerDummySecurityPolicy(permissive=False)
        request = testing.DummyRequest()
        context = ReviewedObject()
        context.state = 'pending'
        workflow.transition_to_state(context, request, 'published')
        self.assertEqual(len(executed), 1)
        executed = executed[0]
        self.assertEqual(executed['context'], context)
        self.assertEqual(executed['name'], 'published')
        permitted = executed['guards'][0]
        self.assertRaises(StateMachineError,
                          permitted, None, {'permission':'view'})

    def test_transition_to_state_request_is_None(self):
        workflow = self._makeOne()
        executed = []
        def append(context, name, guards=()):
            D = {'context':context, 'name': name, 'guards':guards }
            executed.append(D)
        workflow._transition_to_state = lambda *arg, **kw: append(*arg, **kw)
        testing.registerDummySecurityPolicy(permissive=False)
        context = ReviewedObject()
        context.state = 'pending'
        workflow.transition_to_state(context, None, 'published')
        self.assertEqual(len(executed), 1)
        executed = executed[0]
        self.assertEqual(executed['context'], context)
        self.assertEqual(executed['name'], 'published')
        permitted = executed['guards'][0]
        self.assertEqual(None, permitted(None, {'permission':'view'}))

    def test_transition_to_state_permission_is_None(self):
        workflow = self._makeOne()
        executed = []
        def append(context, name, guards=()):
            D = {'context':context, 'name': name, 'guards':guards }
            executed.append(D)
        workflow._transition_to_state = lambda *arg, **kw: append(*arg, **kw)
        testing.registerDummySecurityPolicy(permissive=False)
        context = ReviewedObject()
        context.state = 'pending'
        request = testing.DummyRequest()
        workflow.transition_to_state(context, request, 'published')
        self.assertEqual(len(executed), 1)
        executed = executed[0]
        self.assertEqual(executed['context'], context)
        self.assertEqual(executed['name'], 'published')
        permitted = executed['guards'][0]
        self.assertEqual(None, permitted(None, {}))

    def test_transitions_permissive(self):
        workflow = self._makeOne()
        workflow._transitions = lambda *arg, **kw: [{'permission':'view'}, {}]
        testing.registerDummySecurityPolicy(permissive=True)
        request = testing.DummyRequest()
        transitions = workflow.transitions(None, request, 'private')
        self.assertEqual(len(transitions), 2)

    def test_transitions_nonpermissive(self):
        workflow = self._makeOne()
        workflow._transitions = lambda *arg, **kw: [{'permission':'view'}, {}]
        testing.registerDummySecurityPolicy(permissive=False)
        request = testing.DummyRequest()
        transitions = workflow.transitions(request, 'private')
        self.assertEqual(len(transitions), 1)

    def test_state_info_permissive(self):
        state_info = []
        state_info.append({'transitions':[{'permission':'view'}, {}]})
        state_info.append({'transitions':[{'permission':'view'}, {}]})
        workflow = self._makeOne()
        workflow._state_info = lambda *arg, **kw: state_info
        request = testing.DummyRequest()
        testing.registerDummySecurityPolicy(permissive=True)
        result = workflow.state_info(request, 'whatever')
        self.assertEqual(result, state_info)

    def test_state_info_nonpermissive(self):
        state_info = []
        state_info.append({'transitions':[{'permission':'view'}, {}]})
        state_info.append({'transitions':[{'permission':'view'}, {}]})
        workflow = self._makeOne()
        workflow._state_info = lambda *arg, **kw: state_info
        request = testing.DummyRequest()
        testing.registerDummySecurityPolicy(permissive=False)
        result = workflow.state_info(request, 'whatever')
        self.assertEqual(result, [{'transitions': [{}]}, {'transitions': [{}]}])

class TestGetWorkflow(unittest.TestCase):
    def setUp(self):
        testing.cleanUp()

    def tearDown(self):
        testing.cleanUp()

    def _callFUT(self, iface, name):
        from repoze.bfg.workflow import get_workflow
        return get_workflow(iface, name)

    def test_it(self):
        from zope.interface import Interface
        class IDummy(Interface):
            pass
        from repoze.bfg.workflow import IWorkflow
        testing.registerAdapter('adapter', (IDummy,), IWorkflow, name="foo")
        result = self._callFUT(IDummy, 'foo')
        self.assertEqual(result, 'adapter')

class ReviewedObject:
    pass
