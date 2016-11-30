from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from ftw.participation import _
from ftw.participation.events import InvitationCreatedEvent
from ftw.participation.interfaces import IParticipationQuotaHelper
from ftw.participation.interfaces import IParticipationQuotaSupport
from ftw.participation.interfaces import IParticipationRegistry
from ftw.participation.invitation import Invitation
from plone.formwidget.autocomplete.widget import AutocompleteMultiFieldWidget
from plone.registry.interfaces import IRegistry
from plone.z3cform.layout import wrap_form
from Products.CMFCore.interfaces import IPropertiesTool
from Products.CMFCore.utils import getToolByName
from Products.statusmessages.interfaces import IStatusMessage
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.browser.radio import RadioFieldWidget
from z3c.form.button import buttonAndHandler
from z3c.form.field import Fields
from z3c.form.form import Form
from z3c.form.util import getSpecification
from z3c.form.validator import InvariantsValidator
from z3c.form.validator import SimpleFieldValidator
from z3c.form.validator import WidgetsValidatorDiscriminators
from z3c.form.validator import WidgetValidatorDiscriminators
from zExceptions import NotFound
from zope import schema
from zope.component import provideAdapter, getUtility
from zope.event import notify
from zope.i18n import translate
from zope.interface import Interface
from zope.interface import Invalid
import os.path
import re


class IInviteSchema(Interface):
    """Schema interface for invite form
    """

    users = schema.List(
        title=_(u'label_users', default=u'Users'),
        description=_(u'help_users',
                      default=u'Select users to invite.'),
        value_type=schema.Choice(
            vocabulary=u'ftw.participation.users'),
        required=False)

    addresses = schema.Text(
        title=_(u'label_addresses', default=u'E-Mail Addresses'),
        description=_(u'help_addresses',
                      default=u'Enter one e-mail address per line'),
        required=False)

    roles = schema.List(
        title=_(u'label_roles', default=u'Roles'),
        value_type=schema.Choice(
            vocabulary=u'ftw.participation.roles'),
        required=False)

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
        if value:
            addresses = value.strip().split('\n')
            self._validate_addresses(addresses)

    def _validate_addresses(self, addresses):
        """E-Mail address validation
        """

        for addr in addresses:
            addr = addr.strip()
            if not self.email_expression.match(addr):
                msg = _(u'error_invalid_addresses',
                        default=u'At least one of the defined addresses '
                        'are not valid.')
                raise Invalid(msg)


WidgetValidatorDiscriminators(AddressesValidator,
                              field=IInviteSchema['addresses'])
provideAdapter(AddressesValidator)


class NumberOfAdressesAndUsersValidator(InvariantsValidator):

    def validate(self, data):
        errors = ()
        invitations_nr = (data.get('users') and len(data.get('users')) or 0) +\
            (data.get('addresses') and len(data.get('addresses')) or 0)

        if invitations_nr == 0:
            # at least one invitation required
            registry = getUtility(IRegistry)
            config = registry.forInterface(IParticipationRegistry)
            if config.allow_invite_email and config.allow_invite_users:
                errors += (Invalid(_(u'Select at least one user or enter at '
                                     'least one e-mail address')),)
            elif config.allow_invite_email:
                errors += (Invalid(_(u'Enter at least one e-mail address.')),)
            elif config.allow_invite_users:
                errors += (Invalid(_(u'Select at least one user.')),)

        if IParticipationQuotaSupport.providedBy(self.context):
            # check maximum participants when quota enabled
            quota_support = IParticipationQuotaHelper(self.context)
            allowed = quota_support.allowed_number_of_invitations()
            if invitations_nr > allowed:
                if allowed <= 0:
                    msg = _(u'error_participation_quota_reached',
                            default=u'The participation quota is reached, '
                            'you cannot add any further participants.')
                else:
                    msg = _('error_too_many_participants',
                            default=u'You cannot invite so many participants '
                            'any more. Can only add ${num} more participants.',
                            mapping={'num': allowed})
                raise Invalid(msg)

        return errors

WidgetsValidatorDiscriminators(NumberOfAdressesAndUsersValidator,
                               schema=getSpecification(IInviteSchema,
                                                       force=True))
provideAdapter(NumberOfAdressesAndUsersValidator)


class RolesValidator(SimpleFieldValidator):
    """Validator for validating the e-mail addresses field
    """

    def validate(self, roles):
        registry = getUtility(IRegistry)
        config = registry.forInterface(IParticipationRegistry)

        if not config.allow_multiple_roles and not roles:
            msg = _(u'error_no_roles', default=u'Please select a role')
            raise Invalid(msg)

