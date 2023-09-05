import models
from sqlalchemy.orm import Session
from database import SessionLocal,engine

import logging

class PostgresHandler(logging.Handler):
    def __init__(self, connection, table_name="logs"):
        super().__init__()
        self.connection = connection
        self.table_name = table_name

    def emit(self, record):
        try:
            log = models.Log(level=record.levelname, message=record.msg)
            with SessionLocal() as session:
                session.add(log)
                session.commit()
        except Exception as e:
            print(f"Error while logging to PostgreSQL: {e}")



def get_custom_logger(connection, table_name="logs"):
    logger = logging.getLogger("custom_logger")
    if not logger.handlers:  # Check if handlers are already set
        logger.setLevel(logging.INFO)
        handler = PostgresHandler(connection, table_name)
        logger.addHandler(handler)
    return logger
