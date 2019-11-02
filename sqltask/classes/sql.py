import logging
from collections import namedtuple
from typing import Iterator, TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy.engine import RowProxy
from sqlalchemy.sql import text

from sqltask.classes.common import BaseDataSource

if TYPE_CHECKING:
    from sqltask.classes.engine import EngineContext


class SqlDataSource(BaseDataSource):
    def __init__(
            self,
            sql: str,
            params: Dict[str, Any],
            engine_context: "EngineContext",
            name: Optional[str] = None,
            database: Optional[str] = None,
            schema: Optional[str] = None,
    ):
        """
        :param sql: sql query with parameter values prefixed with a colon, e.g.
        `WHERE dt <= :batch_date`
        :param params: mapping between parameter keys and values, e.g.
        `{"batch_date": date(2010, 1, 1)}`
        :param name: name of data source
        :param database: database to use when executing query. Uses database defined
        in sql_engine if left undefined.
        :param schema: schema to use when executing query. Uses schema defined
        in sql_engine if left undefined.
        :param engine_context: engine used to execute the query.
        """
        params = params or {}
        database = database or engine_context.database
        schema = schema or engine_context.schema
        super().__init__(name)
        self.sql = sql
        self.params = params or {}
        self.database = database or engine_context.database
        self.schema = schema or engine_context.schema
        self.engine_context = engine_context.create_new(
            database=self.database, schema=self.schema
        )

    def __iter__(self) -> Iterator[RowProxy]:
        rows = self.engine_context.engine.execute(text(self.sql), self.params)
        for row in rows:
            yield row
