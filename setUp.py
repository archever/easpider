
from setuptools import setup, find_packages

setup(name='easpider',
      version='1.0.1',
      keywords=('spider'),
      description='easy to spide',
      license='MIT License',

      url='http://archever.me',
      author='archever',
      author_email='archever@163.com',

      packages=find_packages(),
      include_package_data=True,
      platforms='any',
      install_requires=['requests', 'gevent'],
      classifiers=[
          'Environment :: Web Environment',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
          'Topic :: Software Development :: Libraries :: Python Modules'
      ],)