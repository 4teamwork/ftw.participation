from zope.interface import implements
from zope.schema.interfaces import IVocabularyFactory
from Acquisition import aq_inner
from plone.app.workflow.interfaces import ISharingPageRole
from Products.CMFCore.utils import getToolByName
from zope.component import getUtilitiesFor
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


class LocalRolesForDisplay(object):
    """Vocabulary of local roles"""

    implements(IVocabularyFactory)

    def __call__(self, context, role_filter=['Reader', 'Reviewer', ]):
        """Get a list of roles, similar like @@sharing"""
        context = aq_inner(context)
        portal_membership = getToolByName(context, 'portal_membership')

        roles = []
        for name, utility in getUtilitiesFor(ISharingPageRole):
            if name not in role_filter:
                permission = utility.required_permission
                if permission is None or portal_membership.checkPermission(
                    permission,
                    context):
                    roles.append(
                        SimpleTerm(name, name, utility.title))
        # Sort
        roles.sort(lambda x, y: cmp(x.title, y.title))
        return SimpleVocabulary(roles)

LocalRolesForDisplayFactory = LocalRolesForDisplay()
