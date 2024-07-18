import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from shout_subgroup.models import Base

# Create an SQLite in-memory database and a session factory
engine = create_engine('sqlite:///:memory:', echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    # Create tables
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    
    try:
        yield session
    finally:
        # Close the session and drop all tables
        session.close()
    
    Base.metadata.drop_all(bind=engine)
