API Documentation for repoze.workflow
=====================================

.. _workflow_module:

:mod:`repoze.workflow`
----------------------

.. automodule:: repoze.workflow

  The get_workflow API is the primary API:

  .. autofunction:: get_workflow(content_type, type, context=None)

  Workflow objects returned by get_workflow implement the following
  interface:

  .. autointerface:: repoze.workflow.interfaces.IWorkflow

  The single exception defined as an API by :mod:`repoze.workflow` is:

  .. autoclass:: WorkflowError

