# athenapythontest

A sample app to show how to access BV's Raven data in Athena using Python.

## What it is

This app does one thing: run simple, hard-coded queries against
Raven data in Athena. The intent is to show how to
accomplish Athena queries in a Python webapp.

**To understand how it works, [read app.py](./app.py)!** The code contains comments that describe what it does and why.

### What it is not

This app is intended to be a naive introduction to querying Athena in Python; nothing more, nothing less. It is not a
tutorial or general guide for SQL, Raven, Athena, Flask, Python, or Flynn. However, if you are interested in those
topics, check out these resources:

* [Amazon AWS Athena](https://aws.amazon.com/athena/)
  * [Athena SQL Reference](https://docs.aws.amazon.com/athena/latest/ug/functions-operators-reference-section.html)
* [Flask quickstart](http://flask.pocoo.org/docs/quickstart/)
* [Flynn](https://flynn.io/docs/basics)

## Setup and Running Locally

```bash
# install python 3 if needed
brew install python3

# clone this repo
git clone git@github.com:bazaarvoice/athenapythontest.git

# create a virtual environment and activate it
cd ./athenapythontest
python3 -m venv ./.venv
source ./.venv/bin/activate

# install dependencies to the virtual environment
pip install --requirement ./requirements.txt

# run the app
./start.sh
```

## Deployment

**DO NOT** deploy this app unless you are _positive_ you won't overwrite someone else's deployment.

```bash
./deploy/deploy.sh
```

### Scoped Deployment

If you must deploy, scope your deployment to avoid overwriting someone else's deployment.

```bash
BVFLYNN_APP_SCOPE=<your ldap> ./deploy/deploy.sh
```
