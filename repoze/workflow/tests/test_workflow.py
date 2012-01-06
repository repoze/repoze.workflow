import unittest
from zope.testing.cleanup import cleanUp

class WorkflowTests(unittest.TestCase):

    def _getTargetClass(self):
        from repoze.workflow import Workflow
        return Workflow

    def _makeOne(self, attr='state', initial_state='pending',
                 permission_checker=None):
        klass = self._getTargetClass()
        return klass(attr, initial_state, permission_checker)

    def _makePopulated(self, state_callback=None, transition_callback=None):
        sm = self._makeOne()
        sm._state_order = ['pending', 'published', 'private']
        sm._state_data.setdefault('pending', {'callback':state_callback})
        sm._state_data.setdefault('published', {'callback':state_callback})
        sm._state_data.setdefault('private', {'callback':state_callback})
        tdata = sm._transition_data
        tdata['publish'] =  dict(name='publish',
                                 from_state='pending',
                                 to_state='published',
                                 callback=transition_callback)
        tdata['reject'] = dict(name='reject',
                               from_state='pending',
                               to_state='private',
                               callback=transition_callback)
        tdata['retract'] = dict(name='retract',
                                from_state='published',
                                to_state='pending',
                                callback=transition_callback)
        tdata['submit'] = dict(name='submit',
                               from_state='private',
                               to_state='pending',
                               callback=transition_callback)
        sm._transition_order = ['publish', 'reject', 'retract', 'submit']
        return sm

    def _makePopulatedOverlappingTransitions(
        self, state_callback=None, transition_callback=None,
        permission_checker=None):
        sm = self._makePopulated(state_callback, transition_callback)
        sm.permission_checker = permission_checker

        sm._transition_data['submit2'] = dict(
            name='submit2',
            from_state='private',
            to_state='pending',
            callback=transition_callback,
            )
        sm._transition_order.append('submit2')
        return sm

    def test_transition_to_state_two_transitions_second_works(self):
        args = []
        def dummy(content, info):
            args.append((content, info))

        def checker(permission, context, request):
            return permission == 'allowed'

        sm = self._makePopulatedOverlappingTransitions(
            transition_callback=dummy,
            permission_checker=checker,
            )

        sm._transition_data['submit']['permission'] = 'forbidden'
        sm._transition_data['submit2']['permission'] = 'allowed'

        ob = DummyContent()
        ob.state = 'private'
        sm.transition_to_state(ob, object(), 'pending')
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0][1].transition['name'], 'submit2')

    def test_transition_to_state_two_transitions_none_works(self):
        callback_args = []
        def dummy(content, info):
            callback_args.append((content, info))

        checker_args = []
        def checker(permission, context, request):
            checker_args.append((permission, context, request))
            return permission == 'allowed'

        sm = self._makePopulatedOverlappingTransitions(
            transition_callback=dummy,
            permission_checker=checker,
            )

        sm._transition_data['submit']['permission'] = 'forbidden1'
        sm._transition_data['submit2']['permission'] = 'forbidden2'

        ob = DummyContent()
        ob.state = 'private'
        from repoze.workflow import WorkflowError
        self.assertRaises(WorkflowError, sm.transition_to_state,
                          ob, object(), 'pending')
        self.assertEqual(len(callback_args), 0)
        self.assertEqual(len(checker_args), 2)
        self.assertEqual([a[0] for a in checker_args],
                         ['forbidden1', 'forbidden2'])

    def test_class_conforms_to_IWorkflow(self):
        from zope.interface.verify import verifyClass
        from repoze.workflow.interfaces import IWorkflow
        verifyClass(IWorkflow, self._getTargetClass())

    def test_instance_conforms_to_IWorkflow(self):
        from zope.interface.verify import verifyObject
        from repoze.workflow.interfaces import IWorkflow
        verifyObject(IWorkflow, self._makeOne())

    def test_call(self):
        workflow = self._makeOne()
        self.assertEqual(workflow(None), workflow)

    def test_has_state_false(self):
        sm = self._makeOne()
        self.assertEqual(sm.has_state(None), False)

    def test_has_state_true(self):
        sm = self._makeOne()
        ob = DummyContent()
        ob.state = 'abc'
        self.assertEqual(sm.has_state(ob), True)

    def test__state_of_uninitialized(self):
        sm = self._makeOne()
        ob = DummyContent()
        self.assertEqual(sm._state_of(ob),  None)

    def test__state_of_initialized(self):
        sm = self._makeOne()
        ob = DummyContent()
        ob.state = 'pending'
        self.assertEqual(sm._state_of(ob),  'pending')

    def test_state_of_does_initialization(self):
        sm = self._makeOne()
        sm.add_state('pending')
        ob = DummyContent()
        self.assertEqual(sm.state_of(ob), 'pending')
        self.assertEqual(ob.state, 'pending')

    def test_state_of_nondefault(self):
        sm = self._makeOne()
        ob = DummyContent()
        ob.state = 'pending'
        self.assertEqual(sm.state_of(ob), 'pending')

    def test_state_of_uses_aliases(self):
        sm = self._makeOne()
        sm._state_aliases = {'supersecret':'private'}
        ob = DummyContent()
        ob.state = 'supersecret'
        self.assertEqual(sm.state_of(ob), 'private')

    def test_state_of_None_is_initial_state(self):
        sm = self._makeOne()
        self.assertEqual(sm.state_of(None), 'pending')

    def test_add_state_state_exists(self):
        from repoze.workflow import WorkflowError
        sm = self._makeOne()
        sm._state_order = ['foo']
        sm._state_data = {'foo':{'c':5}}
        self.assertRaises(WorkflowError, sm.add_state, 'foo')

    def test_add_state_alias_exists(self):
        from repoze.workflow import WorkflowError
        sm = self._makeOne()
        sm._state_order = ['foo']
        sm._state_data = {'foo':{'c':5}}
        sm._state_aliases = {'bar':'foo'}
        self.assertRaises(WorkflowError, sm.add_state, 'bar')

    def test_add_state_info_state_doesntexist(self):
        sm = self._makeOne()
        callback = object()
        sm.add_state('foo', callback, a=1, b=2)
        self.assertEqual(sm._state_order, ['foo'])
        self.assertEqual(sm._state_data, {'foo':{'callback':callback,
                                                 'a':1, 'b':2}})

    def test_add_state_defaults(self):
        sm = self._makeOne()
        callback = object()
        sm.add_state('foo')
        self.assertEqual(sm._state_order, ['foo'])
        self.assertEqual(sm._state_data, {'foo':{'callback':None}})

    def test_add_state_with_aliases(self):
        sm = self._makeOne()
        callback = object()
        sm.add_state('foo', aliases=['abc', 'def'])
        self.assertEqual(sm._state_order, ['foo'])
        self.assertEqual(sm._state_aliases, {'abc':'foo', 'def':'foo'})
        self.assertEqual(sm._state_data, {'foo':{'callback':None}})

    def test_add_transition(self):
        sm = self._makeOne()
        sm.add_state('public')
        sm.add_state('private')
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

    def test_add_transition_transition_name_already_exists(self):
        from repoze.workflow import WorkflowError
        sm = self._makeOne()
        sm.add_state('public')
        sm.add_state('private')
        sm.add_transition('make_public', 'private', 'public', None, a=1)
        self.assertRaises(WorkflowError, sm.add_transition, 'make_public',
                          'private', 'public')

    def test_add_transition_from_state_doesnt_exist(self):
        from repoze.workflow import WorkflowError
        sm = self._makeOne()
        sm.add_state('public')
        self.assertRaises(WorkflowError, sm.add_transition, 'make_public',
                          'private', 'public')

    def test_add_transition_to_state_doesnt_exist(self):
        from repoze.workflow import WorkflowError
        sm = self._makeOne()
        sm.add_state('private')
        self.assertRaises(WorkflowError, sm.add_transition, 'make_public',
                          'private', 'public')

    def test_add_transition_with_permission_no_permission_checker(self):
        from repoze.workflow import WorkflowError
        sm = self._makeOne()
        sm.add_state('private')
        sm.add_state('public')
        self.assertRaises(WorkflowError, sm.add_transition, 'make_public',
                          'private', 'public', permission='permission')

    def test_check_fails(self):
        from repoze.workflow import WorkflowError
        sm = self._makeOne()
        self.assertRaises(WorkflowError, sm.check)
        
    def test_check_succeeds(self):
        sm = self._makeOne()
        sm.add_state('pending')
        self.assertEqual(sm.check(), None)

    def test__get_transitions_default_from_state(self):
        sm = self._makePopulated()
        ob = DummyContent()
        ob.state = 'pending'
        result = sm._get_transitions(ob)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'publish')
        self.assertEqual(result[1]['name'], 'reject')

    def test__get_transitions_overridden_from_state(self):
        sm = self._makePopulated()
        ob = DummyContent()
        result = sm._get_transitions(ob, from_state='private')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'submit')

    def test__get_transitions_content_has_state(self):
        sm = self._makePopulated()
        ob = DummyContent()
        ob.state = 'published'
        result = sm._get_transitions(ob)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'retract')

    def test__transition(self):
        args = []
        def dummy(content, info):
            args.append((content, info))
        sm = self._makePopulated(transition_callback=dummy)
        ob = DummyContent()
        ob.state = 'pending'
        sm._transition(ob, 'publish')
        self.assertEqual(ob.state, 'published')
        sm._transition(ob, 'retract')
        self.assertEqual(ob.state, 'pending')
        sm._transition(ob, 'reject')
        self.assertEqual(ob.state, 'private')
        sm._transition(ob, 'submit')
        self.assertEqual(ob.state, 'pending')

        self.assertEqual(len(args), 4)
        self.assertEqual(args[0][0], ob)
        info = args[0][1]
        self.assertEqual(info.transition, {'from_state': 'pending',
                                           'callback': dummy,
                                           'to_state': 'published',
                                           'name': 'publish'})
        self.assertEqual(info.workflow, sm)
        self.assertEqual(args[1][0], ob)
        info = args[1][1]
        self.assertEqual(info.transition, {'from_state': 'published',
                                           'callback': dummy,
                                           'to_state': 'pending',
                                           'name': 'retract'})
        self.assertEqual(args[1][0], ob)
        self.assertEqual(args[2][0], ob)
        info = args[2][1]
        self.assertEqual(info.transition, {'from_state': 'pending',
                                           'callback': dummy,
                                           'to_state': 'private',
                                           'name': 'reject'})
        self.assertEqual(info.workflow, sm)
        self.assertEqual(args[3][0], ob)
        info = args[3][1]
        self.assertEqual(info.transition, {'from_state': 'private',
                                           'callback': dummy,
                                           'to_state': 'pending',
                                           'name': 'submit'})
        self.assertEqual(info.workflow, sm)


    def test__transition_with_state_callback(self):
        def dummy(content, info):
            content.info = info
        sm = self._makePopulated(state_callback=dummy)
        ob = DummyContent()
        ob.state = 'pending'
        sm._transition(ob, 'publish')
        self.assertEqual(ob.info.transition,
                         {'from_state': 'pending',
                          'callback': None,
                          'to_state':
                          'published',
                          'name': 'publish'})
        self.assertEqual(ob.info.workflow, sm)

    def test__transition_error(self):
        sm = self._makeOne(initial_state='pending')
        sm.add_state('pending')
        ob = DummyContent()
        from repoze.workflow import WorkflowError
        self.assertRaises(WorkflowError, sm._transition, ob, 'nosuch')

    def test__transition_guard(self):
        def guard(content, info):
            raise ValueError
        sm = self._makePopulated()
        ob = DummyContent()
        ob.state = 'pending'
        self.assertRaises(ValueError, sm._transition, ob,
                          'publish', None, (guard,))

    def test__transition_to_state(self):
        args = []
        def dummy(content, info):
            args.append((content, info))
        sm = self._makePopulated(transition_callback=dummy)
        ob = DummyContent()
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
        info = args[0][1]
        self.assertEqual(info.transition, {'from_state': 'pending',
                                           'callback': dummy,
                                           'to_state': 'published',
                                           'name': 'publish'})
        self.assertEqual(info.workflow, sm)
        self.assertEqual(args[1][0], ob)
        info = args[1][1]
        self.assertEqual(info.transition, {'from_state': 'published',
                                           'callback': dummy,
                                           'to_state': 'pending',
                                           'name': 'retract'})
        self.assertEqual(info.workflow, sm)
        self.assertEqual(args[2][0], ob)
        info = args[2][1]
        self.assertEqual(info.transition, {'from_state': 'pending',
                                           'callback': dummy,
                                           'to_state': 'private',
                                           'name': 'reject'})
        self.assertEqual(info.workflow, sm)
        self.assertEqual(args[3][0], ob)
        info = args[3][1]
        self.assertEqual(info.transition, {'from_state': 'private',
                                           'callback': dummy,
                                           'to_state': 'pending',
                                           'name': 'submit'})
        self.assertEqual(info.workflow, sm)

    def test__transition_to_state_error(self):
        sm = self._makeOne(initial_state='pending')
        sm.add_state('pending')
        ob = DummyContent()
        from repoze.workflow import WorkflowError
        self.assertRaises(WorkflowError, sm._transition_to_state, ob,
                          'nosuch')

    def test__transition_to_state_skip_same_false(self):
        sm = self._makeOne(initial_state='pending')
        sm.add_state('pending')
        ob = DummyContent()
        from repoze.workflow import WorkflowError
        self.assertRaises(WorkflowError, sm._transition_to_state, ob, None,
                          'pending', (), False)

    def test__transition_to_state_skip_same_true(self):
        sm = self._makeOne(initial_state='pending')
        ob = DummyContent()
        ob.state = 'pending'
        self.assertEqual(sm._transition_to_state(ob, 'pending', (), True), None)

    def test__state_with_title(self):
        sm = self._makeOne()
        sm.add_state('pending', title='Pending')
        ob = DummyContent()
        ob.state = 'pending'
        result = sm._state_info(ob)
        
        state = result[0]
        self.assertEqual(state['initial'], True)
        self.assertEqual(state['current'], True)
        self.assertEqual(state['name'], 'pending')
        self.assertEqual(state['title'], 'Pending')
        self.assertEqual(state['data'], {'callback':None, 'title':'Pending'})
        self.assertEqual(len(state['transitions']), 0)


    def test__state_info_pending(self):
        sm = self._makePopulated()
        ob = DummyContent()
        ob.state = 'pending'
        result = sm._state_info(ob)
        self.assertEqual(len(result), 3)

        state = result[0]
        self.assertEqual(state['initial'], True)
        self.assertEqual(state['current'], True)
        self.assertEqual(state['name'], 'pending')
        self.assertEqual(state['title'], 'pending')
        self.assertEqual(state['data'], {'callback':None})
        self.assertEqual(len(state['transitions']), 0)

        state = result[1]
        self.assertEqual(state['initial'], False)
        self.assertEqual(state['current'], False)
        self.assertEqual(state['name'], 'published')
        self.assertEqual(state['title'], 'published')
        self.assertEqual(state['data'], {'callback':None})
        self.assertEqual(len(state['transitions']), 1)
        self.assertEquals(state['transitions'][0]['name'], 'publish')

        state = result[2]
        self.assertEqual(state['initial'], False)
        self.assertEqual(state['current'], False)
        self.assertEqual(state['name'], 'private')
        self.assertEqual(state['title'], 'private')
        self.assertEqual(state['data'], {'callback':None})
        self.assertEqual(len(state['transitions']), 1)
        self.assertEqual(state['transitions'][0]['name'], 'reject')


    def test__state_info_published(self):
        sm = self._makePopulated()
        ob = DummyContent()
        ob.state = 'published'
        result = sm._state_info(ob)
        self.assertEqual(len(result), 3)

        state = result[0]
        self.assertEqual(state['initial'], True)
        self.assertEqual(state['current'], False)
        self.assertEqual(state['name'], 'pending')
        self.assertEqual(state['title'], 'pending')
        self.assertEqual(state['data'], {'callback':None})
        self.assertEqual(len(state['transitions']), 1)
        self.assertEquals(state['transitions'][0]['name'], 'retract')

        state = result[1]
        self.assertEqual(state['initial'], False)
        self.assertEqual(state['current'], True)
        self.assertEqual(state['name'], 'published')
        self.assertEqual(state['title'], 'published')
        self.assertEqual(state['data'], {'callback':None})
        self.assertEqual(len(state['transitions']), 0)

        state = result[2]
        self.assertEqual(state['initial'], False)
        self.assertEqual(state['current'], False)
        self.assertEqual(state['name'], 'private')
        self.assertEqual(state['title'], 'private')
        self.assertEqual(state['data'], {'callback':None})
        self.assertEqual(len(state['transitions']), 0)

    def test__state_info_private(self):
        sm = self._makePopulated()
        ob = DummyContent()
        ob.state = 'private'
        result = sm._state_info(ob)
        self.assertEqual(len(result), 3)

        state = result[0]
        self.assertEqual(state['initial'], True)
        self.assertEqual(state['current'], False)
        self.assertEqual(state['name'], 'pending')
        self.assertEqual(state['title'], 'pending')
        self.assertEqual(state['data'], {'callback':None})
        self.assertEqual(len(state['transitions']), 1)
        self.assertEquals(state['transitions'][0]['name'], 'submit')

        state = result[1]
        self.assertEqual(state['initial'], False)
        self.assertEqual(state['current'], False)
        self.assertEqual(state['name'], 'published')
        self.assertEqual(state['title'], 'published')
        self.assertEqual(state['data'], {'callback':None})
        self.assertEqual(len(state['transitions']), 0)

        state = result[2]
        self.assertEqual(state['initial'], False)
        self.assertEqual(state['current'], True)
        self.assertEqual(state['name'], 'private')
        self.assertEqual(state['title'], 'private')
        self.assertEqual(state['data'], {'callback':None})
        self.assertEqual(len(state['transitions']), 0)

    def test_initialize_no_initializer(self):
        sm = self._makeOne(initial_state='pending')
        sm.add_state('pending')
        ob = DummyContent()
        state, msg = sm.initialize(ob)
        self.assertEqual(ob.state, 'pending')
        self.assertEqual(msg, None)
        self.assertEqual(state, 'pending')
        
    def test_initialize_with_initializer(self):
        def initializer(content, info):
            content.initialized = True
            return 'abc'
        sm = self._makeOne(initial_state='pending')
        sm.add_state('pending', initializer)
        ob = DummyContent()
        state, msg = sm.initialize(ob)
        self.assertEqual(ob.state, 'pending')
        self.assertEqual(ob.initialized, True)
        self.assertEqual(msg, 'abc')
        self.assertEqual(state, 'pending')

    def test_reset_content_has_no_state(self):
        def callback(content, info):
            content.called_back = True
            return '123'
        sm = self._makeOne(initial_state='pending')
        sm.add_state('pending', callback=callback)
        ob = DummyContent()
        state, msg = sm.reset(ob)
        self.assertEqual(ob.state, 'pending')
        self.assertEqual(ob.called_back, True)
        self.assertEqual(state, 'pending')
        self.assertEqual(msg, '123')

    def test_reset_content_no_callback(self):
        sm = self._makeOne(initial_state='pending')
        sm.add_state('pending',)
        ob = DummyContent()
        state, msg = sm.reset(ob)
        self.assertEqual(ob.state, 'pending')
        self.assertEqual(state, 'pending')
        self.assertEqual(msg, None)

    def test_reset_content_has_state(self):
        def callback(content, info):
            content.called_back = True
            return '123'
        sm = self._makeOne(initial_state='pending')
        sm.add_state('pending')
        sm.add_state('private', callback=callback)
        ob = DummyContent()
        ob.state = 'private'
        state, msg = sm.reset(ob)
        self.assertEqual(ob.state, 'private')
        self.assertEqual(ob.called_back, True)
        self.assertEqual(state, 'private')
        self.assertEqual(msg, '123')

    def test_reset_content_state_aliased(self):
        def callback(content, info):
            content.called_back = True
            return '123'
        sm = self._makeOne(initial_state='pending')
        sm.add_state('pending')
        sm.add_state('private', callback=callback, aliases=('supersecret',))
        ob = DummyContent()
        ob.state = 'supersecret'
        state, msg = sm.reset(ob)
        self.assertEqual(ob.state, 'private')
        self.assertEqual(ob.called_back, True)
        self.assertEqual(state, 'private')
        self.assertEqual(msg, '123')

    def test_reset_content_has_state_not_in_workflow(self):
        from repoze.workflow import WorkflowError
        sm = self._makeOne(initial_state='pending')
        sm.add_state('pending')
        ob = DummyContent()
        ob.state = 'supersecret'
        self.assertRaises(WorkflowError, sm.reset, ob)

    def test_transition_permissive(self):
        args = []
        def checker(*arg):
            args.append(arg)
            return True
        workflow = self._makeOne(permission_checker=checker)
        transitioned = []
        def append(content, name, context=None, guards=()):
            D = {'content':content, 'name': name, 'guards':guards,
                 'context':context }
            transitioned.append(D)
        workflow._transition = lambda *arg, **kw: append(*arg, **kw)
        content = DummyContent()
        content.state = 'pending'
        request = object()
        workflow.transition(content, request, 'publish')
        self.assertEqual(len(transitioned), 1)
        transitioned = transitioned[0]
        self.assertEqual(transitioned['content'], content)
        self.assertEqual(transitioned['name'], 'publish')
        self.assertEqual(transitioned['context'], None)
        permitted = transitioned['guards'][0]
        info = DummyCallbackInfo(transition = {'permission':'view'})
        result = permitted(None, info)
        self.assertEqual(result, None)
        self.assertEqual(args, [('view', None, request)])

    def test_transition_not_permissive(self):
        args = []
        def checker(*arg):
            args.append(arg)
            return False
        from repoze.workflow import WorkflowError
        workflow = self._makeOne(permission_checker=checker)
        transitioned = []
        def append(content, name, context=None, guards=()):
            D = {'content':content, 'name': name, 'guards':guards,
                 'context':context }
            transitioned.append(D)
        workflow._transition = lambda *arg, **kw: append(*arg, **kw)
        request = object()
        content = DummyContent()
        content.state = 'pending'
        workflow.transition(content, request, 'publish')
        self.assertEqual(len(transitioned), 1)
        transitioned = transitioned[0]
        self.assertEqual(transitioned['content'], content)
        self.assertEqual(transitioned['name'], 'publish')
        self.assertEqual(transitioned['context'], None)
        permitted = transitioned['guards'][0]
        info = DummyCallbackInfo(transition = {'permission':'view'})
        self.assertRaises(WorkflowError, permitted, None, info)
        self.assertEqual(args, [('view', None, request)])

    def test_transition_request_is_None(self):
        def checker(*arg): raise NotImplementedError
        workflow = self._makeOne(permission_checker=checker)
        transitioned = []
        def append(content, name, context=None, guards=(), skip_same=True):
            D = {'content':content, 'name': name, 'guards':guards,
                 'context':context, 'skip_same':skip_same }
            transitioned.append(D)
        workflow._transition = lambda *arg, **kw: append(*arg, **kw)
        content = DummyContent()
        content.state = 'pending'
        workflow.transition(content, None, 'publish')
        self.assertEqual(len(transitioned), 1)
        transitioned = transitioned[0]
        self.assertEqual(transitioned['content'], content)
        self.assertEqual(transitioned['name'], 'publish')
        self.assertEqual(transitioned['context'], None)
        self.assertEqual(transitioned['skip_same'], True)
        permitted = transitioned['guards'][0]
        info = DummyCallbackInfo(transition = {'permission':'view'})
        self.assertEqual(None, permitted(None, info))

    def test_transition_permission_is_None(self):
        def checker(*arg): raise NotImplementedError
        workflow = self._makeOne(permission_checker=checker)
        transitioned = []
        def append(content, name, context=None, guards=()):
            D = {'content':content, 'name': name, 'guards':guards,
                 'context':context }
            transitioned.append(D)
        workflow._transition = lambda *arg, **kw: append(*arg, **kw)
        content = DummyContent()
        content.state = 'pending'
        request = object()
        workflow.transition(content, request, 'publish')
        self.assertEqual(len(transitioned), 1)
        transitioned = transitioned[0]
        self.assertEqual(transitioned['content'], content)
        self.assertEqual(transitioned['name'], 'publish')
        self.assertEqual(transitioned['context'], None)
        permitted = transitioned['guards'][0]
        info = DummyCallbackInfo(transition = {})
        self.assertEqual(None, permitted(None, info))

    def test_transition_to_state_permissive(self):
        args = []
        def checker(*arg):
            args.append(arg)
            return True
        workflow = self._makeOne(permission_checker=checker)
        transitioned = []
        def append(content, name, context=None, guards=(), skip_same=True):
            D = {'content':content, 'name': name, 'guards':guards,
                 'context':context, 'skip_same':skip_same }
            transitioned.append(D)
        workflow._transition_to_state = lambda *arg, **kw: append(*arg, **kw)
        content = DummyContent()
        content.state = 'pending'
        request = object()
        workflow.transition_to_state(content, request, 'published')
        self.assertEqual(len(transitioned), 1)
        transitioned = transitioned[0]
        self.assertEqual(transitioned['content'], content)
        self.assertEqual(transitioned['name'], 'published')
        self.assertEqual(transitioned['context'], None)
        self.assertEqual(transitioned['skip_same'], True)
        permitted = transitioned['guards'][0]
        info = DummyCallbackInfo(transition = {'permission':'view'})
        self.assertEqual(None, permitted(None, info))
        self.assertEqual(args, [('view', None, request)])

    def test_transition_to_state_not_permissive(self):
        args = []
        def checker(*arg):
            args.append(arg)
            return False
        from repoze.workflow import WorkflowError
        workflow = self._makeOne(permission_checker=checker)
        transitioned = []
        def append(content, name, context=None, guards=(), skip_same=True):
            D = {'content':content, 'name': name, 'guards':guards,
                 'context':context, 'skip_same':skip_same }
            transitioned.append(D)
        workflow._transition_to_state = lambda *arg, **kw: append(*arg, **kw)
        request = object()
        content = DummyContent()
        content.state = 'pending'
        workflow.transition_to_state(content, request, 'published')
        self.assertEqual(len(transitioned), 1)
        transitioned = transitioned[0]
        self.assertEqual(transitioned['content'], content)
        self.assertEqual(transitioned['name'], 'published')
        self.assertEqual(transitioned['context'], None)
        self.assertEqual(transitioned['skip_same'], True)
        permitted = transitioned['guards'][0]
        info = DummyCallbackInfo(transition = {'permission':'view'})
        self.assertRaises(WorkflowError, permitted, None, info)
        self.assertEqual(args, [('view', None, request)])

    def test_transition_to_state_request_is_None(self):
        def checker(*arg): raise NotImplementedError
        workflow = self._makeOne(permission_checker=checker)
        transitioned = []
        def append(content, name, context=None, guards=(), skip_same=True):
            D = {'content':content, 'name': name, 'guards':guards,
                 'context':context, 'skip_same':skip_same }
            transitioned.append(D)
        workflow._transition_to_state = lambda *arg, **kw: append(*arg, **kw)
        content = DummyContent()
        content.state = 'pending'
        workflow.transition_to_state(content, None, 'published')
        self.assertEqual(len(transitioned), 1)
        transitioned = transitioned[0]
        self.assertEqual(transitioned['content'], content)
        self.assertEqual(transitioned['name'], 'published')
        self.assertEqual(transitioned['context'], None)
        self.assertEqual(transitioned['skip_same'], True)
        permitted = transitioned['guards'][0]
        info = DummyCallbackInfo(transition = {'permission':'view'})
        self.assertEqual(None, permitted(None, info))

    def test_transition_to_state_permission_is_None(self):
        def checker(*arg): raise NotImplementedError
        workflow = self._makeOne(permission_checker=checker)
        transitioned = []
        def append(content, name, context=None, guards=(), skip_same=True):
            D = {'content':content, 'name': name, 'guards':guards,
                 'context':context, 'skip_same':skip_same }
            transitioned.append(D)
        workflow._transition_to_state = lambda *arg, **kw: append(*arg, **kw)
        content = DummyContent()
        content.state = 'pending'
        request = object()
        workflow.transition_to_state(content, request, 'published')
        self.assertEqual(len(transitioned), 1)
        transitioned = transitioned[0]
        self.assertEqual(transitioned['content'], content)
        self.assertEqual(transitioned['name'], 'published')
        self.assertEqual(transitioned['context'], None)
        self.assertEqual(transitioned['skip_same'], True)
        permitted = transitioned['guards'][0]
        info = DummyCallbackInfo(transition = {})
        self.assertEqual(None, permitted(None, info))

    def test_get_transitions_permissive(self):
        args = []
        def checker(*arg):
            args.append(arg)
            return True
        workflow = self._makeOne(permission_checker=checker)
        workflow._get_transitions=lambda *arg, **kw: [{'permission':'view'}, {}]
        transitions = workflow.get_transitions(None, None, None, 'private')
        self.assertEqual(len(transitions), 2)
        self.assertEqual(args, [('view', None, None)])

    def test_get_transitions_nonpermissive(self):
        args = []
        def checker(*arg):
            args.append(arg)
            return False
        workflow = self._makeOne(permission_checker=checker)
        workflow._get_transitions=lambda *arg, **kw: [{'permission':'view'}, {}]
        transitions = workflow.get_transitions(None, 'private')
        self.assertEqual(len(transitions), 1)
        self.assertEqual(args, [('view', None, 'private')])

    def test_state_info_permissive(self):
        args = []
        def checker(*arg):
            args.append(arg)
            return True
        state_info = []
        state_info.append({'transitions':[{'permission':'view'}, {}]})
        state_info.append({'transitions':[{'permission':'view'}, {}]})
        workflow = self._makeOne(permission_checker=checker)
        workflow._state_info = lambda *arg, **kw: state_info
        request = object()
        result = workflow.state_info(request, 'whatever')
        self.assertEqual(result, state_info)
        self.assertEqual(args, [('view', request, 'whatever'),
                                ('view', request, 'whatever')])

    def test_state_info_nonpermissive(self):
        args = []
        def checker(*arg):
            args.append(arg)
            return False
        state_info = []
        state_info.append({'transitions':[{'permission':'view'}, {}]})
        state_info.append({'transitions':[{'permission':'view'}, {}]})
        workflow = self._makeOne(permission_checker=checker)
        workflow._state_info = lambda *arg, **kw: state_info
        request = object()
        result = workflow.state_info(request, 'whatever')
        self.assertEqual(result, [{'transitions': [{}]}, {'transitions': [{}]}])
        self.assertEqual(args, [('view', request, 'whatever'),
                                ('view', request, 'whatever')])

