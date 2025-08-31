from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="gridiron-guru-ai",
    version="1.0.0",
    author="tsmith4014",
    description="AI-Powered Fantasy Football Draft Assistant with ML-driven recommendations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tsmith4014/gridiron-guru-ai",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Topic :: Games/Entertainment",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    include_package_data=True,
    package_data={
        "app": ["static/*", "frontend/*"],
    },
    entry_points={
        "console_scripts": [
            "gridiron-guru=main:main",
        ],
    },
)
