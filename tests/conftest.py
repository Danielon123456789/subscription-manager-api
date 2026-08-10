import pytest
from app.core.config import settings
from sqlalchemy.orm import sessionmaker
from app.core.database import engine
from sqlalchemy import event


@pytest.fixture(scope="session", autouse=True)
def guard_test_database():
    database_url = str(settings.DATABASE_URL)

    if "test" not in database_url:
        pytest.exit(
            f"ABORTED: test must run against a test database. Got: {database_url}"
        )

    yield


@pytest.fixture()
def db_session():
    connection = engine.connect()
    transaction = connection.begin()

    TestingSessionLocal = sessionmaker(bind=connection)
    session = TestingSessionLocal()

    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, trans):
        if trans.nested and not trans._parent.nested:
            sess.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()
