from Products.CMFCore.interfaces import IPropertiesTool
from Products.CMFCore.utils import getToolByName
from Products.statusmessages.interfaces import IStatusMessage
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from ftw.participation import _
from ftw.participation.invitation import Invitation
from plone.z3cform.layout import wrap_form
from z3c.form.button import buttonAndHandler
from z3c.form.error import ErrorViewMessage
from z3c.form.field import Fields
from z3c.form.form import Form
from z3c.form.validator import SimpleFieldValidator
from z3c.form.validator import WidgetValidatorDiscriminators
from zope import schema
from zope.component import provideAdapter, getUtility
from zope.i18n import translate
from zope.interface import Interface
import os.path
import re


class IInviteSchema(Interface):
    """Schema interface for invite form
    """

    addresses = schema.Text(
        title=_(u'label_addresses', default=u'E-Mail Addresses'),
        description=_(u'help_addresses',
                      default=u'Enter one e-mail address per line'),
        required=True,
        )

    comment = schema.Text(
        title=_(u'label_comment', default=u'Comment'),
        description=_(u'help_comment',
                      default=u'Enter a comment which will be contained '
                      'in the invitaiton E-Mail'),
        required=False,
        )


class AddressesValidator(SimpleFieldValidator):
    """Validator for validating the e-mail addresses field
    """

    MAIL_EXPRESSION = r"^(\w&.%#$&'\*+-/=?^_`{}|~]+!)*[\w&.%#$&'\*+-/=" +\
        "?^_`{}|~]+@(([0-9a-z]([0-9a-z-]*[0-9a-z])?" +\
        "\.)+[a-z]{2,6}|([0-9]{1,3}\.){3}[0-9]{1,3})$"

    def __init__(self, *args, **kwargs):
        super(AddressesValidator, self).__init__(*args, **kwargs)
        self.email_expression = re.compile(AddressesValidator.MAIL_EXPRESSION,
                                           re.IGNORECASE)

    def validate(self, value):
        """Validates the `value`, expects a list of carriage-return-separated
        email addresses.

        """
        super(AddressesValidator, self).validate(value)
        for addr in value.strip().split('\n'):
            addr = addr.strip()
            if not self.email_expression.match(addr):
                raise schema.interfaces.ConstraintNotSatisfied()


WidgetValidatorDiscriminators(AddressesValidator,
                              field=IInviteSchema['addresses'])
provideAdapter(AddressesValidator)
provideAdapter(ErrorViewMessage(
        _(u'error_invalid_addresses',
          default=u'At least one of the defined addresses are not valid.'),
        error=schema.interfaces.ConstraintNotSatisfied,
        field=IInviteSchema['addresses']), name='message')


class InviteForm(Form):
    fields = Fields(IInviteSchema)
    label = _(u'label_invite_participants', default=u'Invite Participants')
    ignoreContext = True

    def __init__(self, *a, **kw):
        super(InviteForm, self).__init__(*a, **kw)

    @buttonAndHandler(_(u'button_invite', default=u'Invite'))
    def handle_invite(self, action):
        """Invite the users: create Invitations and send email
        """
        data, errors = self.extractData()
        if len(errors) == 0:
            # get inviter
            mtool = getToolByName(self.context, 'portal_membership')
            inviter = mtool.getAuthenticatedMember()
            # handle every email seperate
            for email in data.get('addresses').strip().split('\n'):
                email = email.strip()
                if not email:
                    continue
                inv = Invitation(self.context, email, inviter.getId())
                self.send_invitation(inv, email, inviter, data.get('comment'))
            # notify user
            msg = _(u'info_invitations_sent',
                    default=u'The invitation mails were sent.')
            IStatusMessage(self.request).addStatusMessage(msg, type='info')
            return self.redirect()

    @buttonAndHandler(_(u'button_cancel', default=u'Cancel'))
    def handle_cancel(self, action):
        return self.redirect()

    def redirect(self):
        """Redirect back
        """
        return self.request.RESPONSE.redirect('./')

    def send_invitation(self, invitation, email, inviter, comment):
        """Send a invitation email to a user
        """
        properties = getUtility(IPropertiesTool)
        # prepare from address for header
        header_from = Header(properties.email_from_name.decode('utf-8'),
                             'iso-8859-1')
        header_from.append(u'<%s>' % properties.email_from_address.
                           decode('utf-8'),
                           'iso-8859-1')
        # get subject
        header_subject = Header(unicode(self.get_subject()), 'iso-8859-1')

        # prepare comment
        pttool = getToolByName(self.context, 'portal_transforms')
        html_comment = pttool('text_to_html', comment) or ''

        # prepare options
        options = {
            'invitation': invitation,
            'email': email,
            'inviter': inviter,
            'inviter_name': inviter.getProperty('fullname',
                                                False) or inviter.getId(),
            'text_comment': comment,
            'html_comment': html_comment,
            'link_url': self.get_url(invitation),
            'site_title': self.context.portal_url.getPortalObject().Title(),
            }

        # get the body views
        html_view = self.context.unrestrictedTraverse('@@invitation_mail_html')
        text_view = self.context.unrestrictedTraverse('@@invitation_mail_text')
        # make the mail
        msg = MIMEMultipart('alternative')
        msg['Subject'] = header_subject
        msg['From'] = header_from
        msg['To'] = email

        # render and embedd html / text
        text_body = text_view(**options).encode('utf-8')
        msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
        html_body = html_view(**options).encode('utf-8')
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        # send the mail
        mh = getToolByName(self.context, 'MailHost')
        mh.send(msg, mto=email)

    def get_subject(self):
        """Returns the translated subject of the email.
        """
        context_title = self.context.pretty_title_or_id().decode('utf-8')
        # -- i18ndude hint --
        if 0:
            _(u'mail_invitation_subject',
              default=u'Invitation for paticipating in ${title}',
              mapping=dict(title=context_title))
        # / -- i18ndude hint --
        # do not use translation messages - translate directly
        return translate(u'mail_invitation_subject',
                         domain='ftw.participation',
                         context=self.request,
                         default=u'Invitation for paticipating in ${title}',
                         mapping=dict(title=context_title))

    def get_url(self, invitation):
        """Returns the URL which is embedded in the invitation email. Usually
        the links points to the invitation view and uses the iid of the
        invitation as parameter, so that the invitation will be marked as
        pending in the session.

        """
        return os.path.join(self.context.portal_url(),
                            '@@invitations?iid=%s' % invitation.iid)

InviteParticipantsView = wrap_form(InviteForm)
