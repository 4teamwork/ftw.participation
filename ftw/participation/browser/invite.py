from Products.statusmessages.interfaces import IStatusMessage
from ftw.participation import _
from plone.z3cform.layout import wrap_form
from z3c.form.button import buttonAndHandler
from z3c.form.error import ErrorViewMessage
from z3c.form.field import Fields
from z3c.form.form import Form
from z3c.form.validator import SimpleFieldValidator
from z3c.form.validator import WidgetValidatorDiscriminators
from zope import schema
from zope.component import provideAdapter
from zope.interface import Interface
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
            IStatusMessage(self.request).addStatusMessage(
                'not yet implemented', type='info')
            return self.request.RESPONSE.redirect('./')

    @buttonAndHandler(_(u'button_cancel', default=u'Cancel'))
    def handle_cancel(self, action):
        """Go back to the site we came from
        """
        url = self.request.get('HTTP_REFERER')
        url = url or self.context.portal_url()
        self.request.RESPONSE.redirect(url)

InviteParticipantsView = wrap_form(InviteForm)
