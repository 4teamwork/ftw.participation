from ftw.participation import _
from zope import schema
from zope.interface import Interface


class IParticipationBrowserLayer(Interface):
    """Browser layer interface for ftw.participation
    """


class IParticipationRegistry(Interface):
    """plone.app.registry configuration interface
    """

    allow_invite_users = schema.Bool(
        title=_(u'label_allow_invite_users',
                default=u'Allow to invite users'),
        description=_(u'help_allow_invite_users',
                      default=u'Allow to search users from PAS in invitation '
                      'form.'),
        default=True)

    allow_invite_email = schema.Bool(
        title=_(u'label_allow_invite_email',
                default=u'Allow to invite participants by email'),
        description=_(u'help_allow_invite_email',
                      default=u'Allow to invite participants by typing the '
                      'e-mail address in the invitation form. It is '
                      'recommended to enable registriation in plone security'),
        default=True)

    allow_multiple_roles = schema.Bool(
        title=_(u'label_multiple_roles',
                default=u'Allow to give multiple roles'),
        description=_(u'help_multiple_roles',
                      default=u'Allow to pass multiple roles to a invited '
                               'user.'),
        default=True)


class IInvitation(Interface):
    """Marker interface for invitations
    """


class IInvitationStorage(Interface):
    """Adapter interface for managing and storing invitations
    """


class IParticipationSupport(Interface):
    """Marker interface for objects where other users can be invitation
    """


class IInvitationMailer(Interface):
    """Adapter interface for the invitation mailer
    """


class IParticipationSetter(Interface):
    """Adapter interface for the adapter which sets the permission or does
    other things for participating a user.
    Discriminators: context, request, invitation, member

    """


class IParticipationQuotaSupport(Interface):
    """This marker interface enables a participation quota on the provided
    context. A protected field for defining the quota limit is added to
    the schema.

    """


class IParticipationQuotaHelper(Interface):
    """Helper adapter for the participation quota.
    """
