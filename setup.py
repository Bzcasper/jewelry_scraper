from setuptools import setup, find_packages

setup(
    name="jewelry_scraper",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        line.strip()
        for line in open("pip_requirements.txt")
        if not line.startswith("#")
    ],
)