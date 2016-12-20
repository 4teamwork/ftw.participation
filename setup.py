from setuptools import setup, find_packages
import os

version = '1.5.0'
maintainer = 'Jonas Baumann'

tests_require = (
    'zope.testing',
    'plone.app.testing',
    'zope.globalrequest', # Because of TinyMCE
    'ftw.activity > 2',
    'ftw.builder',
    'ftw.testbrowser',
    'ftw.testing',
    'ftw.builder',
    'ftw.tabbedview',
    )


extras_require = {
    'tests': tests_require,
    'activity': [
        'ftw.activity > 2',
    ]
}


setup(name='ftw.participation',
      version=version,
      description='Invite other users (registered or unregistered) to a ' + \
          'context in plone.',
      long_description=open('README.rst').read() + '\n' + \
          open(os.path.join('docs', 'HISTORY.txt')).read(),


      # Get more strings from
      # http://www.python.org/pypi?%3Aaction=list_classifiers

      classifiers=[
        'Framework :: Plone',
        'Framework :: Plone :: 4.3',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ],

      keywords='ftw participation plone',
      author='4teamwork AG',
      author_email='mailto:info@4teamwork.ch',
      maintainer=maintainer,
      url='https://github.com/4teamwork/ftw.participation',
      license='GPL2',

      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['ftw'],
      include_package_data=True,
      zip_safe=False,

      install_requires=[
        'Plone',
        'archetypes.schemaextender',
        'ftw.upgrade>=1.6.0',
        'plone.app.registry',
        'plone.formwidget.autocomplete',
        'plone.principalsource',
        'plone.z3cform',
        'setuptools',
        'z3c.form',
        ],

      tests_require=tests_require,
      extras_require=extras_require,
      entry_points='''
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone
      ''',
      )
