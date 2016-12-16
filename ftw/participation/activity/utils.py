from ftw.participation import _
from ftw.participation.browser.participants import get_friendly_role_names
from zope.i18n import translate


def translate_and_join_roles(roles, context, request):
    roles = get_friendly_role_names(roles, context, request)
    and_ = translate(_(' and '), context=request)
    return ', '.join(roles[:-2] + [and_.join(roles[-2:])])
