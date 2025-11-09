from setuptools import setup, find_packages

setup(
    name="downloadbeast-leviathon",
    version="6.3.3",
    description="DownloadBeast - Leviathon: URL & Video downloader with subtitle, transcription, translation and dubbing tools",
    author="Colin KaiserKobayashi Gerrard",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "downloadbeast-leviathon = downloadbeast.__main__:main",
        ],
    },
)