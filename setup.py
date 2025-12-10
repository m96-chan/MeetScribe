"""
Setup configuration for MeetScribe.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
if requirements_path.exists():
    with open(requirements_path, encoding="utf-8") as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]
else:
    requirements = []

setup(
    name="meetscribe",
    version="0.1.0",
    description="Multi-source AI Meeting Pipeline Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="MeetScribe Contributors",
    author_email="",
    url="https://github.com/yourusername/meetscribe",
    license="Apache-2.0",
    packages=find_packages(exclude=["tests", "docs"]),
    include_package_data=True,
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
        "discord": [
            "discord.py>=2.3.0",
            "py-cord>=2.4.0",
        ],
        "all": [
            "discord.py>=2.3.0",
            "py-cord>=2.4.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "meetscribe=meetscribe.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Office/Business",
    ],
    keywords="meeting transcription ai llm minutes notebooklm discord zoom",
)
