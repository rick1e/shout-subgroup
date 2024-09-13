# Ping Dem Bot
This is a Telegram bot that mentions members of a group chat. It can also allow you
to mention subgroups within the chat.

## Requisites
- Docker
- Python 3.12+

## How to run
1. Create a `.env` file based on `.env.template`. 
2. Fill in the API keys as required. Use your own keys, or ask the maintainers.

### A. Using Rye
It's suggested to use the python build tool, [Rye](https://rye-up.com/guide/).
Installation guides can be found on their site.

After Rye is installed, you run the following:
1. Initialize the virtual environment and download the dependencies
`rye sync`
2. Build and run the application via a run script
`rye run build`
3. Stop the application via a run script
`rye run stop`

### B. Spinning Docker up manually
You can build and run the application as a docker containers with the following.
```shell
docker-compose up -d --build 
```

This will build the images for you then run them in a detached mode.
If you do not need to build the images, you can use the following command.
```shell
docker-compose up -d
```

## Building only the app image
Use the following command to build the image
```shell
docker build . -t <tag-the-image>
```

## Running the database
You can run the database separately from the application. To do so run
`rye run db`

Alternatively, if you need more control you can do the steps below
`docker-compose up db -d`

After the database starts, it will have no tables. You'll need to
run the migration. See the [Running database migrations](#running-database-migrations)

### Running database migrations
We use [Alembic](https://alembic.sqlalchemy.org/en/latest/index.html#) to handle migrations.
Alembic will autogenerate schemas for us whenever we change the database model.

Make sure the `MIGRATE` environment variable is set to "true"

Create an alembic revision
`alembic revision --autogenerate -m <revision message>`

After the revision is created, run below to apply the changes
`alembic upgrade head`