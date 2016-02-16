from ftw.builder.testing import BUILDER_LAYER
from ftw.builder.testing import functional_session_factory
from ftw.builder.testing import set_builder_session_factory
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import setRoles, TEST_USER_ID, TEST_USER_NAME, login
from Testing.ZopeTestCase.utils import setupCoreSessions
from zope.configuration import xmlconfig
import ftw.participation.tests.builders
import transaction


TEST_USER_ID_2 = '_test_user_2_'
TEST_USER_PW_2 = 'secret'


class FtwParticipationLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE, BUILDER_LAYER)

    def setUpZope(self, app, configurationContext):
        xmlconfig.string(
            '<configure xmlns="http://namespaces.zope.org/zope">'
            '  <include package="z3c.autoinclude" file="meta.zcml" />'
            '  <includePlugins package="plone" />'
            '  <includePluginsOverrides package="plone" />'
            '</configure>',
            context=configurationContext)

        # Invoke SESSION
        setupCoreSessions(app)
        transaction.commit()

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'ftw.participation:default')
        applyProfile(portal, 'plone.formwidget.autocomplete:default')
        applyProfile(portal, 'ftw.tabbedview:default')

        setRoles(portal, TEST_USER_ID, ['Manager'])
        login(portal, TEST_USER_NAME)

        portal.portal_registration.addMember(TEST_USER_ID_2, TEST_USER_PW_2)


FTW_PARTICIPATION_FIXTURE = FtwParticipationLayer()
FTW_PARTICIPATION_INTEGRATION_TESTING = IntegrationTesting(
    bases=(FTW_PARTICIPATION_FIXTURE,), name="FtwParticipation:Integration")

FTW_PARTICIPATION_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(FTW_PARTICIPATION_FIXTURE,
           set_builder_session_factory(functional_session_factory)),
    name="FtwParticipation:Functional")
