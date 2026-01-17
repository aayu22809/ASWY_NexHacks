"""
Setup script for Plasma Jet Path Planner.

Install in development mode:
    pip install -e .

Install with all dependencies:
    pip install -e ".[dev]"
"""

from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

# Core dependencies
INSTALL_REQUIRES = [
    'numpy>=1.21.0,<2.0.0',
    'scipy>=1.7.0',
    'pyrealsense2>=2.56.5',
    'open3d>=0.17.0',
    'matplotlib>=3.5.0',
    'pyyaml>=6.0',
]

# Development dependencies
DEV_REQUIRES = [
    'pytest>=7.0.0',
    'pytest-cov>=4.0.0',
    'black>=23.0.0',
    'flake8>=6.0.0',
    'mypy>=1.0.0',
    'sphinx>=5.0.0',
]

# Optional dependencies
EXTRAS_REQUIRE = {
    'dev': DEV_REQUIRES,
    'docs': [
        'sphinx>=5.0.0',
        'sphinx-rtd-theme>=1.0.0',
    ],
}

setup(
    name='plasma-jet-path-planner',
    version='1.0.0',
    author='ASWY NexHacks Team',
    author_email='',
    description='Intelligent path planning system for cold atmospheric plasma wound healing',
    long_description=read_readme(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/ASWY_NexHacks',
    packages=find_packages(exclude=['tests', 'tests.*', 'docs', 'frontend']),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Healthcare Industry',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Medical Science Apps.',
        'Topic :: Scientific/Engineering :: Image Recognition',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    entry_points={
        'console_scripts': [
            'plasma-scanner=run_scanner:main',
            'plasma-planner=run_planner:main',
            'plasma-visualizer=run_visualizer:main',
            'plasma-pipeline=run_full_pipeline:main',
        ],
    },
    include_package_data=True,
    package_data={
        'backend': ['py.typed'],
        'config': ['*.yaml'],
    },
    zip_safe=False,
    keywords='plasma medical robotics path-planning 3d-scanning',
    project_urls={
        'Documentation': 'https://github.com/yourusername/ASWY_NexHacks/docs',
        'Source': 'https://github.com/yourusername/ASWY_NexHacks',
        'Tracker': 'https://github.com/yourusername/ASWY_NexHacks/issues',
    },
)

