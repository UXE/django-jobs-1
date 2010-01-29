import random


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

        ``lambda r, a, c: len(c) > 15``

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
