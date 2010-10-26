from django import template

register = template.Library()

@register.simple_tag
def status(application, component):
    """
    Usage: {% status application component %}

    Returns the status of the particular component.
    """
    return u"&mdash;"