class CallbackInfoTests(unittest.TestCase):

    def _getTargetClass(self):
        from repoze.workflow.workflow import CallbackInfo
        return CallbackInfo

    def _makeOne(self, workflow, transition):
        klass = self._getTargetClass()
        return klass(workflow, transition)

    def test_class_conforms_to_ICallbackInfo(self):
        from zope.interface.verify import verifyClass
        from repoze.workflow.interfaces import ICallbackInfo
        verifyClass(ICallbackInfo, self._getTargetClass())

    def test_instance_conforms_to_ICallbackInfo(self):
        from zope.interface.verify import verifyObject
        from repoze.workflow.interfaces import ICallbackInfo
        verifyObject(ICallbackInfo, self._makeOne('workflow', 'transition'))

    def test_it(self):
        info = self._makeOne('workflow', 'transition')
        self.assertEqual(info.workflow, 'workflow')
        self.assertEqual(info.transition, 'transition')

class TestGetWorkflow(unittest.TestCase):
    def setUp(self):
        cleanUp()

    def tearDown(self):
        cleanUp()

    def _getIContent(self):
        from zope.interface import Interface
        class IContent(Interface):
            pass
        return IContent

    def _callFUT(self, iface, name, workflows=None, context=None):
        if workflows is None:
            wokflows = []
        def process_workflow_list(wf_list, context):
            if workflows:
                return workflows.pop()
        from repoze.workflow import get_workflow
        return get_workflow(iface, name, context, process_workflow_list)

    def _registerWorkflowList(self, content_type, name=''):
        from repoze.workflow.interfaces import IWorkflowList
        from zope.component import getSiteManager
        sm = getSiteManager()
        sm.registerAdapter([], (content_type,), IWorkflowList, name=name)

    def test_content_type_is_None_no_registered_workflows(self):
        self.assertEqual(self._callFUT(None, ''), None)

    def test_content_type_is_IDefaultWorkflow_no_registered_workflows(self):
        from repoze.workflow.interfaces import IDefaultWorkflow
        self.assertEqual(self._callFUT(IDefaultWorkflow, ''), None)

    def test_content_type_is_None_registered_workflow(self):
        from repoze.workflow.interfaces import IDefaultWorkflow
        workflow = object()
        self._registerWorkflowList(IDefaultWorkflow)
        result = self._callFUT(None, '', [workflow])
        self.assertEqual(result, workflow)

    def test_content_type_is_class_registered_workflow(self):
        from repoze.workflow.interfaces import IDefaultWorkflow
        class Content:
            pass
        workflow = object()
        self._registerWorkflowList(IDefaultWorkflow)
        result = self._callFUT(Content, '', [workflow])
        self.assertEqual(result, workflow)
        
    def test_content_type_is_IDefaultWorkflow_registered_workflow(self):
        from repoze.workflow.interfaces import IDefaultWorkflow
        workflow = object()
        self._registerWorkflowList(IDefaultWorkflow)
        self.assertEqual(self._callFUT(IDefaultWorkflow, '', [workflow]),
                         workflow)

    def test_content_type_is_IContent_no_registered_workflows(self):
        IContent = self._getIContent()
        self.assertEqual(self._callFUT(IContent, ''), None)
        
    def test_content_type_is_IContent_finds_default(self):
        IContent = self._getIContent()
        from repoze.workflow.interfaces import IDefaultWorkflow
        workflow = object()
        self._registerWorkflowList(IDefaultWorkflow)
        self.assertEqual(self._callFUT(IContent, '', [workflow]), workflow)

    def test_content_type_is_IContent_finds_specific(self):
        IContent = self._getIContent()
        workflow = object()
        self._registerWorkflowList(IContent)
        self.assertEqual(self._callFUT(IContent, '', [workflow]), workflow)

    def test_content_type_is_IContent_finds_more_specific_first(self):
        from repoze.workflow.interfaces import IDefaultWorkflow
        IContent = self._getIContent()
        default_workflow = object()
        specific_workflow = object()
        self._registerWorkflowList(IContent)
        self._registerWorkflowList(IDefaultWorkflow)
        self.assertEqual(
            self._callFUT(IContent, '', [specific_workflow]),
            specific_workflow)
        self.assertEqual(
            self._callFUT(None, '', [default_workflow]),
            default_workflow)

    def test_content_type_inherits_from_IContent(self):
        from repoze.workflow.interfaces import IDefaultWorkflow
        IContent = self._getIContent()
        class IContent2(IContent):
            pass
        default_workflow = object()
        specific_workflow = object()
        self._registerWorkflowList(IContent)
        self._registerWorkflowList(IDefaultWorkflow)
        self.assertEqual(
            self._callFUT(IContent2, '', [specific_workflow]),
            specific_workflow)

