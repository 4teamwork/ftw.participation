from ftw.participation import _
from ftw.participation.browser.accept import AcceptInvitation
from ftw.participation.events import InvitationRejectedEvent
from Products.CMFCore.utils import getToolByName
from Products.statusmessages.interfaces import IStatusMessage
from zope.event import notify
from zope.i18n import translate
import os.path


class RejectInvitation(AcceptInvitation):
    """Reject a invitation. Like accept but with different messages
    and without partipating.

    """

    def __call__(self, iid=None):
        """
        """
        if not iid:
            iid = self.request.get('iid')

        self.load(iid)
        notify(InvitationRejectedEvent(self.target, self.invitation))

        self.send_email()

        # add status message
        msg = _(u'info_invitation_rejected',
                default=u'You have rejected the invitation.')
        IStatusMessage(self.request).addStatusMessage(msg, type='info')

        # destroy the invitation
        self.storage.remove_invitation(self.invitation)
        del self.invitation

        # redirect back
        url = self.request.get('HTTP_REFERER',
                               os.path.join(self.context.portal_url(),
                                            '@@invitations'))
        return self.request.RESPONSE.redirect(url)

    def get_mail_body_html_view(self):
        return self.context.unrestrictedTraverse(
            '@@invitation_rejected_mail_html')

    def get_mail_body_text_view(self):
        return self.context.unrestrictedTraverse(
            '@@invitation_rejected_mail_text')

    def get_subject(self):
        """Returns the translated subject of the email.
        """
        member = getToolByName(self.context,
                               'portal_membership').getAuthenticatedMember()
        fullname = member.getProperty(
            'fullname', member.getId()).decode('utf8')
        context_title = self.context.pretty_title_or_id().decode('utf-8')
        # -- i18ndude hint --
        if 0:
            _(u'mail_invitation_rejected_subject',
              default=u'The Invitation to participate in ${title} '
              u'was rejected by ${user}',
              mapping=dict(title=context_title,
                           user=fullname))
        # / -- i18ndude hint --
        # do not use translation messages - translate directly
        return translate(u'mail_invitation_rejected_subject',
                         domain='ftw.participation',
                         context=self.request,
                         default=u'The Invitation to participate in ${title} '
                         u'was rejected by ${user}',
                         mapping=dict(title=context_title,
                                      user=fullname))
