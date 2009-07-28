import unittest

class StateMachineTests(unittest.TestCase):

    def _getTargetClass(self):
        from repoze.bfg.workflow.statemachine import StateMachine
        return StateMachine

    def _makeOne(self, attr='state', transitions=None, initial_state=None,
                 initializer=None):
        klass = self._getTargetClass()
        return klass(attr, transitions, initial_state, initializer)

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
        self.assertEqual(len(sm._transitions), 2)
        transitions = sm._transitions
        self.assertEqual(transitions[0]['name'], 'make_public')
        self.assertEqual(transitions[0]['from_state'], 'private')
        self.assertEqual(transitions[0]['to_state'], 'public')
        self.assertEqual(transitions[0]['callback'], None)
        self.assertEqual(transitions[0]['a'], 1)
        self.assertEqual(transitions[1]['name'], 'make_private')
        self.assertEqual(transitions[1]['from_state'], 'public')
        self.assertEqual(transitions[1]['to_state'], 'private')
        self.assertEqual(transitions[1]['callback'], None)
        self.assertEqual(transitions[1]['b'], 2)

        self.assertEqual(len(sm._state_order), 2)

    def _add_transitions(self, sm, callback=None):
        sm._transitions.extend(
            [
            dict(name='publish', from_state='pending', to_state='published',
                 callback=callback),
            dict(name='reject', from_state='pending', to_state='private',
                 callback=callback),
            dict(name='retract', from_state='published', to_state='pending',
                 callback=callback),
            dict(name='submit', from_state='private', to_state='pending',
                 callback=callback),
            ]
            )
        if not sm._state_order:
            sm._state_order = ['pending', 'published', 'private']
        sm._state_data.setdefault('pending', {})
        sm._state_data.setdefault('published', {})
        sm._state_data.setdefault('private', {})

    def test_transitions_default_from_state(self):
        sm = self._makeOne(initial_state='pending')
        self._add_transitions(sm)
        ob = ReviewedObject()
        result = sm.transitions(ob)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'publish')
        self.assertEqual(result[1]['name'], 'reject')

    def test_transitions_overridden_from_state(self):
        sm = self._makeOne(initial_state='pending')
        self._add_transitions(sm)
        ob = ReviewedObject()
        result = sm.transitions(ob, from_state='private')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'submit')

    def test_transitions_context_has_state(self):
        sm = self._makeOne(initial_state='pending')
        self._add_transitions(sm)
        ob = ReviewedObject()
        ob.state = 'published'
        result = sm.transitions(ob)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'retract')

    def test_execute(self):
        sm = self._makeOne(initial_state='pending')
        args = []
        def dummy(context, transition):
            args.append((context, transition))
        self._add_transitions(sm, callback=dummy)
        ob = ReviewedObject()
        sm.execute(ob, 'publish')
        self.assertEqual(ob.state, 'published')
        sm.execute(ob, 'retract')
        self.assertEqual(ob.state, 'pending')
        sm.execute(ob, 'reject')
        self.assertEqual(ob.state, 'private')
        sm.execute(ob, 'submit')
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


    def test_execute_error(self):
        sm = self._makeOne(initial_state='pending')
        ob = ReviewedObject()
        from repoze.bfg.workflow.statemachine import StateMachineError
        self.assertRaises(StateMachineError, sm.execute, ob, 'nosuch')

    def test_execute_guard(self):
        def guard(context, transition):
            raise ValueError
        sm = self._makeOne(initial_state='pending')
        self._add_transitions(sm)
        ob = ReviewedObject()
        self.assertRaises(ValueError, sm.execute, ob, 'publish', (guard,))

    def test_transition_to_state(self):
        sm = self._makeOne(initial_state='pending')
        args = []
        def dummy(context, transition):
            args.append((context, transition))
        self._add_transitions(sm, callback=dummy)
        ob = ReviewedObject()
        ob.state = 'pending'
        sm.transition_to_state(ob, 'published')
        self.assertEqual(ob.state, 'published')
        sm.transition_to_state(ob, 'pending')
        self.assertEqual(ob.state, 'pending')
        sm.transition_to_state(ob, 'private')
        self.assertEqual(ob.state, 'private')
        sm.transition_to_state(ob, 'pending')

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

    def test_transition_to_state_error(self):
        sm = self._makeOne(initial_state='pending')
        ob = ReviewedObject()
        from repoze.bfg.workflow.statemachine import StateMachineError
        self.assertRaises(StateMachineError, sm.transition_to_state, ob,
                          'nosuch')

    def test_transition_to_state_skip_same_false(self):
        sm = self._makeOne(initial_state='pending')
        ob = ReviewedObject()
        from repoze.bfg.workflow.statemachine import StateMachineError
        self.assertRaises(StateMachineError, sm.transition_to_state, ob,
                          'pending', (), False)

    def test_transition_to_state_skip_same_true(self):
        sm = self._makeOne(initial_state='pending')
        ob = ReviewedObject()
        from repoze.bfg.workflow.statemachine import StateMachineError
        self.assertEqual(sm.transition_to_state(ob, 'pending', (), True), None)

    def test_state_info_with_title(self):
        sm = self._makeOne(initial_state='pending')
        sm.add_state_info('pending', title='Pending')
        self._add_transitions(sm)
        ob = ReviewedObject()
        ob.state = 'pending'
        result = sm.state_info(ob)
        
        state = result[0]
        self.assertEqual(state['initial'], True)
        self.assertEqual(state['current'], True)
        self.assertEqual(state['name'], 'pending')
        self.assertEqual(state['title'], 'Pending')
        self.assertEqual(state['data'], {'title':'Pending'})
        self.assertEqual(len(state['transitions']), 0)


    def test_state_info_pending(self):
        sm = self._makeOne(initial_state='pending')
        sm.add_state_info('pending', desc='Pending')
        sm.add_state_info('published', desc='Published')
        sm.add_state_info('private', desc='Private')
        self._add_transitions(sm)
        ob = ReviewedObject()
        ob.state = 'pending'
        result = sm.state_info(ob)
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


    def test_state_info_published(self):
        sm = self._makeOne(initial_state='pending')
        sm.add_state_info('pending', desc='Pending')
        sm.add_state_info('published', desc='Published')
        sm.add_state_info('private', desc='Private')
        self._add_transitions(sm)
        ob = ReviewedObject()
        ob.state = 'published'
        result = sm.state_info(ob)
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

    def test_state_info_private(self):
        sm = self._makeOne(initial_state='pending')
        sm.add_state_info('pending', desc='Pending')
        sm.add_state_info('published', desc='Published')
        sm.add_state_info('private', desc='Private')
        self._add_transitions(sm)
        ob = ReviewedObject()
        ob.state = 'private'
        result = sm.state_info(ob)
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
        sm = self._makeOne(initial_state='pending', initializer=None)
        ob = ReviewedObject()
        sm.initialize(ob)
        self.assertEqual(ob.state, 'pending')
        
    def test_initialize_with_initializer(self):
        def initializer(context):
            context.initialized = True
        sm = self._makeOne(initial_state='pending', initializer=initializer)
        ob = ReviewedObject()
        sm.initialize(ob)
        self.assertEqual(ob.state, 'pending')
        self.assertEqual(ob.initialized, True)
        

class ReviewedObject:
    pass
