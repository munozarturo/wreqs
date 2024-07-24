from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="wreqs",
    version="1.2.1",
    author="Arturo Munoz",
    author_email="munoz.arturoroman@gmail.com",
    description="Simplified and enhanced request handling.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/munozarturo/wreqs",
    packages=find_packages(),
    package_data={"wreqs": ["py.typed"]},
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP",
    ],
    keywords="http, requests, wrapper, retry, timeout",
    python_requires=">=3.7",
    install_requires=["requests>=2.20.0"],
    extras_require={
        "dev": ["pytest", "pytest-cov", "flask", "mypy", "flake8", "black"],
        "docs": ["sphinx", "sphinx_rtd_theme"],
    },
    project_urls={
        "Bug Reports": "https://github.com/munozarturo/wreqs/issues",
        "Source": "https://github.com/munozarturo/wreqs/",
    },
)
