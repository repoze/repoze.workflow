from zope.component import getSiteManager

import zope.configuration.config

from zope.configuration.fields import GlobalObject

from zope.interface import Interface
from zope.interface import implements

from zope.schema import TextLine

from repoze.bfg.workflow.workflow import Workflow
from repoze.bfg.workflow.interfaces import IWorkflow

def handler(methodName, *args, **kwargs): # pragma: no cover
    method = getattr(getSiteManager(), methodName)
    method(*args, **kwargs)

class IKeyValueDirective(Interface):
    """ The interface for a key/value pair subdirective """
    name = TextLine(title=u'key', required=True)
    value = TextLine(title=u'value', required=True)

class ITransitionDirective(Interface):
    """ The interface for a transition directive """
    name = TextLine(title=u'name', required=True)
    callback = GlobalObject(title=u'callback', required=True)
    from_state = TextLine(title=u'from_state', required=True)
    to_state = TextLine(title=u'to_state', required=True)
    permission = TextLine(title=u'permission', required=False)

class IStateDirective(Interface):
    """ The interface for a state directive """
    name = TextLine(title=u'name', required=True)
    title = TextLine(title=u'title', required=False)

class IWorkflowDirective(Interface):
    name = TextLine(title=u'name', required=True)
    initial_state = TextLine(title=u'initial_state', required=True)
    state_attr = TextLine(title=u'state_attr', required=False)
    class_ = GlobalObject(title=u'class', required=False)

class WorkflowDirective(zope.configuration.config.GroupingContextDecorator):
    implements(zope.configuration.config.IConfigurationContext,
               IWorkflowDirective)
    def __init__(self, context, name, initial_state, state_attr=None,
                 class_=None):
        self.context = context
        self.name = name
        self.initial_state = initial_state
        if state_attr is None:
            state_attr = name
        self.state_attr = state_attr
        if class_ is None:
            class_ = Workflow
        self.class_ = class_
        self.transitions = [] # mutated by subdirectives
        self.states = [] # mutated by subdirectives

    def after(self):
        workflow = Workflow(self.state_attr,
                               initial_state=self.initial_state)
        for state in self.states:
            workflow.add_state_info(state.name, **state.extras)

        for transition in self.transitions:
            workflow.add_transition(transition.name,
                                    transition.from_state,
                                    transition.to_state,
                                    transition.callback,
                                    **transition.extras)

        self.action(
            discriminator = (IWorkflow, self.name),
            callable = handler,
            args = ('registerUtility', workflow, IWorkflow, self.name,
                    self.info)
            )

class TransitionDirective(zope.configuration.config.GroupingContextDecorator):
    """ Handle ``transition`` ZCML directives
    """
    implements(zope.configuration.config.IConfigurationContext,
               ITransitionDirective)

    def __init__(self, context, name, callback, from_state, to_state,
                 permission=None):
        self.context = context
        self.name = name
        self.callback = callback
        if not from_state:
            from_state = None
        self.from_state = from_state
        self.to_state = to_state
        self.permission = permission
        self.extras = {} # mutated by subdirectives

    def after(self):
        self.context.transitions.append(self)

class StateDirective(zope.configuration.config.GroupingContextDecorator):
    implements(zope.configuration.config.IConfigurationContext,
               IStateDirective)
    def __init__(self, context, name, title=None):
        self.context = context
        self.name = name
        if title is None:
            title = name
        self.extras = {'title':title} # mutated by subdirectives

    def after(self):
        self.context.states.append(self)

def key_value_pair(context, name, value):
    ob = context.context
    if not hasattr(ob, 'extras'):
        ob.extras = {}
    ob.extras[str(name)] = value


        

    
