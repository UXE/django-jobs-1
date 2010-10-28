from django import template

register = template.Library()

@register.simple_tag
def status(application, component):
    """
    Usage: {% status application component %}

    Returns the status of the particular component.
    """
    is_complete = []
    activity_date = None
    for component_part in component.componentpart_set.all():
        application_component_part = application.applicationcomponentpart_set.get(
            component_part=component_part
        )

        if application_component_part.content_object:
            is_complete.append(True)

            if not activity_date:
                activity_date = application_component_part.activity_date
            elif application_component_part.activity_date > activity_date:
                activity_date = application_component_part.activity_date

        else:
            is_complete.append(False)

    if all(is_complete):
        return "<strong>Completed</strong> on %s" % activity_date.strftime("%A, %B %e at %I:%M %p")
        #return "Completed: %s" % activity_date.strftime("%m/%d/%Y %I:%M")
    elif True in is_complete:
        return "<strong>Started</strong>, last modified on %s" % activity_date.strftime("%A, %B %e at %I:%M %p")
    else:
        return u"&mdash;"

