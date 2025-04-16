from setuptools import setup, find_packages

setup(
    name="linguist",  # Replace with your package name
    version="0.1.0",  # Initial version
    description="A CLI and GUI tool for TTS and STT",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Michael Montanaro",
    author_email="mcmontanaro01@gmail.com",
    url="https://github.com/montymi/linguist",  # Replace with your repo URL
    license="GNU GPLv3",
    keywords="TTS STT CLI GUI",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=open("requirements.txt").read().splitlines(),
    entry_points={
        "console_scripts": [
            "linguist=linguist:main",  # Correctly reference the module
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)