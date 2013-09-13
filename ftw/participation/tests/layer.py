from Products.PloneTestCase import ptc
from Testing.ZopeTestCase.utils import setupCoreSessions
from collective.testcaselayer import common
from collective.testcaselayer import ptc as tcl_ptc
from ftw.builder.testing import BUILDER_LAYER
from ftw.builder.testing import functional_session_factory
from ftw.builder.testing import set_builder_session_factory
from ftw.testing import FunctionalSplinterTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.app.testing import setRoles, TEST_USER_ID, TEST_USER_NAME, login
from zope.configuration import xmlconfig
import transaction


class Layer(tcl_ptc.BasePTCLayer):
    """Install ftw.participation"""

    def afterSetUp(self):
        ptc.installPackage('ftw.participation')
        self.addProfile('ftw.participation:default')

layer = Layer([common.common_layer])


TEST_USER_ID_2 = '_test_user_2_'
TEST_USER_PW_2 = 'secret'


class FtwParticipationLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE, BUILDER_LAYER)

    def setUpZope(self, app, configurationContext):
        import ftw.participation
        xmlconfig.file('configure.zcml', ftw.participation,
                       context=configurationContext)

        # Invoke SESSION
        setupCoreSessions(app)
        transaction.commit()

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'ftw.participation:default')

        setRoles(portal, TEST_USER_ID, ['Manager'])
        login(portal, TEST_USER_NAME)

        portal.portal_registration.addMember(TEST_USER_ID_2, TEST_USER_PW_2)


FTW_PARTICIPATION_FIXTURE = FtwParticipationLayer()
FTW_PARTICIPATION_INTEGRATION_TESTING = IntegrationTesting(
    bases=(FTW_PARTICIPATION_FIXTURE,), name="FtwParticipation:Integration")

FTW_PARTICIPATION_FUNCTIONAL_TESTING = FunctionalSplinterTesting(
    bases=(FTW_PARTICIPATION_FIXTURE,
           set_builder_session_factory(functional_session_factory)),
    name="FtwParticipation:Functional")
