"""
Jobs utility classes.
"""

class ComponentRegistry(dict):
    """
    Tracks relationships between job components and Django forms, models, and
    templates.
    """
    class NotRegistered(Exception):
        """
        Alerts users when a key has nothing registered in this registry.
        """
        pass

    class AlreadyRegistered(Exception):
        """
        Alerts users when a value has already been registered for a given
        component.
        """
        pass

    def register(self, component, key, value):
        """
        Stores a dictionary of values for each component, creating a new
        dictionary for each component if one doesn't exist already.
        """
        if component not in self:
            self[component] = {}

        if key in self[component]:
            raise self.AlreadyRegistered(
                "Key '%s' is already registered for component '%s'." % (key, component)
            )
        else:
            self[component][key] = value

    def get(self, component):
        """
        Tries to find a value for the given component. Raises an exception if nothing
        has been registered for the given component.
        """
        value = super(ComponentRegistry, self).get(component)
        if value is None:
            raise self.NotRegistered("No values registered for component '%s'." % component)
        else:
            return value

registry = ComponentRegistry()
