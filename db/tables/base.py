from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class para definições de modelos SQLAlchemy do PagBank.

    https://fastapi.tiangolo.com/tutorial/sql-databases/#create-a-base-class
    https://docs.sqlalchemy.org/en/20/orm/mapping_api.html#sqlalchemy.orm.DeclarativeBase
    """

    metadata = MetaData(schema="public")


# Import all table definitions to ensure they are registered
from .agent_versions import AgentVersion, AgentVersionHistory, AgentVersionMetrics