WidgetValidatorDiscriminators(RolesValidator,
                               field=IInviteSchema['roles'])
provideAdapter(RolesValidator)


class InviteForm(Form):
    label = _(u'label_invite_participants', default=u'Invite Participants')

    description = _(u'text_invite_new',
                    default=u'Use this form to invide new user')

    ignoreContext = True
    fields = Fields(IInviteSchema)
    fields['users'].widgetFactory = AutocompleteMultiFieldWidget

    def update(self):
        registry = getUtility(IRegistry)
        config = registry.forInterface(IParticipationRegistry)

        if not (config.allow_invite_email or config.allow_invite_users):
            raise NotFound

        if config.allow_multiple_roles:
            self.fields['roles'].widgetFactory = CheckBoxFieldWidget
        else:
            self.fields['roles'].widgetFactory = RadioFieldWidget

        super(InviteForm, self).update()

    def updateWidgets(self):
        super(InviteForm, self).updateWidgets()
        registry = getUtility(IRegistry)
        config = registry.forInterface(IParticipationRegistry)

        if not config.allow_invite_email:
            # disable address field
            del self.widgets['addresses']
            self.widgets['users'].required = True

        if not config.allow_invite_users:
            # disable users field
            del self.widgets['users']
            self.widgets['addresses'].required = True

        if not config.allow_multiple_roles:
            self.widgets['roles'].required = True

    def updateActions(self):
        super(InviteForm, self).updateActions()
        self.actions['button_invite'].addClass("context")

    @buttonAndHandler(_(u'button_invite', default=u'Invite'))
    def handle_invite(self, action):
        """Invite the users: create Invitations and send email
        """
        registry = getUtility(IRegistry)
        config = registry.forInterface(IParticipationRegistry)

        data, errors = self.extractData()
        if len(errors) == 0:
            # get inviter
            mtool = getToolByName(self.context, 'portal_membership')
            inviter = mtool.getAuthenticatedMember()

            # get all addresses
            addresses = []
            if config.allow_invite_email and \
                    data.get('addresses') and len(data.get('addresses')):
                for addr in data.get('addresses').split('\n'):
                    addresses.append(addr.strip())

            if config.allow_invite_users and data.get('users'):
                for user in data['users']:
                    member = mtool.getMemberById(user)
                    addresses.append(member.getProperty('email'))

            # get roles
            roles = data.get('roles', [])

            # handle every email seperate
            emails = []  # used for info msg
            for email in addresses:
                email = email.strip()
                if not email:
                    continue
                inv = Invitation(self.context, email, inviter.getId(), roles)
                self.send_invitation(inv, email, inviter, data.get('comment'))
                notify(InvitationCreatedEvent(self.context, inv,
                                              data.get('comment')))
                emails.append(email)

            # notify user
            emails.sort()
            msg = _(u'info_invitations_sent',
                    default=u'The invitation mails were sent to ${emails}.',
                    mapping={'emails': ', '.join(emails), })
            IStatusMessage(self.request).addStatusMessage(msg, type='info')
            return self.redirect()

    @buttonAndHandler(_(u'button_cancel', default=u'Cancel'))
    def handle_cancel(self, action):
        return self.redirect()

    def redirect(self):
        """Redirect back
        """

        url = self.context.absolute_url() + '/@@participants'
        return self.request.RESPONSE.redirect(url)

    def send_invitation(self, invitation, email, inviter, comment):
        """Send a invitation email to a user
        """

        properties = getUtility(IPropertiesTool)
        # prepare from address for header
        header_from = Header(properties.email_from_name,
                             'utf-8')
        header_from.append(u'<%s>' % properties.email_from_address.
                           decode('utf-8'),
                           'utf-8')
        # get subject
        header_subject = Header(unicode(self.get_subject()), 'utf-8')

        # prepare comment
        pttool = getToolByName(self.context, 'portal_transforms')
        html_comment = comment and pttool('text_to_html', comment) or ''

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
        msg['From'] = str(header_from)
        msg['To'] = email

        # render and embedd html / text
        text_body = text_view(**options).encode('utf-8')
        msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
        html_body = html_view(**options).encode('utf-8')
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        # send the mail
        mh = getToolByName(self.context, 'MailHost')
        mh.send(msg)

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
