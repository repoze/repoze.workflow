Using a Configured Workflow
===========================

Once a workflow has been configured via :term:`ZCML`, and you've got
that ZCML included in your application, you can begin to use it in
your application's code.

Getting a Workflow
------------------

You can obtain a workflow object using the ``get_workflow`` API:

.. code-block:: python
   :linenos:

   class Content(object):
       pass

   from repoze.bfg.workflow import get_workflow

   get_workflow(Content, 'security')

If a registration has been made that would associate the ``Content``
class above with the workflow, a workflow object is returned.

You can also pass a ``context`` argument into ``get_workflow`` for
purposes of obtaining a more specific workflow for a particular
context (see the ``container_type`` attribute of the ``workflow`` tag
in :ref:`configuration`):

.. code-block:: python
   :linenos:

   class Content(object):
       pass

   from repoze.bfg.workflow import get_workflow

   get_workflow(Content, 'security', context=someotherobject)

If there is a more specific workflow matching the interface associated
with ``someotherobject`` (or its traversal parents), that workflow
will be chosen first.

Workflow Objects
----------------

Workflow objects can be used to initialize and transition content.

Here is how you initialize a piece of content to the initial workflow
state:

.. code-block:: python
   :linenos:

   workflow.initialize(content)


Here is how you transition a piece of content using a particular
transition name:

.. code-block:: python
   :linenos:

   workflow.transition(content, 'to_public')

Here is how you transition a piece of content to a particular state
(there must be a valid transition to this state from its current
state):

.. code-block:: python
   :linenos:

   workflow.transition_to_state(content, request, 'public')

You can obtain available state information from a content object using
the ``state_info`` method:

.. code-block:: python
   :linenos:

   state_info = workflow.state_info(content, request)

You can also obtain state information about a nonexistent object
(essentially about the workflow itself rather than any particular
content object) using ``state_info``:

.. code-block:: python
   :linenos:

   state_info = workflow.state_info(None, request)

You can obtain transition information for a piece of content using the
``get_transitions`` API:

.. code-block:: python
   :linenos:

   info = workflow.get_transitions(context, request)
