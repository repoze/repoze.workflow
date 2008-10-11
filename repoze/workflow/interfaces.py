from zope.interface import Interface

class IStateMachine(Interface):
    def add(state, transition_id, newstate, transition_fn):
        """
        """

    def execute(context, transition_id):
        """
        """

    def state_of(context):
        """
        """

    def transitions(context, from_state=None):
        """
        """

    def before_transition(state, newstate, transition_id, context):
        """
        """

    def after_transition(state, newstate, transition_id, context):
        """
        """
        
