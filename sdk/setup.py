"""Setup configuration for qilbee-mycelial-network SDK."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="qilbee-mycelial-network",
    version="0.1.2",
    author="AICUBE TECHNOLOGY LLC",
    author_email="contact@aicube.ca",
    description="Enterprise SaaS SDK for Qilbee Mycelial Network - Adaptive AI Agent Communication",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/qilbee/mycelial-network",
    project_urls={
        "Homepage": "http://www.qilbee.io",
        "Documentation": "http://www.qilbee.io/docs",
        "Source": "https://github.com/qilbee/mycelial-network",
        "Tracker": "https://github.com/qilbee/mycelial-network/issues",
        "Changelog": "https://github.com/qilbee/mycelial-network/releases",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=[
        "httpx>=0.25.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "mypy>=1.0.0",
        ],
        "grpc": [
            "grpcio>=1.50.0",
            "grpcio-tools>=1.50.0",
        ],
        "quic": [
            "aioquic>=0.9.0",
        ],
        "telemetry": [
            "opentelemetry-api>=1.20.0",
            "opentelemetry-sdk>=1.20.0",
            "opentelemetry-instrumentation-httpx>=0.41b0",
        ],
    },
    entry_points={
        "console_scripts": [
            "qmn=qilbee_mycelial_network.cli:main",
        ],
    },
)
