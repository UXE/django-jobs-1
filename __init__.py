"""
Jobs utility classes.
"""

class ComponentRegistry(dict):
    """
    Tracks relationships between job components and Django forms, models, and
    templates.
    """
    class NotRegistered(Exception):
        pass

    def register(self, key, value):
        """
        Stores a list of values for each key, creating a new list for a key if
        one doesn't exist already.
        """
        self.setdefault(key, set()).add(value)

    def get(self, key):
        value = super(ComponentRegistry, self).get(key)
        if value is None:
            raise self.NotRegistered("No values registered for key '%s'." % key)
        else:
            return value
