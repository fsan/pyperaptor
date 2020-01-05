from distutils.core import setup
setup(
  name = 'pyperaptor',
  packages = ['pyperaptor'],
  version = '0.1.0',
  license='MIT',
  description = 'Small pipeline organizer for multiprocessing execution',
  author = 'fsan',
  author_email = "pabyo.sansinaeti@gmail.com",
  url = 'https://github.com/fsan/pyperaptor',
  download_url = 'https://github.com/fsan/pyperaptor/releases/download/0.1.0/pyperaptor-0.1.0.tar.gz',
  keywords = ['pipeline', 'dinossaurs', 'threading'],
  install_requires=[
      ],
  classifiers=[
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'Topic :: Other/Nonlisted Topic',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
  ],
)
