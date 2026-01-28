from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize(
        [
            "app/gui.py",
            "app/main_cli.py",
            "app/extractor.py",
            "app/parser.py",
            "app/storage.py",
            "app/config.py",
            "app/models.py",
            "app/utils.py",
        ],
        language_level=3,
        compiler_directives={"always_allow_keywords": True}
    )
)
