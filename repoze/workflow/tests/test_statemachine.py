import unittest
from zope.component.testing import PlacelessSetup

class StateMachineTests(unittest.TestCase, PlacelessSetup):
    def setUp(self):
        PlacelessSetup.setUp(self)

    def tearDown(self):
        PlacelessSetup.tearDown(self)

    def _getTargetClass(self):
        from repoze.lemonade.statemachine import StateMachine
        return StateMachine

    def _makeOne(self, attr='state', initial_state=None):
        klass = self._getTargetClass()
        return klass(attr, initial_state)

    def test_add(self):
        sm = self._makeOne()
        sm.add('start', 'add', 'adding', None)
        sm.add('start', 'get', 'getting', None)
        self.assertEqual(sm.states[('start', 'add')], ('adding', None))
        self.assertEqual(sm.states[('start', 'get')], ('getting', None))

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

    def test_execute(self):
        sm = self._makeOne(initial_state='pending')
        args = []
        def dummy(state, newstate, transition_id, context):
            args.append((state, newstate, transition_id, context))
        sm.add('pending', 'publish', 'published', dummy)
        sm.add('pending', 'reject', 'private', dummy)
        sm.add('published', 'retract', 'pending', dummy)
        sm.add('private', 'submit', 'pending', dummy)
        sm.add('pending', None, 'published', dummy)
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
        from repoze.lemonade.statemachine import StateMachineError
        self.assertRaises(StateMachineError, sm.execute, ob, 'nosuch')
