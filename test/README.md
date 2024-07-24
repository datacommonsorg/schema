# Schema Validation

In addition to the [import tool](https://github.com/datacommonsorg/import), we
do further validations of schema.

## Install requirements

```
pip install -r requirements.txt
```

## URL Checker

We check that all new urls referenced in schema are valid (i.e. return a 200
status code). To run the url checker:

```
export DC_API_KEY=<AUTOPUSH KEY>
python3 url_checker.py
```

Please fix all invalid urls. (Note that redirects are considered invalid and
should be replaced by the final url or otherwise updated). By default the
checker will only process locally modified files (i.e. not yet commited).

`url_allowlist.csv` contains previously submitted invalid urls. After fixing a
url in the allowlist, remove it from the allowlist and re-run the checker to
make sure it passes. (When fixing a url, make sure to update each occurrence in
the schema. Since the checker only tests locally modified files, you can commit
each modified file separately to avoid rechecking files that you've already
updated.)

Alternatively you can automatically update the allowlist (however this will take
more time since it will process all files):

```
export DC_API_KEY=<AUTOPUSH KEY>
python3 url_checker.py --update_allowlist
```
