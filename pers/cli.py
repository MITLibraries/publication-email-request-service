import logging
from datetime import timedelta
from time import perf_counter

import click

from pers.config import Config
from pers.database_engine import DatabaseEngine
from pers.elements import ElementsClient

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
