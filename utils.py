from sqlalchemy import or_

import random

from wwu_housing.data import Person
from wwu_housing.library.validator import validate_id

from models import ApplicationComponentPart

def get_application_component_status(application, component):
    is_complete = []
    activity_date = None
    for component_part in component.componentpart_set.all():
        try:
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
        except ApplicationComponentPart.DoesNotExist:
            is_complete.append(False)

    return (is_complete, activity_date)


def assign_reviewers(reviewers, applicants, rules=None,
                     get_reviewer_key=None, count_max=20):
    """
    Assign applicants to each reviewer so that all the ``rules`` pass.

    Returns a dictionary indexed by ``get_reviewer_key(reviewer)`` containing
    applicants assigned to that reviewer.

    ``reviewers`` and ``applicants`` should both be iterables of arbitrary
    reviewer and applicant objects.

    ``rules`` = an iterable of functions that take a reviewer, applicant, and
    the reviewer's currently assigned applicants (in that order) and return
    false if the applicant can't be assigned to the reviewer, otherwise return
    true. For example, to make sure no reviewer has more than fifteen applicants
    assigned to them, add this function to your rules:

        ``lambda r, a, c: len(c) < 15``

    ``get_reviewer_key`` = A function that takes a reviewer and returns an
    immutable key to index the returned dictionary by. For example if a reviewer
    object is a list of ``[name, hall_1, hall_2, ..., hall_n]``, then
    ``get_reviewer_key`` could be

        ``lambda r: r[0]``

    so that it returned a string of the reviewer's name.

    ``count_max`` = The maximum number of pass throughs to attempt assigning an
    applicant to a reviewer before moving on.
    """
    rules = rules or []
    if not get_reviewer_key:
        raise TypeError("""
Must pass a function to the keyword argument "get_reviewer_key" that returns an
immutable data structure (such as a string) to index reviewers by in the
resulting dictionary. You passed: %s
""" % str(get_reviewer_key))
    assignments = {}

    for applicant in applicants:
        count = 0
        while count < count_max:
            reviewer = random.choice(reviewers)

            # Get current applicants for this reviewer.
            key = get_reviewer_key(reviewer)
            if key not in assignments:
                assignments[key] = []
            current_applicants = assignments[key]

            rule_results = [rule(reviewer, applicant, current_applicants)
                            for rule in rules]
            if all(rule_results):
                assignments[key].append(applicant)
                break
            else:
                count += 1
                if count == count_max:
                    if "_UNASSIGNED" not in assignments:
                        assignments["_UNASSIGNED"] = [applicant]
                    else:
                        assignments["_UNASSIGNED"].append(applicant)

    return assignments

def _get_persons_for_job(job):
    # load person objects for all job applicants
    usernames = []
    student_ids = []
    for application in job.application_set.all():
        if not application.applicationcomponentpart_set.all():
            continue
        if validate_id(application.applicant.user.username):
            student_ids.append(application.applicant.user.username)
        else:
            usernames.append(application.applicant.user.username)
    if student_ids or usernames:
        student_ids_or = [Person.student_id == student_id for student_id in student_ids]
        usernames_or = [Person.pidm == Person.pidm_from_username(username) for username in usernames]
        ids_or = student_ids_or + usernames_or
        persons = Person.query.filter(or_(*ids_or))
        object_dict = {}
        for person in persons:
            if person.username:
                object_dict[person.username] = person
            else:
                object_dict[person.student_id] = person

        return object_dict
    else:
        return None

