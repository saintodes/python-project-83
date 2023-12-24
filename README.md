[Try page analyzer](https://page-analyzer-jhv6.onrender.com/) 

### Hexlet tests and linter status:

[![Actions Status](https://github.com/saintodes/python-project-83/actions/workflows/hexlet-check.yml/badge.svg)](https://github.com/saintodes/python-project-83/actions)[![Linter check](https://github.com/saintodes/python-project-83/actions/workflows/python-app.yml/badge.svg)](https://github.com/saintodes/python-project-83/actions/workflows/python-app.yml)[![Maintainability](https://api.codeclimate.com/v1/badges/dbc6d478d65edc9a7ff5/maintainability)](https://codeclimate.com/github/saintodes/python-project-83/maintainability)



## Objective

The objective of this project is to develop a full-fledged web application that mimics the functionality of tools like PageSpeed Insights for SEO suitability analysis. Throughout this project, I've gained practical experience in:

- Understanding and handling HTTP requests and responses.
- Implementing routing with HTTP methods to create specific routes.
- Designing and managing a database schema without using migrations.
- Executing SQL queries using the psycopg library.
- Incorporating Bootstrap components for front-end styling.
- Setting up a local development environment with a web server and database.
- Familiarizing with TCP protocol fundamentals, IP addresses, and ports.
- Deploying the application to production using the PaaS model on render.com.

## Features

- **SEO Analysis**: Evaluate pages for SEO effectiveness.
- **Performance Metrics**: Similar to PageSpeed Insights, provide insights on page performance.
- **User-friendly Interface**: Utilize Bootstrap for a responsive and intuitive design


## Prerequisites
- Python 3.10 or higher
- Poetry for dependency management


## Setup Instructions

First, ensure you have Poetry installed. If you do not have Poetry installed, you can install it with the following command:
```bash
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
```
Or follow the instructions on the [official Poetry website](https://python-poetry.org/docs/)

Also you need Postgres client. Install it with next command:
```bash
sudo apt install postgresql
'''

Once you have Poetry and Postgres installed, you can set up the project using the following steps:

1. Clone the repository:
```bash
git clone git@github.com:saintodes/python-project-83.git
cd page-analyzer
```
2. Install the project dependencies:
```bash
poetry install
```
3. Make the build scripts executable:
``` bash
make gr
```

## Deployment on render.com

Before deploying to render.com, you need to set up a PostgreSQL server on their platform. Once your database server is up, you should specify the connection string in the environment variables of your project. This will allow the service to connect to the correct database during the build and deployment process.

To build the application on render.com, use the following command:

```bash
make build
```
To start the application with Gunicorn on render.com, use the command:
```bash
make start
```
If you want to run the Flask app in debug mode on render.com, specify the command:
```bash
make start-dev-external
```

## Local Deployment
You also have the option to build and run the application locally.

To build locally and set up the database, use the command:
```bash
make dev-build-local-db
```
Please note that sudo access will be requested to create the database, user, and configure the appropriate permissions.

To start the Flask app in dev mode locally, you can use the command:
```bash
make start-dev-local
```

## Local Deployment with external PostgeSQL server 
You have the option to start local web server with external DB connection.
To build it use the command:
```bash
make dev-build-render-db:
```
Make sure that the .env file contains the current string for connecting to the remote database
To start the Flask app in dev mode locally, you can use the same command:
```bash
make start-dev-local
```
