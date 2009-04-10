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
        self.assertEqual(sm.states[('start', 'add')], ('adding', None))
        self.assertEqual(sm.states[('start', 'get')], ('getting', None))

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
        class ReviewedObject:
            pass
        ob = ReviewedObject()
        self.assertEqual(sorted(sm.transitions(ob)), ['publish', 'reject'])
        self.assertEqual(sorted(sm.transitions(ob, from_state='private')),
                         ['submit'])
        ob.state = 'published'
        self.assertEqual(sorted(sm.transitions(ob)), ['retract'])

    def test_execute_use_add(self):
        sm = self._makeOne(initial_state='pending')
        args = []
        def dummy(state, newstate, transition_id, context):
            args.append((state, newstate, transition_id, context))
        sm.add('pending', 'publish', 'published', dummy)
        sm.add('pending', 'reject', 'private', dummy)
        sm.add('published', 'retract', 'pending', dummy)
        sm.add('private', 'submit', 'pending', dummy)
        sm.add('pending', None, 'published', dummy)
        self._do_execute(sm, args)

    def test_execute_use_constructor(self):
        args = []
        def dummy(state, newstate, transition_id, context):
            args.append((state, newstate, transition_id, context))
        states = {('pending', 'publish'): ('published', dummy),
                  ('pending', 'reject'): ('private', dummy),
                  ('published', 'retract'): ('pending', dummy),
                  ('private', 'submit'): ('pending', dummy),
                  ('pending', None): ('published', dummy),}
        sm = self._makeOne(states=states, initial_state='pending')
        self._do_execute(sm, args)

    def _do_execute(self, sm, args):
        class ReviewedObject:
            pass
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
        self.assertEqual(args[0], ('pending', 'published', 'publish', ob))
        self.assertEqual(args[1], ('published', 'pending', 'retract', ob))
        self.assertEqual(args[2], ('pending', 'private', 'reject', ob))
        self.assertEqual(args[3], ('private', 'pending', 'submit', ob))
        self.assertEqual(args[4], ('pending', 'published', None, ob))
        from repoze.workflow.statemachine import StateMachineError
        self.assertRaises(StateMachineError, sm.execute, ob, 'nosuch')

    def test_fail_before_transition(self):
        from repoze.workflow.statemachine import StateMachine
        from repoze.workflow.statemachine import StateMachineError
        
        class FailBeforeTransition(StateMachine):
            def before_transition(self, a, b, c, d):
                raise StateMachineError

        class ReviewedObject:
            pass

        def dummy(state, newstate, transition_id, context):
            pass

        states = {('from', 'do_it'):('to', dummy)}
        sm = FailBeforeTransition('state', states, initial_state='from')
        ob = ReviewedObject()
        self.assertRaises(StateMachineError, sm.execute, ob, 'do_it')
        self.assertEqual(hasattr(ob, 'state'), False)
        self.assertEqual(sm.state_of(ob), 'from')
