from setuptools import setup, find_packages
import os

version = open('ftw/participation/version.txt').read().strip()
maintainer = 'Jonas Baumann'

setup(name='ftw.participation',
      version=version,
      description="Invite other users (register or unregistered) to a context" + \
          ' (Maintainer: %s)' % maintainer,
      long_description=open("README.txt").read() + "\n" + \
          open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        ],
      keywords='ftw participation',
      author='%s, 4teamwork GmbH' % maintainer,
      author_email='mailto:info@4teamwork.ch',
      maintainer=maintainer,
      url='http://psc.4teamwork.ch/4teamwork/ftw/ftw-participation',
      license='GPL2',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['ftw'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'z3c.form',
        'plone.z3cform',
        'setuptools',
        'plone.browserlayer',
        'z3c.autoinclude',
        ],
      entry_points="""
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
