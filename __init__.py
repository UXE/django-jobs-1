"""
Jobs utility classes.
"""

class ComponentRegistry(dict):
    """
    Defines relationships between Django content types and Django form classes.

    These relationships are used to determine which form to use for a given
    ComponentPart based on its content object's content type.
    """
    class NotRegistered(Exception):
        """
        Alerts users when nothing is registered for a given app_label.
        """
        pass

    class AlreadyRegistered(Exception):
        """
        Alerts users when a value has already been registered for a given
        app_label.
        """
        pass

    def register(self, app_label, model, value):
        """
        Stores a dictionary of values for each app_label, creating a new
        dictionary for each app_label if one doesn't exist already.
        """
        if app_label not in self:
            self[app_label] = {}

        if model in self[app_label]:
            raise self.AlreadyRegistered(
                "Model '%s' is already registered for app_label '%s'." % (model, app_label)
            )
        else:
            self[app_label][model] = value

    def get(self, app_label):
        """
        Tries to find a value for the given app_label. Raises an exception if nothing
        has been registered for the given app_label.
        """
        value = super(ComponentRegistry, self).get(app_label)
        if value is None:
            raise self.NotRegistered("No values registered for app_label '%s'." % app_label)
        else:
            return value

registry = ComponentRegistry()
