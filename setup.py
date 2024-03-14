from setuptools import setup, find_packages

setup(
    name='ebakery',
    version='0.1',
    packages=find_packages(),
    license='MIT',
    long_description=open('README.md').read(),
    install_requires=[
        'tqdm',
        'numpy',
        'pandas',
        'networkx',
        'matplotlib',
        'scikit-learn',
        'spacy',
        'nltk',
        'gensim',
        'requests',
        'sqlalchemy',
        'python-dotenv',
    ]
)