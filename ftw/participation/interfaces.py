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
