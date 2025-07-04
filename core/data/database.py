import logging
import os
import secrets
import string
import warnings
from hashlib import sha256
from logging.handlers import TimedRotatingFileHandler
from typing import ClassVar, Optional

import alembic.config
import bcrypt
import coloredlogs
import pymysql.err
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

from core.config import CoreConfig
from core.data.schema import ArcadeData, BaseData, CardData, UserData, metadata
from core.utils import MISSING, Utils


class Data:
    engine: ClassVar[AsyncEngine] = MISSING
    session: ClassVar["sessionmaker[AsyncSession]"] = MISSING
    user: ClassVar[UserData] = MISSING
    arcade: ClassVar[ArcadeData] = MISSING
    card: ClassVar[CardData] = MISSING
    base: ClassVar[BaseData] = MISSING

    def __init__(self, cfg: CoreConfig) -> None:
        self.config = cfg

        if self.config.database.sha2_password:
            passwd = sha256(self.config.database.password.encode()).digest()
            self.__url = f"{self.config.database.protocol}+aiomysql://{self.config.database.username}:{passwd.hex()}@{self.config.database.host}:{self.config.database.port}/{self.config.database.name}"
        else:
            self.__url = f"{self.config.database.protocol}+aiomysql://{self.config.database.username}:{self.config.database.password}@{self.config.database.host}:{self.config.database.port}/{self.config.database.name}"

        if Data.engine is MISSING:
            Data.engine = create_async_engine(
                self.__url,
                pool_recycle=3600,
                isolation_level="AUTOCOMMIT",
                connect_args={
                    "charset": "utf8mb4",
                    "ssl": self.config.database.create_ssl_context_if_enabled(),
                },
            )
            self.__engine = Data.engine

        if Data.session is MISSING:
            Data.session = sessionmaker(Data.engine, expire_on_commit=False, class_=AsyncSession)

        if Data.user is MISSING:
            Data.user = UserData(self.config, self.session)
        
        if Data.arcade is MISSING:
            Data.arcade = ArcadeData(self.config, self.session)
        
        if Data.card is MISSING:
            Data.card = CardData(self.config, self.session)
        
        if Data.base is MISSING:
            Data.base = BaseData(self.config, self.session)

        self.logger = logging.getLogger("database")

        # Prevent the logger from adding handlers multiple times
        if not getattr(self.logger, "handler_set", None):            
            log_fmt_str = "[%(asctime)s] %(levelname)s | Database | %(message)s"
            log_fmt = logging.Formatter(log_fmt_str)
            fileHandler = TimedRotatingFileHandler(
                "{0}/{1}.log".format(self.config.server.log_dir, "db"),
                encoding="utf-8",
                when="d",
                backupCount=10,
            )
            fileHandler.setFormatter(log_fmt)

            consoleHandler = logging.StreamHandler()
            consoleHandler.setFormatter(log_fmt)

            self.logger.addHandler(fileHandler)
            self.logger.addHandler(consoleHandler)

            self.logger.setLevel(self.config.database.loglevel)
            coloredlogs.install(
                cfg.database.loglevel, logger=self.logger, fmt=log_fmt_str
            )
            self.logger.handler_set = True  # type: ignore

    def __alembic_cmd(self, command: str, *args: str) -> None:
        old_dir = os.path.abspath(os.path.curdir)
        base_dir = os.path.join(os.path.abspath(os.path.curdir), 'core', 'data', 'alembic')
        alembicArgs = [
            "-c",
            os.path.join(base_dir, "alembic.ini"),
            "-x",
            f"script_location={base_dir}",
            "-x",
            f"sqlalchemy.url={self.__url}",
            command,
        ]
        alembicArgs.extend(args)
        os.chdir(base_dir)
        alembic.config.main(argv=alembicArgs)
        os.chdir(old_dir)

    async def create_database(self):
        self.logger.info("Creating databases...")

        with warnings.catch_warnings():
            # SQLAlchemy will generate a nice primary key constraint name, but in
            # MySQL/MariaDB the constraint name is always PRIMARY. Every time a
            # custom primary key name is generated, a warning is emitted from pymysql,
            # which we don't care about. Other warnings may be helpful though, don't
            # suppress everything.            
            warnings.filterwarnings(
                action="ignore",
                message=r"Name '(.+)' ignored for PRIMARY key\.",
                category=pymysql.err.Warning,
            )

            async with self.engine.begin() as conn:
                await conn.run_sync(metadata.create_all, checkfirst=True)

                for _, mod in Utils.get_all_titles().items():
                    if hasattr(mod, "database"):
                        mod.database(self.config)

                        await conn.run_sync(metadata.create_all, checkfirst=True)

            # Stamp the end revision as if alembic had created it, so it can take off after this.
            self.__alembic_cmd(
                "stamp",
                "head",
            )

    def schema_upgrade(self, ver: Optional[str] = None):
        with warnings.catch_warnings():
            # SQLAlchemy will generate a nice primary key constraint name, but in
            # MySQL/MariaDB the constraint name is always PRIMARY. Every time a
            # custom primary key name is generated, a warning is emitted from pymysql,
            # which we don't care about. Other warnings may be helpful though, don't
            # suppress everything.            
            warnings.filterwarnings(
                action="ignore",
                message=r"Name '(.+)' ignored for PRIMARY key\.",
                category=pymysql.err.Warning,
            )

            self.__alembic_cmd(
                "upgrade",
                "head" if not ver else ver,
            )

    def schema_downgrade(self, ver: str):
        with warnings.catch_warnings():
            # SQLAlchemy will generate a nice primary key constraint name, but in
            # MySQL/MariaDB the constraint name is always PRIMARY. Every time a
            # custom primary key name is generated, a warning is emitted from pymysql,
            # which we don't care about. Other warnings may be helpful though, don't
            # suppress everything.            
            warnings.filterwarnings(
                action="ignore",
                message=r"Name '(.+)' ignored for PRIMARY key\.",
                category=pymysql.err.Warning,
            )

            self.__alembic_cmd(
                "downgrade",
                ver,
            )

    async def create_owner(self, email: Optional[str] = None, code: str = "00000000000000000000") -> None:
        pw = "".join(
            secrets.choice(string.ascii_letters + string.digits) for i in range(20)
        )
        hash = bcrypt.hashpw(pw.encode(), bcrypt.gensalt())

        user_id = await self.user.create_user(username="sysowner", email=email, password=hash.decode(), permission=255)
        if user_id is None:
            self.logger.error(f"Failed to create owner with email {email}")
            return

        card_id = await self.card.create_card(user_id, code)
        if card_id is None:
            self.logger.error(f"Failed to create card for owner with id {user_id}")
            return

        self.logger.warning(
            f"Successfully created owner with email {email}, access code {code}, and password {pw} Make sure to change this password and assign a real card ASAP!"
        )
    
    async def migrate(self) -> None:
        exist = await self.base.execute("SELECT * FROM alembic_version")
        if exist is not None:
            self.logger.warning("No need to migrate as you have already migrated to alembic. If you are trying to upgrade the schema, use `upgrade` instead!")
            return
        
        self.logger.info("Upgrading to latest with legacy system")
        if not await self.legacy_upgrade():
            self.logger.warning("No need to migrate as you have already deleted the old schema_versions system. If you are trying to upgrade the schema, use `upgrade` instead!")
            return
        self.logger.info("Done")
        
        self.logger.info("Stamp with initial revision")
        self.__alembic_cmd(
            "stamp",
            "835b862f9bf0",
        )

        self.logger.info("Upgrade")
        self.__alembic_cmd(
            "upgrade",
            "head",
        )
    
    async def legacy_upgrade(self) -> bool:
        vers = await self.base.execute("SELECT * FROM schema_versions")
        if vers is None:
            self.logger.warning("Cannot legacy upgrade, schema_versions table unavailable!")
            return False
        
        db_vers = {}
        vers_list = vers.fetchall()
        for x in vers_list:
            db_vers[x['game']] = x['version']
        
        core_now_ver = int(db_vers['CORE']) + 1
        while os.path.exists(f"core/data/schema/versions/CORE_{core_now_ver}_upgrade.sql"):
            with open(f"core/data/schema/versions/CORE_{core_now_ver}_upgrade.sql", "r") as f:
                result = await self.base.execute(f.read())
                
                if result is None:
                    self.logger.error(f"Invalid upgrade script CORE_{core_now_ver}_upgrade.sql")
                    break

                result = await self.base.execute(f"UPDATE schema_versions SET version = {core_now_ver} WHERE game = 'CORE'")
                if result is None:
                    self.logger.error(f"Failed to update schema version for CORE to {core_now_ver}")
                    break
            
            self.logger.info(f"Upgrade CORE to version {core_now_ver}")
            core_now_ver += 1
        
        for _, mod in Utils.get_all_titles().items():
            game_codes = getattr(mod, "game_codes", [])
            for game in game_codes:
                if game not in db_vers:
                    self.logger.warning(f"{game} does not have an antry in schema_versions, skipping")
                    continue

                now_ver = int(db_vers[game]) + 1
                while os.path.exists(f"core/data/schema/versions/{game}_{now_ver}_upgrade.sql"):
                    with open(f"core/data/schema/versions/{game}_{now_ver}_upgrade.sql", "r") as f:
                        result = await self.base.execute(f.read())
                        
                        if result is None:
                            self.logger.error(f"Invalid upgrade script {game}_{now_ver}_upgrade.sql")
                            break

                        result = await self.base.execute(f"UPDATE schema_versions SET version = {now_ver} WHERE game = '{game}'")
                        if result is None:
                            self.logger.error(f"Failed to update schema version for {game} to {now_ver}")
                            break

                    self.logger.info(f"Upgrade {game} to version {now_ver}")
                    now_ver += 1
        
        return True

    async def create_revision(self, message: str) -> None:
        if not message:
            self.logger.info("Message is required for create-revision")
            return
        
        self.__alembic_cmd(
            "revision",
            "-m",
            message,
        )

    async def create_revision_auto(self, message: str) -> None:
        if not message:
            self.logger.info("Message is required for create-revision")
            return
        
        for _, mod in Utils.get_all_titles().items():
            if hasattr(mod, "database"):
                mod.database(self.config)
        
        self.__alembic_cmd(
            "revision",
            "--autogenerate",
            "-m",
            message,
        )
