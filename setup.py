from setuptools import setup
import os

ROOT_DIR='pynortek'
with open(os.path.join(ROOT_DIR, 'VERSION')) as version_file:
    version = version_file.read().strip()

setup(name='pynortek',
      version=version,
      description='Tool to parse Nortek data files',
      url='https://github.com/MarineDataTools/pynortek',
      author='Peter Holtermann',
      author_email='peter.holtermann@io-warnemuende.de',
      license='GPLv03',
      packages=['pynortek'],
      scripts = [],
      entry_points={'console_scripts': ['pynortek_time=pynortek.nortek_time:main','pynortek_time_gui=pynortek.nortek_time:gui','pynortek_vec2nc=pynortek.pynortek_binary:vec2nc']},
      package_data = {'':['VERSION']},
      zip_safe=False)


