from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="hierarchical-research-ai",
    version="0.1.0",
    author="Strategic Consulting",
    description="Hierarchical Multi-Agent Research System with Conversational CLI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/strategic-consulting/hierarchical-research-ai",
    
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    
    # Dual entry points for CLI and module access
    entry_points={
        "console_scripts": [
            "research-ai=hierarchical_research_ai.cli.interface:main",
            "hrai=hierarchical_research_ai.cli.interface:main",  # Short alias
        ]
    },
    
    # Python API access
    python_requires=">=3.9",
    install_requires=[
        "langgraph>=0.2.27",
        "langchain>=0.3.0",
        "langchain-community>=0.3.0",
        "langchain-anthropic>=0.2.0",
        "langchain-ollama>=0.2.0",
        "python-dotenv>=1.0.0",
        "rich>=13.7.0",
        "click>=8.1.0",
        "questionary>=2.0.0",
        "httpx>=0.25.0",
        "requests>=2.31.0",
        "pandas>=2.1.0",
        "numpy>=1.24.0",
        "aiohttp>=3.9.0",
        "tenacity>=8.2.0",
        "structlog>=23.2.0",
    ],
    
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.23.0",
            "pytest-mock>=3.12.0",
            "black>=23.11.0",
            "flake8>=6.1.0",
            "mypy>=1.7.0",
            "pre-commit>=3.6.0",
        ],
        "research": [
            "scholarly>=1.7.0",
            "arxiv>=2.1.0",
            "beautifulsoup4>=4.12.0",
            "pypdf>=3.17.0",
            "python-docx>=1.1.0",
            "markdown>=3.5.0",
        ],
        "ml": [
            "sentence-transformers>=2.2.0",
            "transformers>=4.35.0",
            "tokenizers>=0.15.0",
        ],
    },
    
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)