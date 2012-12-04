from setuptools import setup, find_packages
import os

version = '1.0rc14'

setup(name='gu.moai.rifcs',
      version=version,
      description="MOAI RIFCS metadata support",
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
      namespace_packages=['gu', 'gu.moai'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'MOAI',
      ],
      entry_points="""
      [moai.format]
      rif = gu.moai.rifcs.rifcs:RIFCSMetadataFormat
      """,
      )
