from setuptools import setup

setup(
    name="milnlp",
    version="0.1.0",
    description="Packaged military tools for nlp tasks.",
    author="Zach Welz",
    author_email="zach.welz@gtri.gatech.edu",
    url="https://github.com/zwelz3/milnlp",
    license="GNU General Public License v3.0",
    keywords=[
        "data mining",
        "NLP",
        "natural language processing",
        "knowledge management",
        "summarization"
    ],
    install_requires=[
        "pycountry>=18.2.23",
        "nltk>=3.0.2",
        "sumy>=0.7.0",
    ],)
