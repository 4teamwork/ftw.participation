from Products.Archetypes.atapi import IntegerField, IntegerWidget
from Products.CMFCore.permissions import ManagePortal
from ftw.participation.interfaces import IParticipationQuotaSupport
from ftw.participation.interfaces import IParticipationQuotaHelper
from ftw.participation.interfaces import IInvitationStorage
from ftw.participation import _
from zope.interface import implements
from zope.component import adapts
from archetypes.schemaextender.field import ExtensionField
from archetypes.schemaextender.interfaces import ISchemaExtender


class ParticipationQuotaIntField(ExtensionField, IntegerField):
    """Integer field for setting the participation quota limit.
    """


class ParticipationQuotaExtender(object):
    """Extends the context with participation_quota_limit field using
    archetypes.schemaextender.

    """
    implements(ISchemaExtender)
    adapts(IParticipationQuotaSupport)

    fields = [
        ParticipationQuotaIntField(
            name='participation_limit_quota',
            schemata='quota',
            required=False,
            default=5,
            write_permission=ManagePortal,
            searchable=False,
            widget=IntegerWidget(
                label=_(u'label_participation_quota_limit',
                        default=u'Participation quota limit'),
                description=_(u'help_participation_quota_limit',
                              default=u''),
                size=20)),
        ]

    def __init__(self, context):
        self.context = context

    def getFields(self):
        return self.fields


class ParticipationQuotaHelper(object):
    """Support methdos for participation quota
    """
    implements(IParticipationQuotaHelper)
    adapts(IParticipationQuotaSupport)

    def __init__(self, context):
        self.context = context

    def get_quota_limit(self):
        """Returns the quota limit for this context.
        """
        field = self.context.Schema().getField('participation_limit_quota')
        return field.get(self.context)

    def allowed_number_of_invitations(self):
        """Returns how many users can be invited on the context at the moment.
        Pending invitations are counted.

        """
        allowed = int(self.get_quota_limit())
        # subtract amount of local roles
        allowed -= len(self.context.get_local_roles())
        # subtract the amount of pending invitations
        storage = IInvitationStorage(self.context)
        allowed -= len(storage.get_invitations_for_context(self.context))
        return allowed

    def is_quota_exceeded(self):
        """Returns True if the participation quota is reached.
        """
        return self.allowed_number_of_invitations() > 0
