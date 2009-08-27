Using Configured Workflows
==========================

Once one or more workflows has been configured via :term:`ZCML`, and
you've got that ZCML executed, you can begin to use it in your
application's code.

Getting a Workflow
------------------

You can obtain a workflow object using the ``get_workflow`` API:

.. code-block:: python
   :linenos:

   class Content(object):
       pass

   from repoze.workflow import get_workflow

   get_workflow(Content, 'security')

The first argument is the content type (a class or :term:`interface`).
The second argument you pass to ``get_workflow`` is a workflow "type"
(the string attached to the ``type`` attribute of a workflow
definition).

If a workflow has been created in ZCML that would associate the
``Content`` class above with the workflow, a workflow object is
returned.

You can also pass a ``context`` argument into ``get_workflow`` for
purposes of obtaining a more specific workflow for a particular
context (see the ``elector`` attribute of the ``workflow`` tag in
:ref:`configuration`):

.. code-block:: python
   :linenos:

   class Content(object):
       pass

   from repoze.workflow import get_workflow

   get_workflow(Content, 'security', context=someotherobject)

When a context is passed, if there is a more specific workflow
matching the interface associated with ``someotherobject`` based on an
ordered match against each workflow that matches this content type
with an elector, that workflow will be chosen first.  Otherwise, a
workflow that matches the content type without an elector will be
chosen.

If no workflow matches the content type, ``None`` is returned from
``get_workflow``.

Understanding Workflow Precedence
---------------------------------

In general, the "first, most-specific" workflow for a given set of
arguments is returned from the ``get_workflow`` API.  This section
describes how "first, most-specific" is computed.

Since more than one workflow can be defined for a given content type /
workflow type pair, it's important to be able to understand how "the
workflow" for a given call to ``get_workflow`` is found. The workflow
found for a call to ``get_workflow`` will depend on these things:

- The content type.

- The workflow type.

- The context.

- The relative ordering of workflows within the ZCML configuration
  file.

When multiple workflows are found for a particular content type /
workflow type pair:

If no ``context`` is passed or ``context`` is None:

- All workflows with an elector are ignored.

- The first workflow (as defined in ZCML order) without an elector
  within the configuration is returned as "the workflow".

If a ``context`` is passed:

- all workflows *with an elector* are consulted first in the order in
  which they are defined in ZCML.  During this processing, if any
  elector returns ``True``, this workflow as returned as ``the
  workflow``.

- If no workflow with an elector exists in the configuration or no
  elector-having-workflow elector returns ``True`` during the above
  step, the *first* workflow defined in ZCML order that does not
  possess an elector is returned as "the workflow".

In general, you should define any overlapping workflows within ZCML in
most-specific to least-specific order in order for ``get_workflow`` to
behave as most people might expect.

Workflow Objects
----------------

Workflow objects can be used to initialize and transition content.  To
use some of these APIs you need a "request" object.  This object is
available in :mod:`repoze.bfg` views as the "request" parameter to the
view.  Your web framework may have another kind of request object
obtained from another place.  If none of your workflows use a
``permission_checker``, you can pass ``None`` as the request object.

Here is how you initialize a piece of content to the initial workflow
state:

.. code-block:: python
   :linenos:

   workflow.initialize(content)

No permission is ever required to initialize a piece of content, so
the API does not accept a request.

Here is how you transition a piece of content using a particular
transition name:

.. code-block:: python
   :linenos:

   workflow.transition(content, request, 'to_public')

Here is how you transition a piece of content to a particular state
(there must be a valid transition to this state from its current
state):

.. code-block:: python
   :linenos:

   workflow.transition_to_state(content, request, 'public')

.. note::

  ``workflow.transition_to_state`` calls ``workflow.initialize`` if
  the content has not already been initialized.

You can obtain available state information from a content object using
the ``state_info`` method:

.. code-block:: python
   :linenos:

   state_info = workflow.state_info(content, request)

``state_info`` above will be a list of dictonaries.  Each dictionary
will have the following keys:

name

  The state's name.

title

  The state's title (or the state name if this state has no title).

data

  State data, containing ``callback``, and any arbitrary key value
  pairs associated with the state through use of the ``key`` tag in
  ZCML.

initial

  True if this state is the initial state for this workflow.

current

  True if the content object supplied is in this state.

transitions

  A sequence of transition dictionaries; if any of the transitions is
  not allowed due to a permission violation, it will not show up in
  this list.

You can also obtain state information about a nonexistent object
(essentially about the workflow itself rather than any particular
content object) using ``state_info``:

.. code-block:: python
   :linenos:

   state_info = workflow.state_info(None, request, context=someotherobject)

This will return the same list of dictionaries, except the ``current``
flag will always be false.  Permissions used to compute the allowed
transitions will be computed against the ``context`` (the ``context``
will be passed to the permission checker instead of any particular
content object).

You can obtain transition information for a piece of content using the
``get_transitions`` API:

.. code-block:: python
   :linenos:

   info = workflow.get_transitions(context, request)

You can reset the workflow state of an object using the ``reset`` API:

.. code-block:: python
   :linenos:

   newstate = workflow.reset(context)

You can test if an object is in any state at all using the
``has_state`` API:

.. code-block:: python
   :linenos:

   if workflow.has_state(context):
      # do something

You can find the workflow state of an existing object using the using
the ``state_of`` API:

.. code-block:: python
   :linenos:

   state = workflow.state_of(content)

.. note::

  Calling the ``state_of`` API will initialize the object if it hasn't
  already been initialized.

Here's usage of the API in context on a :term:`repoze.bfg`
self-posting "add content" view.  It's assumed that the
``add_content.pt`` form rendered uses the state information returned
from ``state_info`` to render available state names to a set of radio
buttons or a dropdown single-select list; the form post will return
this value in the ``security_state`` request parameter.

.. code-block:: python
   :linenos:

    from repoze.workflow import get_workflow
    from repoze.bfg.chameleon_zpt import render_template_to_response

    from webob.exc import HTTPFound

    class Content:
        pass

    def add_content_view(context, request):

        workflow = get_workflow(Content, 'security', context)
        security_states = workflow.state_info(None, request)

        if 'form.submitted' in request.POST:
            content = Content(request['title'])
            # if this were real, we'd persist content
            workflow.transition_to_state(content, request,
                                         request['security_state'])
            return HTTPFound(location='/')

        return render_template_to_response(
            'add_content.pt',
            security_states = security_states,
            )

Here's usage of the API in context on a :term:`repoze.bfg`
self-posting "edit content" view.  It's assumed that the
``edit_content.pt`` form rendered uses the state information returned
from ``state_info`` to render available state names to a set of radio
buttons or a dropdown single-select list; the form post will return
this value in the ``security_state`` request parameter.  It's also
assumed that the "context" object is a ``Content`` instance.

.. code-block:: python
   :linenos:

    from repoze.workflow import get_workflow
    from repoze.bfg.chameleon_zpt import render_template_to_response

    from webob.exc import HTTPFound

    class Content:
        pass

    def edit_content_view(context, request):
        workflow = get_workflow(Content, 'security', context)
        security_states = workflow.state_info(None, request)

        if 'form.submitted' in request.POST:
            # if this were real, we'd persist content
            workflow.transition_to_state(context, request,
                                         request['security_state'])
            return HTTPFound(location='/')

        return render_template_to_response(
            'edit_content.pt',
            security_states = security_states,
            )
