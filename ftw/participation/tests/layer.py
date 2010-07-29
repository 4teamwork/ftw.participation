from Products.PloneTestCase import ptc
from collective.testcaselayer import common
from collective.testcaselayer import ptc as tcl_ptc


class Layer(tcl_ptc.BasePTCLayer):
    """Install ftw.participation"""

    def afterSetUp(self):
        ptc.installPackage('ftw.participation')
        self.addProfile('ftw.participation:default')

layer = Layer([common.common_layer])
