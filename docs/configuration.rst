.. _configuration:

Configuration
=============

Configuring a :mod:`repoze.workflow` workflow requires an
understanding of its terminology.

A workflow's *type* is a string, such as "security".  You use this
identifier to look up the workflow later.  A workflow's *content type*
is a Python class or :term:`interface`.  You also use this value to
look up a workflow later.  An *elector* is a function which returns
true or false; it operates on a "context" which you pass to a function
named ``get_workflow`` which looks up the workflow.  The *state_attr*
of a workflow is the attribute of content objects which will be
managed by the workflow.  The state of the content object (a string)
will be kept on this attribute.

A workflow contains *states* and *transitions*.  The main job of a
workflow is to transition objects into states.  It can also check that
a user possesses a permission before executing a transition.

A *state* is a workflow "end point" associated with a piece of
content.  A state can be associated with a :term:`callback`.  A
callback is a Python callable that accepts two arguments: a
``content`` and a ``info`` object.  The content object is the object
being workflowed.  The ``info`` object is an object which has access
to information about the transition currently being undergone, the
workflow, and other attributes.

A *transition* is the step from one state to another.  A transition
may also be associated with a callback.  The callback associated with
a transition is called as the transition is executed.  The execution
of a transition callback happens *before* the execution the state
callback of the target state.  A transition may also be associated
with a *permission* (an arbitrary string such as "administer" or
"moderate").

More than one workflow can be used simultaneously in the same system.
A workflow is unique in a system using multiple workflows if the
combination of its *type*, its *content type*, its *elector*, and its
*state_attr* are different than the combination of those attributes
configured in any other workflow.

:mod:`repoze.workflow` workflows are configured using a
combination of :term:`ZCML` and Python.

You may use ZCML to define states and transitions, instead of
composing them imperatively.

Here's an example of the ZCML portion of a :mod:`repoze.workflow`
workflow.

.. code-block:: xml
   :linenos:

   <configure xmlns="http://namespaces.repoze.org/bfg">

   <include package="repoze.workflow" file="meta.zcml"/>

   <workflow
      type="security"
      name="the workflow"
      state_attr="state"
      initial_state="private"
      content_types=".dummy.IContent"
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

The ``workflow`` Tag
---------------------

The ``workflow`` ZCML tag defines a workflow.  It has the following
attributes:

``type``

  The workflow type.  This is attribute is required.  It should be a
  string, indicating the situation in which it's used (e.g.
  "security").  Multiple workflows configured in a system may share
  the same type.

``name``

  A short name for the workflow.  This attribute is required; it should
  be a short description of the purpose of the workflow.

``description``

  A longer description (than the name) of the workflow.  This
  attribute is not required; it defaults to the empty string.

``initial_state``

  The initial state of content initialized into the workflow.  This
  attribute is required.  The details of the state referred to in this
  attribute *must* be declared via a ``state`` tag within the workflow
  definition.  If it is not, a configuration error will be raised at
  startup time.

``state_attr``

  The name of the attribute of the content object that will be used to
  retain the workflow state name.  This attribute is required.

``content_types``

  A sequence of Python dotted-names separated with space characters.
  Each dotted name refers to a class or a Zope interface.  This
  workflow will be considered as a return candidate when looked up via
  the ``get_workflow`` function if the one of the classes or
  interfaces passed as the ``content_type`` argument to
  ``get_workflow`` is an instance of one of these classes or
  implements one of these interfaces (directly or indirectly).  This
  attribute is not required.  If it is not supplied, the workflow will
  be considered for all content types.

``elector``

  A Python dotted-name referring to a :term:`callback`.  When
  ``get_workflow`` is called with a ``context`` argument, if a
  workflow names an ``elector`` the workflow will be considered as a
  candidate workflow if the elector is called and returns true.
  ``elector`` allows an object to participate in one workflow or
  another based on the ``context`` passed to ``get_workflow``.

``permission_checker``

  A Python dotted-name referring to a permission checking function.
  This function should accept three arguments: ``permission`` (a
  string), ``context`` and ``request``.  It should return ``True`` if
  the current user implied by the request has the permission in the
  ``context``, ``False`` otherwise.

A ``workflow`` tag may contain ``transition`` and ``state`` tags.  A
workflow declared via ZCML is unique amongst all workflows defined if
the combination of its ``type``, its ``content_types`` and its
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

The ``key`` Tag
---------------

The ``key`` tag can be used within a ``state`` or ``transition`` tag.
It allows you to associate arbitrary textual key/value pairs with the
state or the transition in which it is contained.  For example:

.. code-block:: python
   :linenos:

   <state name="foo">
      <key name="favorite_color" value="blue"/>
   </state>

It can also be used within a transition tag:

.. code-block:: python
   :linenos:

   <transition name="foo"
               from_state="from"
               to_state="to">
      <key name="favorite_color" value="blue"/>
   </transition>

When the ``key`` tag is used within a ``state`` tag, the key/value
pairs are accessible within the ``data`` element of each dictionary
returned by the ``workflow.state_info`` method.  When the ``key`` tag
is used within a ``transition`` tag, the key/value pair it represents
is accessible within the ``transition`` dictionary of the ``info``
object passed to a :term:`callback`, or within data obtained via
``workflow.get_transitions``.

The ``alias`` Tag
-----------------

The ``alias`` tag may only be used within a ``state`` tag.  The
``alias`` tag creates a state name alias.  If a content object has a
``state_attr`` attribute that matches the state's name *or any of its
aliases*, it will be considered to be in that state, according to
e.g. ``workflow.state_of``, etc.

.. _callbacks:

Callbacks
---------

Callback objects (both transition callbacks and state callbacks)
should accept two positional arguments: ``content`` and ``info``.  The
``info`` argument will be an object which has (at least) two
attributes:

  - ``transition``: a dictionary representing the current transition.

  - ``workflow``: the workflow object which initiated this callback

The ``content`` argument will be the content object that is being
transitioned.

Here's an example of a callback:

.. code-block:: python
   :linenos:

    def to_inherits(content, info):
        if hasattr(content, '__acl__'):
            del content.__acl__

This callback deletes an ``__acl__`` attribute from the content object
(if it exists) when it is called. 

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

