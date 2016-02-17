To upload a new version:

1. git tag a new version: `git tag v1.x.x`
2. Package: `python setup.py sdist`
3. Test installation using the tar: `pip install dist/*.tar`
4. `twine upload dist/*`
