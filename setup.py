from setuptools import setup

setup(
    name="supabase-async",
    version="0.1.0",
    description="Supabase Async Client — requests + ThreadPoolExecutor 기반",
    author="JustJino",
    author_email="dogfootbro@gmail.com",
    url="https://github.com/justjiinoit/supabase-async",
    py_modules=["supabase_async"],
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.31.0",
        "tenacity>=8.2.0",
    ],
    extras_require={
        "dev": ["pytest", "pytest-asyncio"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
