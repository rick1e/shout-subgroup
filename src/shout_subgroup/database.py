import logging
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


def configure_database() -> bool:
    load_dotenv()

    POSTGRES_USER = os.getenv('POSTGRES_USER')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
    POSTGRES_DB = os.getenv('POSTGRES_DB')
    POSTGRES_CONTAINER = os.getenv('POSTGRES_CONTAINER')

    db_configs = {
        "POSTGRES_USER": POSTGRES_USER,
        "POSTGRES_PASSWORD": "*****",
        "POSTGRES_HOST": POSTGRES_CONTAINER,
        "POSTGRES_DB": POSTGRES_DB,
    }
    logger.info(f"Loaded Database configs {db_configs}")

    try:
        engine = create_engine(
            f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_CONTAINER}:5432/{POSTGRES_DB}", echo=True
        )
        logger.info("Created database engine")
    except Exception as ex:
        logger.exception(f"Unable to connect to postgreSQL. See exception details ... {ex}")
        return False

    global Session

    Session = sessionmaker(bind=engine, expire_on_commit=False)

    return True


def get_database():
    return Session
