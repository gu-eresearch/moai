from setuptools import setup, find_packages
import os

version = '1.0-rc21'

setup(name='gu.rh.moai',
      version=version,
      description="MOAI configuration and plugins for ResearchHub",
      #long_description=open("README.txt").read() + "\n" +
      #                 open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from
      # http://pypi.python.org/pypi?:action=list_classifiers
      #classifiers=[
      #  "Framework :: Plone",
      #  "Programming Language :: Python",
      #  ],
      keywords='',
      author='',
      author_email='',
      #url='http://svn.plone.org/svn/collective/',
      #license='GPL',
      packages=find_packages('src'),
      package_dir={'':'src'},
      namespace_packages=['gu', 'gu.rh'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'rdflib',
          'MOAI',
          'gu.moai.rifcs',
          'pasteScript',
      ],
      entry_points="""
      [moai.content]
      moai_rh = gu.rh.moai.content:RDFContentObject

      [moai.provider]
      moai_rh = gu.rh.moai.provider:ContentProvider
      """,
      )
