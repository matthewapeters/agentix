"""
Docstring for agentix.context.context
"""

class Context:
    """
    A class representing the context for Agentix operations.
    """

    def __init__(self, user_id: str, session_id: str):
        """
        Initialize the Context with user and session identifiers.

        :param user_id: The identifier for the user.
        :param session_id: The identifier for the session.
        """
        self.user_id = user_id
        self.session_id = session_id
        self.history = []

    def get_user_id(self) -> str:
        """
        Get the user identifier.

        :return: The user identifier.
        """
        return self.user_id

    def get_session_id(self) -> str:
        """
        Get the session identifier.

        :return: The session identifier.
        """
        return self.session_id