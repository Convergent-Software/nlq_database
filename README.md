# NLQ

Conversational data analysis tool. 

## Installation and Setup

Install the packages:

```bash
pip install -r requirements.txt
```

### Updating Packages

If packages are added or require updates, be sure to run the following to capture the package state:

```bash
pip freeze > requirements.txt
```

Make sure the above is ran in a ```env``` environment.
To make one, run the following:

```bash
python -m venv env
```

When you need to activate the environment, run:

```bash
source env/bin/activate
```

### Setup

From home directory, allow the BASH script as an executable:

```bash
chmod +x runner.sh
```

Following the ```.env.example``` file, create a local ```.env``` file that has those credentials in the same directory.

## Seeding Data

There are useful data generators available if needed across various domains. To configure your generator, modify ```setup.py```.

Then, run the following:

```bash
./runner.sh seed 
```

More generators can be created using ```Faker``` inside ```db/generators```.

## Run App:

To run the app (after following 'Setup'), simply run:

```bash
./runner.sh
```
## Format Code:

Prior to commiting, run the formatter:

```bash
./runner.sh format
```