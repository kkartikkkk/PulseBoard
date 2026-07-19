from setuptools import setup, find_packages

setup(
    name="pulseboard-sdk",
    version="1.0.0",
    description="Python SDK for PulseBoard — real-time API analytics",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "httpx>=0.27.0",
    ],
    python_requires=">=3.10",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Framework :: FastAPI",
    ],
)
