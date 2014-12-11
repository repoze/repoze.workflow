import warnings

from zope.component import getSiteManager
from zope.configuration.config import GroupingContextDecorator
from zope.configuration.config import IConfigurationContext
from zope.configuration.exceptions import ConfigurationError
from zope.configuration.fields import GlobalObject
from zope.configuration.fields import Tokens
from zope.interface import Interface
from zope.interface import implementer
from zope.interface import providedBy
from zope.interface.interfaces import IInterface
from zope.schema import TextLine

from repoze.workflow.interfaces import IWorkflow
from repoze.workflow.interfaces import IWorkflowList
from repoze.workflow.interfaces import IDefaultWorkflow
from repoze.workflow.workflow import Workflow
from repoze.workflow.workflow import WorkflowError
from repoze.workflow._compat import text_ as _u

def handler(methodName, *args, **kwargs): # pragma: no cover
    method = getattr(getSiteManager(), methodName)
    method(*args, **kwargs)

class IGuardDirective(Interface):
    """ A directive for a guard on a transition. """
    function = GlobalObject(title=_u('enter guard function'), required=True)

class IKeyValueDirective(Interface):
    """ The interface for a key/value pair subdirective """
    name = TextLine(title=_u('key'), required=True)
    value = TextLine(title=_u('value'), required=True)

class IAliasDirective(Interface):
    """ The interface for an alias subdirective """
    name = TextLine(title=_u('name'), required=True)

class ITransitionDirective(Interface):
    """ The interface for a transition directive """
    name = TextLine(title=_u('name'), required=True)
    from_state = TextLine(title=_u('from_state'), required=True)
    to_state = TextLine(title=_u('to_state'), required=True)
    permission = TextLine(title=_u('permission'), required=False)
    title = TextLine(title=_u('title'), required=False)
    callback = GlobalObject(title=_u('callback'), required=False)

class IStateDirective(Interface):
    """ The interface for a state directive """
    name = TextLine(title=_u('name'), required=True)
    title = TextLine(title=_u('title'), required=False)
    callback = GlobalObject(title=_u('enter state callback'), required=False)

class IWorkflowDirective(Interface):
    type = TextLine(title=_u('type'), required=True)
    name = TextLine(title=_u('title'), required=True)
    initial_state = TextLine(title=_u('initial_state'), required=True)
    state_attr = TextLine(title=_u('state_attr'), required=True)
    content_types = Tokens(title=_u('content_types'), required=False,
                           value_type=GlobalObject())
    elector = GlobalObject(title=_u('elector'), required=False)
    permission_checker = GlobalObject(title=_u('checker'), required=False)
    description = TextLine(title=_u('description'), required=False)

@implementer(IConfigurationContext, IWorkflowDirective)
class WorkflowDirective(GroupingContextDecorator):
    def __init__(self, context, type, name, state_attr, initial_state,
                 content_types=(), elector=None, permission_checker=None,
                 description=''):
        self.context = context
        self.type = type
        self.name = name
        if state_attr is None:
            state_attr = name
        self.state_attr = state_attr
        self.initial_state = initial_state
        self.content_types = content_types
        self.elector = elector
        self.permission_checker = permission_checker
        self.description = description
        self.transitions = [] # mutated by subdirectives
        self.states = [] # mutated by subdirectives

    def after(self):
        def register(content_type):
            workflow = Workflow(self.state_attr, self.initial_state,
                                self.permission_checker, self.name,
                                self.description)
            for state in self.states:
                try:
                    workflow.add_state(state.name,
                                       state.callback,
                                       aliases=state.aliases,
                                       title=state.title,
                                       **state.extras)
                except WorkflowError as why:
                    raise ConfigurationError(str(why))

            for transition in self.transitions:
                try:
                    workflow.add_transition(transition.name,
                                            transition.from_state,
                                            transition.to_state,
                                            transition.callback,
                                            transition.permission,
                                            transition.title,
                                            guards=transition.guards,
                                            **transition.extras)
                except WorkflowError as why:
                    raise ConfigurationError(str(why))

            try:
                workflow.check()
            except WorkflowError as why:
                raise ConfigurationError(str(why))

            register_workflow(workflow, self.type, content_type,
                              self.elector, self.info)

        if self.elector is not None:
            elector_id = id(self.elector)
        else:
            elector_id = None

        if len(self.content_types) == 0:
            warnings.warn('No content_types specified:  workflow inactive.')
        for content_type in self.content_types:
            self.action(
                discriminator = (IWorkflow, content_type, elector_id,
                                 self.type, self.state_attr),
                callable = register,
                args = (content_type,),
                )

@implementer(IConfigurationContext, ITransitionDirective)
class TransitionDirective(GroupingContextDecorator):
    """ Handle ``transition`` ZCML directives
    """

    def __init__(self, context, name, from_state, to_state,
                 callback=None, permission=None, title=None):
        self.context = context
        self.name = name
        if not from_state:
            from_state = None
        self.from_state = from_state
        self.to_state = to_state
        self.callback = callback
        self.permission = permission
        self.title = title
        self.guards = []
        self.extras = {} # mutated by subdirectives

    def after(self):
        self.context.transitions.append(self)

@implementer(IConfigurationContext, IStateDirective)
class StateDirective(GroupingContextDecorator):
    def __init__(self, context, name, callback=None, title=None):
        self.context = context
        self.name = name
        self.callback = callback
        self.title = title
        self.extras = {} # mutated by subdirectives
        self.aliases = []

    def after(self):
        self.context.states.append(self)

def guard_function(context, function):
    context.guards.append(function)

def key_value_pair(context, name, value):
    ob = context.context
    if not hasattr(ob, 'extras'):
        ob.extras = {}
    ob.extras[str(name)] = value

def alias(context, name):
    ob = context.context
    if not hasattr(ob, 'aliases'):
        ob.aliases = []
    ob.aliases.append(name)

def register_workflow(workflow, type, content_type, elector, info=None):
    if content_type is None:
        content_type = IDefaultWorkflow

    if not IInterface.providedBy(content_type):
        content_type = providedBy(content_type)

    sm = getSiteManager()

    wf_list = sm.adapters.lookup((content_type,), IWorkflowList, name=type,
                                 default=None)

    if wf_list is None:
        wf_list = []
        sm.registerAdapter(wf_list, (content_type,), IWorkflowList, type, info)

    wf_list.append({'workflow':workflow, 'elector':elector})

