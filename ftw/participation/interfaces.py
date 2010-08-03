from zope.interface import Interface


class IParticipationBrowserLayer(Interface):
    """Browser layer interface for ftw.participation
    """


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
