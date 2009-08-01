.. _configuration:

Configuration
=============

:mod:`repoze.workflow` workflows are configured using a
combination of :term:`ZCML` and Python.

Here's an example of the ZCML portion of a :mod:`repoze.workflow`
workflow.

.. code-block:: xml
   :linenos:

   <configure xmlns="http://namespaces.repoze.org/bfg">

   <include package="repoze.workflow" file="meta.zcml"/>

   <workflow
      name="theworkflow"
      state_attr="state"
      initial_state="private"
      content_type=".dummy.IContent"
      permission_checker="repoze.bfg.security.has_permission"
      >

      <state name="private" 
         callback=".dummy.callback">
           <key name="title" value="Private"/>
           <key name="description" value="Nobody can see it"/>
      </state>

      <state name="public"
         callback=".dummy.callback">
        <key name="title" value="Public"/>
        <key name="description" value="Everybody can see it"/>
      </state>

      <transition
         name="public_to_private"
         callback=".dummy.callback"
         from_state="public"
         to_state="private"
         permission="moderate"
         />

      <transition
         name="private_to_public"
         callback=".dummy.callback"
         from_state="private"
         to_state="public"
         permission="moderate"
         />

   </workflow>
         
   </configure>

This configuration defines *states* and *transitions*.  A state is an
"end point" associated with a piece of content.  A transition is a
path from one state to another state (unidirectional).

A state can be associated with a :term:`callback`.  A callback is a
Python callable that accepts two arguments: a ``content`` and a
``transition``.  The content object is the object being workflowed.
The transition is a dictionary containing information about the
transition currently being undergone.

A transition may also be associated with a callback.  The callback
associated with a transition is called as the transition is executed.
The execution of a transition callback happens *before* the execution
the state callback of the target state.

The ``workflow`` Tag
---------------------

The ``workflow`` ZCML tag defines a workflow.  It has the following
attributes:

``name``

  The workflow name.  This is attribute is required.

``initial_state``

  The initial state of content initialized into the workflow.  This
  attribute is required.  The details of the state referred to in this
  attribute *must* be declared via a ``state`` tag within the workflow
  definition.  If it is not, a configuration error will be raised at
  startup time.

``state_attr``

  The name of the attribute of the content object that will be used to
  retain the workflow state name.  This attribute is required.

``content_type``

  A Python dotted-name referring to a class or a Zope interface.  This
  workflow will be considered when looked up via ``get_workflow`` if
  the ``content_type`` argument to ``get_workflow`` is an instance of
  this class or implements this interface (directly or indirectly).
  This attribute is not required.  If it is not supplied, the workflow
  will be considered for all content types.

``elector``

  A Python dotted-name referring to a :term:`callback`.  When
  ``get_workflow`` is called with a ``context`` argument, if a
  workflow names an ``elector`` the workflow will be considered as a
  candidate workflow if the elector is called and returns true.
  ``elector`` allows an object to participate in one workflow or
  another based on its context.

``permission_checker``

  A Python dotted-name referring to a permission checking function.
  This function should accept three arguments: ``permission`` (a
  string), ``context`` and ``reqeuest``.  It should return true if the
  current user implied by the request has the permission in the
  ``context``, false otherwise.

A ``workflow`` tag may contain ``transition`` and ``state`` tags.  A
workflow declared via ZCML is unique amongst all workflows defined if
the combination of its ``name``, its ``content_type`` and its
``container_type`` are unique.  If the combination of these three
attributes is the same for any two workflows defined in ZCML, a
configuration conflict error will be raised at startup time.

The ``state`` Tag
-----------------

A ``state`` tag is a subtag of a ``workflow`` tag.  It defines a state
in a workflow.  A callback may be associated with that state.  When a
callback is associated with a state, the code in the callback is run,
presumably to mutate the content object being transitioned.

The state tag has these attributes:

``name``

  The state name.  This attribute is required.  Each state name must
  be unique within a given workflow.

``title``

  The state title.  This attribute is optional.  If the title is not
  supplied, it will be presented as ``None`` in the representation of
  states used programmatically (except in the case of usage of the
  ``IWorkflow.state_info`` API; it presents the title as the same
  value as ``state_name`` if the title attribute is None).

``callback``

  A Python dotted name that points at a callable object.  This
  attribute is not required.  If it is omitted, no callback will be
  associated with this state.  See :ref:`callbacks` for more
  information about callbacks.

The ``transition`` Tag
----------------------

A ``transition`` tag is a subtag of a ``workflow`` tag.  It defines a
transition between two states in a workflow.  A callback may be
associated with a transition.  When a callback is associated with a
transition, the code in the callback is run, presumably to mutate the
content object being transitioned.  A transition callback is called
before the state callback (if any) of the target state.

The ``transition`` tag accepts the following attributes:

``name``

  The transition name (a string).  This attribute is required.  All
  transition names within a workflow must be unique.

``from_state``

  The name of the "from" state for this transition.  This attribute is
  required.  It must match one of the state names defined in a
  previous ``state`` tag.

``to_state``

  The name of the "to" state for this transition.  This attribute is
  required.  It must match one of the state names defined in a
  previous ``state`` tag.

``permission``

  The permission name (a string) associated with this transition.
  Before the workflow machinery attempts to execute a transition, this
  permission is checked against the current set of credentials and the
  content object using the workflow's ``permission_checker``.  If the
  transition cannot be executed because the user does not possess this
  permission in that set of circumstates, a ``WorkflowError`` is
  raised.  This attribute is optional.  If it is not supplied, no
  permission is associated with this transition, and it may be
  executed without respect to the current user's credentials.

``callback``

  A Python dotted name which points at a "callback".  See
  :ref:`callbacks`.

.. _callbacks:

Callbacks
---------

Callback objects (both transition callbacks and state callbacks)
should accept two positional arguments: ``content`` and
``transition``.  The ``transition`` argument will be a dictionary
representing the current transition.  The ``content`` argument will be
the content object that is being transitioned.


Executing a Configuration
-------------------------

To execute a ZCML-configured set of workflows, do the following.

If your ZCML file is in a package (and contains package-relative
dotted names), use the following:

.. code-block:: python
   :linenos:

   import mypackage

   from zope.configuration import xmlconfig
   xmlconfig.file('configure.zcml', mypackage, execute=True)

If your ZCML file does not live in a package (and does not contain
package-relative dotted names), use the following:

.. code-block:: python
   :linenos:

   from zope.configuration import xmlconfig
   xmlconfig.file('/path/to/configure.zcml', execute=True)