class TestProcessWFList(unittest.TestCase):
    def _callFUT(self, wf_list, context):
        from repoze.workflow.workflow import process_wf_list
        return process_wf_list(wf_list, context)

    def test_nothing_in_wf_list_returns_None(self):
        result = self._callFUT([], None)
        self.assertEqual(result, None)

    def test_context_is_None_elector_is_None(self):
        workflow = object()
        wflist = [{'elector':None, 'workflow':workflow}]
        result = self._callFUT(wflist, None)
        self.assertEqual(result, workflow)

    def test_context_is_None_elector_not_None_no_fallback(self):
        workflow = object()
        def elector(context): return False
        wflist = [{'elector':elector, 'workflow':workflow}]
        result = self._callFUT(wflist, None)
        self.assertEqual(result, None)

    def test_context_is_None_elector_not_None_with_fallback(self):
        workflow = object()
        default = object()
        def elector(context): return False
        wflist = [{'elector':elector, 'workflow':workflow},
                  {'elector':None, 'workflow':default}]
        result = self._callFUT(wflist, None)
        self.assertEqual(result, default)

    def test_context_not_None_elector_not_None_no_fallback(self):
        workflow = object()
        def elector(context):
            return False
        wflist = [{'elector':elector, 'workflow':workflow}]
        result = self._callFUT(wflist, object)
        self.assertEqual(result, None)

    def test_context_not_None_elector_not_None_with_fallback(self):
        workflow = object()
        default = object()
        context = object()
        def elector(context):
            return False
        wflist = [{'elector':elector, 'workflow':workflow},
                  {'elector':None, 'workflow':default}]
        result = self._callFUT(wflist, context)
        self.assertEqual(result, default)

    def test_context_not_None_elector_not_None_interface_found(self):
        workflow = object()
        default = object()
        context = object()
        def elector(context):
            return True
        wflist = [{'elector':elector, 'workflow':workflow},
                  {'elector':None, 'workflow':default}]
        result = self._callFUT(wflist, context)
        self.assertEqual(result, workflow)

    def test_uses_first_fallback(self):
        workflow = object()
        default1 = object()
        default2 = object()
        context = object()
        def elector(context):
            return False
        wflist = [
            {'elector':None, 'workflow':default1},
            {'elector':None, 'workflow':default2},
            {'elector':elector, 'workflow':workflow},
            ]
        result = self._callFUT(wflist, context)
        self.assertEqual(result, default1)

class DummyContent:
    pass

class DummyCallbackInfo:
    def __init__(self, workflow=None, transition=None):
        self.workflow = workflow
        self.transition = transition or {}
        
        
