from django import template

from wwu_housing.jobs.utils import get_application_component_status

register = template.Library()

@register.simple_tag
def status(application, component):
    """
    Usage: {% status application component %}

    Returns the status of the particular component.
    """
    is_complete, activity_date = get_application_component_status(application, component)

    if (is_complete and all(is_complete) or True in is_complete and not component.is_required):
        return "<strong>Completed</strong> on %s" % activity_date.strftime("%A, %B %e at %I:%M %p")
    elif True in is_complete:
        return "<strong>Started</strong>, last modified on %s" % activity_date.strftime("%A, %B %e at %I:%M %p")
    else:
        return u"&mdash;"

