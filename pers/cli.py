import logging
from datetime import timedelta
from time import perf_counter

import click

from pers.config import Config
from pers.database.models import Base
from pers.database_engine import DatabaseEngine
from pers.elements import ElementsClient
from pers.importer import Importer

logger = logging.getLogger(__name__)
CONFIG = Config()


@click.group()
@click.option(
    "-v", "--verbose", help="Pass to log at debug level instead of info", is_flag=True
)
@click.pass_context
def main(ctx: click.Context, verbose: bool) -> None:
    ctx.ensure_object(dict)
    ctx.obj["START_TIME"] = perf_counter()
    logger.info(CONFIG.configure_logger(verbose))
    CONFIG.check_required_env_vars()
    db_engine = DatabaseEngine.configure(CONFIG.PERS_DATABASE_CONNECTION_STRING)
    elements_client = ElementsClient(
        user=CONFIG.ELEMENTS_USER,
        password=CONFIG.ELEMENTS_PASSWORD,
        proxies={"https": CONFIG.QUOTAGUARD_STATIC_URL},
    )
    elements_client.authenticate(url=CONFIG.ELEMENTS_ENDPOINT)
    ctx.obj["db_engine"] = db_engine
    ctx.obj["elements_client"] = elements_client
    logger.info("Running process")


@main.command()
@click.pass_context
def init_db(ctx: click.Context):
    logger.info("Initializing database")
    ctx.obj["db_engine"].init_db(metadata=Base.metadata)
    logger.info(
        "Total elapsed: %s",
        str(timedelta(seconds=perf_counter() - ctx.obj["START_TIME"])),
    )


@main.command()
@click.option(
    "--author-id",
    required=True,
    type=str,
    help="Unique identifier for an author in Symplectic Elements",
)
@click.pass_context
def import_citations(ctx: click.Context, author_id: str):
    importer = Importer(
        db_engine=ctx.obj["db_engine"],
        elements_client=ctx.obj["elements_client"],
        base_url=CONFIG.ELEMENTS_ENDPOINT,
    )
    importer.run(author_id)
    logger.info(
        "Total elapsed: %s",
        str(timedelta(seconds=perf_counter() - ctx.obj["START_TIME"])),
    )
