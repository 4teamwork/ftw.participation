from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from ftw.participation import _
from ftw.participation.events import InvitationAcceptedEvent
from ftw.participation.interfaces import IInvitationStorage
from ftw.participation.interfaces import IParticipationSetter
from Products.CMFCore.interfaces import IPropertiesTool
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from zExceptions import Redirect
from zope.component import getMultiAdapter, getUtility
from zope.event import notify
from zope.i18n import translate


class AcceptInvitation(BrowserView):
    """Accept a invitation. This either called directly from the browser (with
    a url like .../@@accept_invitations?iid=XXX) or through the invitations
    view (with unrestrictedTravers('@@accept_invitations')(iid) ).

    """

    def __call__(self, iid=None, redirect=True):
        if not iid:
            iid = self.request.get('iid')

        self.load(iid)

        self.set_participation()
        notify(InvitationAcceptedEvent(self.target, self.invitation))
        self.send_email()

        # add status message
        msg = _(u'info_invitation_accepted',
                default=u'You have accepted the invitation.')
        IStatusMessage(self.request).addStatusMessage(msg, type='info')

        # destroy the invitation
        self.storage.remove_invitation(self.invitation)
        del self.invitation

        # redirect context (where the user now has access)
        if redirect:
            return self.request.RESPONSE.redirect(self.target.absolute_url())

    def load(self, iid):
        """Loads the storage, the invitation and the target and does some
        more things.

        """
        self.storage = IInvitationStorage(self.context)
        self.invitation = self.storage.get_invitation_by_iid(iid)
        self.target = self.invitation.get_target()

        # sanity check
        mtool = getToolByName(self.context, 'portal_membership')
        self.member = mtool.getAuthenticatedMember()
        valid_emails = (self.member.getId(),
                        self.member.getProperty('email', object()))
        if not self.invitation or self.invitation.email not in valid_emails:
            msg = _(u'error_invitation_not_found',
                    default=u'Could not find the invitation.')
            IStatusMessage(self.request).addStatusMessage(msg, type='error')
            raise Redirect(self.context.portal_url())

    def set_participation(self):
        """Sets up participation up.
        """
        # participate the user (using the adapter)
        setter = getMultiAdapter((self.target, self.request,
                                  self.invitation, self.member),
                                 IParticipationSetter)
        setter()

    def send_email(self):
        """Sends the notification email to the invitor.
        """
        properties = getUtility(IPropertiesTool)
        mtool = getToolByName(self.context, 'portal_membership')
        # prepare from address for header
        from_str = Header(properties.email_from_name, 'utf-8')
        from_str.append(u'<%s>' % properties.email_from_address.decode('utf-8'))

        # To
        to_member = mtool.getMemberById(self.invitation.inviter)
        if not to_member.getProperty('email'):
            msg = _(u'error_inviter_email_missing',
                    default=u'Invitor could not be notified: he has '
                    'no email address defined.')
            IStatusMessage(self.request).addStatusMessage(msg, type='error')
            return
        to_str = to_member.getProperty('fullname', to_member.getId())
        if isinstance(to_str, unicode):
            to_str = to_str.encode('utf8')
        header_to = Header(to_str, 'utf-8')
        header_to.append(u'<%s>' % to_member.getProperty(
                'email').decode('utf-8'))
        # Subject
        subject = self.get_subject()
        if isinstance(subject, unicode):
            subject = subject.encode('utf8')
        header_subject = Header(subject, 'utf8')

        # Options for templated
        options = {
            'invitation': self.invitation,
            'inviter': to_member,
            'inviter_name': to_member.getProperty('fullname',
                                                  to_member.getId()),
            'invited': self.member,
            'invited_name': self.member.getProperty('fullname',
                                                    self.member.getId()),
            'invited_email': self.member.getProperty('email',
                                                     self.member.getId()),
            'target': self.target,
            }

        # make the mail
        msg = MIMEMultipart('alternative')
        msg['Subject'] = header_subject
        msg['From'] = str(from_str)
        msg['To'] = str(header_to)
        # get the body views
        html_view = self.get_mail_body_html_view()
        text_view = self.get_mail_body_text_view()

        # render and emmbed body
        text_body = text_view(**options).encode('utf-8')
        msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
        html_body = html_view(**options).encode('utf-8')
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        # send the email
        mh = getToolByName(self.context, 'MailHost')
        mh.send(msg)

    def get_mail_body_html_view(self):
        return self.context.unrestrictedTraverse(
            '@@invitation_accepted_mail_html')

    def get_mail_body_text_view(self):
        return self.context.unrestrictedTraverse(
            '@@invitation_accepted_mail_text')

    def get_subject(self):
        """Returns the translated subject of the email.
        """
        member = getToolByName(self.context,
                               'portal_membership').getAuthenticatedMember()
        fullname = member.getProperty('fullname',
                                      member.getId()).decode('utf-8')
        context_title = self.context.pretty_title_or_id().decode('utf-8')
        # -- i18ndude hint --
        if 0:
            _(u'mail_invitation_accepted_subject',
              default=u'The Invitation to participate in ${title} '
              u'was accepted by ${user}',
              mapping=dict(title=context_title,
                           user=fullname))
        # / -- i18ndude hint --
        # do not use translation messages - translate directly
        return translate(u'mail_invitation_accepted_subject',
                         domain='ftw.participation',
                         context=self.request,
                         default=u'The Invitation to participate in ${title} '
                         u'was accepted by ${user}',
                         mapping=dict(title=context_title,
                                      user=fullname))
