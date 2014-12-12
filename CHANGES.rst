repoze.workflow Changelog
=========================

1.0b1 (2014-12-11)
------------------

Features
~~~~~~~~

- Add support for PyPy.

- Add support for Python 3.2, 3.3, and 3.4.

- Add support for defining guard functions on transitions in ZCML (PR #5).

- Replace deprecated class-advice declarations (``implements``,
  ``classImplements``) with forward-compatible equivalent class decorators.

- Add an optional ``title`` to states (defaults to the state name).
  In ZCML, the 'title' should now be carried as an attribute of the
  '<state>' element, rather than as a '<key>' sub-element.

- Add an optional ``title`` to transitions (defaults to the transition
  name) (issue #1).

- Add a warning if a ZCML workflow directive has no ``content_types``
  (issue #4).

- Give an optional ``request`` attribute to the ``ICallbackInfo`` interface.
  It will be non-None if the transition triggering the callback is passed a
  request (PR #3).

Bugs Fixed
~~~~~~~~~~

- Include guards defined on the transition itself when checking whether a
  transition is allowed (issue #8).

Housekeeping
~~~~~~~~~~~~

- Add support for continuous integration using ``Travis-CI``.

- Add support for continuous integration using ``tox`` and ``jenkins``.

- Add ``setup.py docs`` alias (installs Sphinx and related dependencies).

- Add ``setup.py dev`` alias (installs nose, coverage, and testing
  dependencies).

Backward-Incompatible Changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Drop preservation of insertion order when listing states / transitions.

- Drop support for Python 2.4 / 2.5.

0.6.1 (2012-03-24)
------------------

- Repair packaging error (incomplete tarball in 0.6).


0.6 (2012-03-24)
----------------

- When multiple transitions exist between two states, try each transition
  until one succeeds, instead of aborting if the first fails.

- Bumped ``zope.configuration`` dependency to require >= 3.8.0:  the internal
  format of configuration actions changed to dictionaries, rather than tuples,
  and our tests make assertions which rely on the format.

- ``repoze.sphinx.autointerface`` and ``zope.testing`` are only required for
  testing and will no longer be downloaded for ``python setup.py install``;
  use ``python setup.py dev`` to get them installed (along with ``nose`` and
  ``coverage``).

- 100% test coverage

0.5 (2009-08-27)
----------------

- Major overhaul.  Older "statemachine" workflows still work, but are
  deprecated.  Workflow declarations may now be performed via ZCML.
  Documentation overhauled to reflect this fact.

0.4 (2009-06-24)
----------------

- 100% test coverage.

- Allow ``add`` method to accept arbitrary keyword arguments.  These
  keyword arguments are now passed as ``**kw`` to transition functions
  as well as ``before_transition`` and ``after_transition``.  This
  allows arbitrary metadata (such as security and UI information) to
  be associated with a transition.

- The ``transitions`` method now returns all transitions, including
  "catch-all" transitions (transitions with a transition_id of None).

- Add ``transition_info`` method to state machine, which

0.3 (2009-04-10)
----------------

- Removed mutable default arguments, to avoid polluting one state machine's
  states when adding to another.

0.2 (2009-02-20)
----------------

- Initial release. Updated README.txt and removed remnants from repoze
  package template.

0.1
---

- Unreleased
