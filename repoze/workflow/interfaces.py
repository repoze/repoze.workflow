from zope.interface import Interface
from zope.interface import Attribute

class IWorkflowFactory(Interface):
    def __call__(self, context, machine):
        """ Return an object which implements IWorkflow """

class IWorkflow(Interface):
    def add_state(name, callback=None, **kw):
        """ Add a new state.  ``callback`` is a callback that will be
        called when a piece of content enters this state."""

    def add_transition(name, from_state, to_state, callback=None, **kw):
        """ Add a new transition.  ``callback`` is the callback that
        will be called when this transition is made (before it enters
        the next state)."""

    def check():
        """ Check the consistency of the workflow state machine. Raise
        an error if it's inconsistent."""

    def state_of(content):
        """ Return the current state of the content object ``content``
        or None if the content object has not particpated yet in this
        workflow.  """

    def has_state(content):
        """ Return true if the content has any state, false if not. """

    def state_info(content, request, context=None, from_state=None):
        """ Return a sequence of state info dictionaries """

    def initialize(content):
        """ Initialize the content object to the initial state of this
        workflow. Return a tuple of (state, msg) """

    def reset(content):
        """ Reset the object by calling the callback of it's current
        state and setting its state attr.  If ``content`` has no
        current state, it will be initialized into the initial state
        for this workflow (see ``initialize``). Return a tuple of
        (state, msg)"""

    def transition(content, request, transition_name, context=None, guards=()):
        """ Execute a transition using a transition name.  
        """
    def transition_to_state(content, request, to_state, context=None,
                            guards=(), skip_same=True):
        """ Execute a transition to another state using a state name
        (``to_state``).  If ``skip_same`` is True, and the
        ``to_state`` is the same as the content state, do nothing."""

    def get_transitions(content, request, context=None, from_state=None):
        """ Return a sequence of transition dictionaries """

class IWorkflowList(Interface):
    """ Marker interface used internally by get_workflow and the ZCML
    machinery.  An item registered as an IWorkflowList utility in
    the component registry is a dictionary that contains lists of
    workflow info dictionaries keyed by content type. """
    
    
class IDefaultWorkflow(Interface):
    """ Marker interface used internally for workflows that aren't
    associated with a particular content type"""
    
class IStateMachine(Interface):
    # NB: this is a backwards compatibility interface only!  See the
    # comment at the top of statemachine.py for more info.
    def add(state, transition_id, newstate, transition_fn, **kw):
        """Add a transition to the FSM."""

    def execute(content, transition_id):
        """Perform a transition and execute an action."""

    def state_of(content):
        """ Return the current state of the given object """

    def transitions(content, from_state=None):
        """ Return the available transition ids for the given object
        (from_state defaults to the object's current state)"""

    def transition_info(content, from_state=None):
        """ Return sequence of dictionaries representing the
        transition information for content (from_state defaults to the
        object's current state).  Each dictionary has the keys
        ``transition_id``, ``from_state``, ``to_state`` as well as any
        keywords passed in to the ``add`` method for this transition."""
    
    def before_transition(state, newstate, transition_id, content, **kw):
        """
        Hook method to be overridden by subclasses (or injected
        directly onto an instance) to allow for before transition
        actions (such as firing an event).

        Raise an exception here to abort the transition.
        """

    def after_transition(state, newstate, transition_id, content, **kw):
        """
        Hook method to be overridden by subclasses (or injected
        directly onto an instance) to allow for after transition
        actions (such as firing an event).
        """
        
class ICallbackInfo(Interface):
    """ Interface used internally to represent 'callback info' objects
    (the 2nd argument passed to callbacks) """

    transition = Attribute('A dictionary representing the transition underway')

    workflow = Attribute('The workflow object that invoked the callback')

    
