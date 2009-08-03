.. _glossary:

============================
Glossary
============================

.. glossary::

  ZCML
    `Zope Configuration Markup Language
    <http://www.muthukadan.net/docs/zca.html#zcml>`_, the XML dialect
    used to configure repoze.workflow workflows declaratively.
  Callback
    A Python callable which accepts two arguments: a content object
    and a transition dictionary.  Callbacks are used to customize
    content objects during transitions.
  Interface
    A `Zope interface <http://pypi.python.org/pypi/zope.interface>`_
    object.  In :mod:`repoze.workflow`, an interface may be attached
    to an content object in order to identify that the object is "of a
    content type".  That interface may then be used as the "content
    type" in a workflow definition and as the content type argument to
    ``get_workflow``.
  ``repoze.bfg``
    A `Python web framework <http://bfg.repoze.org>`_.

