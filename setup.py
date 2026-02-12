# setup.py en C:\Users\ALEXIS\Desktop\API-SISTEMA-MODULAR\setup.py

from setuptools import setup, find_packages

setup(
    name="observability-logs",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.68.0",
        "pymongo>=4.0.0",
        "click>=8.0.0",
        "tabulate>=0.8.9",
        "requests>=2.26.0",
        "pydantic>=1.8.0",
    ],
    python_requires=">=3.8",
)