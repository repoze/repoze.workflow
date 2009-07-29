from zope.component import getSiteManager
from zope.component import queryUtility
from zope.configuration.exceptions import ConfigurationError

import zope.configuration.config

from zope.configuration.fields import GlobalObject

from zope.interface import Interface
from zope.interface import implements

from zope.schema import TextLine

from repoze.bfg.workflow.interfaces import IWorkflow
from repoze.bfg.workflow.interfaces import IWorkflowLookup

from repoze.bfg.workflow.workflow import Workflow
from repoze.bfg.workflow.workflow import StateMachineError

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
    name = TextLine(title=u'name', required=False)
    initial_state = TextLine(title=u'initial_state', required=True)
    state_attr = TextLine(title=u'state_attr', required=False)
    content_type = GlobalObject(title=u'content_type', required=False)
    container_type = GlobalObject(title=u'container_type', required=False)

class WorkflowDirective(zope.configuration.config.GroupingContextDecorator):
    implements(zope.configuration.config.IConfigurationContext,
               IWorkflowDirective)
    def __init__(self, context, initial_state, name=None, state_attr=None,
                 content_type=None, container_type=None):
        self.context = context
        self.initial_state = initial_state
        self.name = name or ''
        if state_attr is None:
            state_attr = name
        self.state_attr = state_attr
        self.content_type = content_type
        self.container_type = container_type
        self.transitions = [] # mutated by subdirectives
        self.states = [] # mutated by subdirectives

    def after(self):
        def register():
            workflow = Workflow(self.state_attr,
                                initial_state=self.initial_state)
            for state in self.states:
                workflow.add_state_info(state.name, **state.extras)

            for transition in self.transitions:
                try:
                    workflow.add_transition(transition.name,
                                            transition.from_state,
                                            transition.to_state,
                                            transition.callback,
                                            **transition.extras)
                except StateMachineError, why:
                    raise ConfigurationError(str(why))

            sm = getSiteManager()

            workflows = queryUtility(IWorkflowLookup, name=self.name,
                                     default=None)
            if workflows is None:
                workflows = {}
                sm.registerUtility(workflows, IWorkflowLookup, name=self.name)

            wf_list = workflows.setdefault(self.content_type, [])
            wf_list.append({'workflow':workflow,
                            'container_type':self.container_type})
                              
        self.action(
            discriminator = (IWorkflow, self.content_type, self.container_type,
                             self.name),
            callable = register,
            args = (),
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

class WorkflowList(object):
    def __init__(self):
        self.workflows = []
        

    
