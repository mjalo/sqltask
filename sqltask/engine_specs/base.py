from enum import Enum
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.engine.url import URL
from sqlalchemy.sql import text
from sqltask.common import TableContext

log = logging


class UploadType(Enum):
    SQL_INSERT = 1
    CSV = 2


class BaseEngineSpec:
    """
    Generic spec defining default behaviour for SqlAlchemy engines.
    """
    engine: Optional[str] = None
    default_upload_type = UploadType.SQL_INSERT
    supports_column_comments = True
    supports_table_comments = True
    supports_schemas = True

    @classmethod
    def insert_rows(cls, output_rows: List[Dict[str, Any]],
                    table_context: TableContext,
                    upload_type: Optional[UploadType] = None) -> None:
        """
        Default method for inserting data into database. This

        :param output_rows: Rows to upload.
        :param table_context: Table context on which the upload should be based.
        :param upload_type: If undefined, defaults to whichever ´UploadType` is defined
        in `default_upload_type`.
        """
        upload_type = upload_type or cls.default_upload_type
        if upload_type == UploadType.SQL_INSERT:
            cls._insert_rows_sql_insert(output_rows, table_context)
        elif upload_type == UploadType.CSV:
            cls._insert_rows_csv(output_rows, table_context)
        else:
            raise NotImplementedError(f"Unsupported upload type: {upload_type}")

    @classmethod
    def _insert_rows_sql_insert(cls, output_rows: List[Dict[str, Any]],
                                table_context: TableContext) -> None:
        """
        Insert rows using standard insert statements. Not very performant, but mostly
        universally supported.
        """
        with table_context.engine_context.engine.begin() as conn:
            conn.execute(table_context.table.insert(), *output_rows)

    @classmethod
    def _insert_rows_csv(cls, output_rows: List[Dict[str, Any]],
                         table_context: TableContext) -> None:
        raise NotImplementedError(f"`{cls.__name__}` does not support CSV upload")

    @classmethod
    def truncate_rows(cls, table_context: TableContext,
                      batch_params: Dict[str, Any]) -> None:
        """
        Delete old rows from target table that match the execution parameters.

        :param table: Output table
        :param execution_columns: execution
        :param params:
        :return:
        """
        table = table_context.table
        engine = table_context.engine_context.engine
        where_clause = " AND ".join(
            [f"{col} = :{col}" for col in batch_params.keys()])
        stmt = f"DELETE FROM {table.name} WHERE {where_clause}"
        engine.execute(text(stmt), batch_params)

    @classmethod
    def get_schema_name(cls, url: URL) -> Optional[str]:
        """
        Extract schema name from URL instance. Assumes that the schema name is what
        cmes after a slash in the database name, e.g. `database/schema`.

        :param url: SqlAlchemy URL instance
        :return: schema name
        """
        schema = None
        if cls.supports_schemas and "/" in url.database:
            schema = url.database.split("/")[1]
        return schema
