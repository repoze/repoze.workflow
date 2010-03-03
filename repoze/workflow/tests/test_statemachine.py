import unittest

class StateMachineTests(unittest.TestCase):

    def _getTargetClass(self):
        from repoze.workflow.statemachine import StateMachine
        return StateMachine

    def _makeOne(self, attr='state', **kw):
        klass = self._getTargetClass()
        return klass(attr, **kw)

    def test_add(self):
        sm = self._makeOne()
        sm.add('start', 'add', 'adding', None)
        sm.add('start', 'get', 'getting', None)
        self.assertEqual(sm.states[('start', 'add')], ('adding', None, {}))
        self.assertEqual(sm.states[('start', 'get')], ('getting', None, {}))

    def test_add_with_kw(self):
        sm = self._makeOne()
        sm.add('start', 'add', 'adding', None, a=1)
        sm.add('start', 'get', 'getting', None, b=2)
        self.assertEqual(sm.states[('start', 'add')], ('adding', None, {'a':1}))
        self.assertEqual(sm.states[('start', 'get')],('getting', None, {'b':2}))

    def test_add_in_separate_instance_does_not_pollute(self):
        sm1 = self._makeOne()
        sm2 = self._makeOne()
        sm1.add('start', 'add', 'adding', None)
        sm1.add('start', 'get', 'getting', None)
        self.assertEqual(len(sm2.states), 0)

    def test_transitions(self):
        sm = self._makeOne(initial_state='pending')
        sm.add('pending', 'publish', 'published', None)
        sm.add('pending', 'reject', 'private', None)
        sm.add('published', 'retract', 'pending', None)
        sm.add('private', 'submit', 'pending', None)
        sm.add('pending', None, 'published', None)
        ob = ReviewedObject()
        self.assertEqual(sorted(sm.transitions(ob)), [None,'publish', 'reject'])
        self.assertEqual(sorted(sm.transitions(ob, from_state='private')),
                         ['submit'])
        ob.state = 'published'
        self.assertEqual(sorted(sm.transitions(ob)), ['retract'])

    def test_transition_info(self):
        sm = self._makeOne(initial_state='pending')
        sm.add('pending', 'publish', 'published', None, a=1)
        sm.add('pending', 'reject', 'private', None, b=2)
        sm.add('published', 'retract', 'pending', None, c=3)
        sm.add('private', 'submit', 'pending', None, d=4)
        sm.add('pending', None, 'published', None, e=5)
        ob = ReviewedObject()
        info = sorted(sm.transition_info(ob))
        self.assertEqual(len(info), 3)
        self.assertEqual(
            info[0],
            {'a': 1, 'from_state': 'pending',
             'to_state': 'published', 'transition_id': 'publish'})
        self.assertEqual(
            info[1],
            {'b':2, 'from_state': 'pending',
             'to_state': 'private', 'transition_id': 'reject'})
        self.assertEqual(
            info[2],
            {'e':5, 'from_state': 'pending',
             'to_state': 'published', 'transition_id': None})
        ob.state = 'published'
        info = sorted(sm.transition_info(ob))
        self.assertEqual(len(info), 1)
        self.assertEqual(
            info[0],
             {'c': 3, 'from_state': 'published',
              'to_state': 'pending', 'transition_id': 'retract'})

    def test_execute_use_add(self):
        sm = self._makeOne(initial_state='pending')
        args = []
        def dummy(state, newstate, transition_id, context, **kw):
            args.append((state, newstate, transition_id, context, kw))
        sm.add('pending', 'publish', 'published', dummy, a=1)
        sm.add('pending', 'reject', 'private', dummy, b=2)
        sm.add('published', 'retract', 'pending', dummy, c=3)
        sm.add('private', 'submit', 'pending', dummy, d=4)
        sm.add('pending', None, 'published', dummy, e=5)
        ob = ReviewedObject()
        sm.execute(ob, 'publish')
        self.assertEqual(ob.state, 'published')
        sm.execute(ob, 'retract')
        self.assertEqual(ob.state, 'pending')
        sm.execute(ob, 'reject')
        self.assertEqual(ob.state, 'private')
        sm.execute(ob, 'submit')
        self.assertEqual(ob.state, 'pending')
        # catch-all
        sm.execute(ob, None)
        self.assertEqual(ob.state, 'published')
        self.assertEqual(len(args), 5)
        self.assertEqual(args[0],
                         ('pending', 'published', 'publish', ob, {'a':1}))
        self.assertEqual(args[1],
                         ('published', 'pending', 'retract', ob, {'c':3}))
        self.assertEqual(args[2],
                         ('pending', 'private', 'reject', ob, {'b':2}))
        self.assertEqual(args[3],
                         ('private', 'pending', 'submit', ob, {'d':4}))
        self.assertEqual(args[4],
                         ('pending', 'published', None, ob, {'e':5}))
        from repoze.workflow.statemachine import StateMachineError
        self.assertRaises(StateMachineError, sm.execute, ob, 'nosuch')

    def test_execute_use_constructor(self):
        args = []
        def dummy(state, newstate, transition_id, context, **kw):
            args.append((state, newstate, transition_id, context, kw))
        states = {('pending', 'publish'): ('published', dummy, {}),
                  ('pending', 'reject'): ('private', dummy, {}),
                  ('published', 'retract'): ('pending', dummy, {}),
                  ('private', 'submit'): ('pending', dummy, {}),
                  ('pending', None): ('published', dummy, {}),}
        sm = self._makeOne(states=states, initial_state='pending')
        ob = ReviewedObject()
        sm.execute(ob, 'publish')
        self.assertEqual(ob.state, 'published')
        sm.execute(ob, 'retract')
        self.assertEqual(ob.state, 'pending')
        sm.execute(ob, 'reject')
        self.assertEqual(ob.state, 'private')
        sm.execute(ob, 'submit')
        self.assertEqual(ob.state, 'pending')
        # catch-all
        sm.execute(ob, None)
        self.assertEqual(ob.state, 'published')
        self.assertEqual(len(args), 5)
        self.assertEqual(args[0], ('pending', 'published', 'publish', ob, {}))
        self.assertEqual(args[1], ('published', 'pending', 'retract', ob, {}))
        self.assertEqual(args[2], ('pending', 'private', 'reject', ob, {}))
        self.assertEqual(args[3], ('private', 'pending', 'submit', ob, {}))
        self.assertEqual(args[4], ('pending', 'published', None, ob, {}))
        from repoze.workflow.statemachine import StateMachineError
        self.assertRaises(StateMachineError, sm.execute, ob, 'nosuch')

    def test_execute_None_match(self):
        sm = self._makeOne(initial_state='pending')
        args = []
        def dummy(state, newstate, transition_id, context, **kw):
            args.append((state, newstate, transition_id, context, kw))
        sm.add('pending', None, 'published', dummy)
        ob = ReviewedObject()
        sm.execute(ob, 'publish')
        self.assertEqual(ob.state, 'published')

    def test_fail_before_transition(self):
        from repoze.workflow.statemachine import StateMachine
        from repoze.workflow.statemachine import StateMachineError
        
        class FailBeforeTransition(StateMachine):
            def before_transition(self, a, b, c, d):
                raise StateMachineError

        def dummy(state, newstate, transition_id, context):
            """ """

        states = {('from', 'do_it'):('to', dummy, {})}
        sm = FailBeforeTransition('state', states, initial_state='from')
        ob = ReviewedObject()
        self.assertRaises(StateMachineError, sm.execute, ob, 'do_it')
        self.assertEqual(hasattr(ob, 'state'), False)
        self.assertEqual(sm.state_of(ob), 'from')

class ReviewedObject:
    pass
