Documentation for repoze.workflow
==================================

State Machine
-------------

:mod:`repoze.workflow` has a very simple state machine implementation
that can be used for workflow-like state transitions.  To use the
state machine, import it within your code and initialize it with a
state attr, a states dictionary, and initial state.  Alternately (or
later), state declarations can be added to the state map using the add
method::

  >>> from repoze.workflow.statemachine import StateMachine
  >>> sm = StateMachine('review_state', initial_state='pending') # attr name, initial state
  >>> def transition(from_state, to_state, action, ob):
  >>>     print action
  >>> sm.add('pending', 'publish', 'published', transition)
  >>> sm.add('pending', 'reject', 'private', transition)
  >>> sm.add('published', 'retract', 'pending', transition)
  >>> sm.add('private', 'submit', 'pending', transition)

The state machine is now ready to use::

  >>> class ReviewedObject:
  >>>     pass
  >>> ob = ReviewedObject()
  >>> sm.transitions(ob, from_state='pending')
  ['publish', 'reject']
  >>> sm.transitions(ob)  # from_state defaults to current or initial state
  ['publish', 'reject']
  >>> ob.review_state = 'published'
  >>> sm.transitions(ob)
  ['retract']
  >>> sm.transitions(ob, from_state='private')
  ['submit']
  >>> sm.execute(ob, 'publish')
  'publish'
  >>> ob.review_state
  'published'
  >>> sm.execute(ob, 'retract')
  'retract'
  >>> ob.review_state
  'pending'
  >>> sm.state_of(ob) # alternate mechanism (always works)
  'pending'

The state machine object does not handle persistence at all.  

- If you want to use a database or other non-code mechanism to persist
  the state machine's state map, you can subclass the StateMachine
  class.  It is highly recommended that all transition functions be
  defined at module scope to facilitate StateMachine persistence.

- To persist a given object's state, persist the specified state_attr
  attribute on the object (or implement this as a property and delegate
  to some other storage mechanism).

.. toctree::
   :maxdepth: 2

   api.rst
   changes.rst


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
