# the publishing is now managed by .github/workflows/publish.yml now but still can be built and pushed locally

# rebuild frontend
rm -rf server/static/
npm install web/ --prefix web/
npm run build --prefix web/

# rebuild package
rm -rf {build,dist,pearmut.egg-info}/*
python3 -m build 

# publish to pypi
python3 -m twine upload dist/* -u __token__

# for local editable install
# pip install -e . --config-settings editable_mode=strict