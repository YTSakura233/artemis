import re
from typing import List, Optional

from sqlalchemy import Column, Table, and_, or_
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.engine import Row
from sqlalchemy.sql import func, select
from sqlalchemy.sql.schema import ForeignKey, PrimaryKeyConstraint
from sqlalchemy.types import JSON, Boolean, Integer, String

from core.data.schema.base import BaseData, metadata

arcade: Table = Table(
    "arcade",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("name", String(255)),
    Column("nickname", String(255)),
    Column("country", String(3)),
    Column("country_id", Integer),
    Column("state", String(255)),
    Column("city", String(255)),
    Column("region_id", Integer),
    Column("timezone", String(255)),
    Column("ip", String(39)),
    mysql_charset="utf8mb4",
)

machine: Table = Table(
    "machine",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "arcade",
        ForeignKey("arcade.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("serial", String(15), nullable=False),
    Column("board", String(15)),
    Column("game", String(4)),
    Column("country", String(3)),  # overwrites if not null
    Column("timezone", String(255)),
    Column("ota_enable", Boolean),
    Column("memo", String(255)),
    Column("is_cab", Boolean),
    Column("data", JSON),
    mysql_charset="utf8mb4",
)

arcade_owner: Table = Table(
    "arcade_owner",
    metadata,
    Column(
        "user",
        Integer,
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column(
        "arcade",
        Integer,
        ForeignKey("arcade.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("permissions", Integer, nullable=False),
    PrimaryKeyConstraint("user", "arcade", name="arcade_owner_pk"),
    mysql_charset="utf8mb4",
)


class ArcadeData(BaseData):
    async def get_machine(self, serial: Optional[str] = None, id: Optional[int] = None) -> Optional[Row]:
        if serial is not None:
            serial = serial.replace("-", "")
            if len(serial) == 11:
                sql = machine.select(machine.c.serial.like(f"{serial}%"))

            elif len(serial) == 15:
                sql = machine.select(machine.c.serial == serial)

            else:
                self.logger.error(f"{__name__ }: Malformed serial {serial}")
                return None

        elif id is not None:
            sql = machine.select(machine.c.id == id)

        else:
            self.logger.error(f"{__name__ }: Need either serial or ID to look up!")
            return None

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()

    async def create_machine(
        self,
        arcade_id: int,
        serial: str = "",
        board: Optional[str] = None,
        game: Optional[str] = None,
        is_cab: bool = False,
    ) -> Optional[int]:
        if not arcade_id:
            self.logger.error(f"{__name__ }: Need arcade id!")
            return None

        sql = machine.insert().values(
            arcade=arcade_id, serial=serial, board=board, game=game, is_cab=is_cab
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.lastrowid

    async def set_machine_arcade(self, machine_id: int, new_arcade: int) -> bool:
        sql = machine.update(machine.c.id == machine_id).values(arcade = new_arcade)
        
        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to update machine {machine_id} arcade to {new_arcade}")
            return False
        return True

    async def set_machine_serial(self, machine_id: int, serial: str) -> None:
        result = await self.execute(
            machine.update(machine.c.id == machine_id).values(keychip=serial)
        )
        if result is None:
            self.logger.error(
                f"Failed to update serial for machine {machine_id} -> {serial}"
            )
        return result.lastrowid

    async def set_machine_boardid(self, machine_id: int, boardid: str) -> None:
        result = await self.execute(
            machine.update(machine.c.id == machine_id).values(board=boardid)
        )
        if result is None:
            self.logger.error(
                f"Failed to update board id for machine {machine_id} -> {boardid}"
            )

    async def set_machine_game(self, machine_id: int, new_game: Optional[str]) -> bool:
        sql = machine.update(machine.c.id == machine_id).values(game = new_game)
        
        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to update machine {machine_id} game to {new_game}")
            return False
        return True

    async def set_machine_country(self, machine_id: int, new_country: Optional[str]) -> bool:
        sql = machine.update(machine.c.id == machine_id).values(country = new_country)
        
        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to update machine {machine_id} country to {new_country}")
            return False
        return True

    async def set_machine_timezone(self, machine_id: int, new_timezone: Optional[str]) -> bool:
        sql = machine.update(machine.c.id == machine_id).values(timezone = new_timezone)
        
        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to update machine {machine_id} timezone to {new_timezone}")
            return False
        return True

    async def set_machine_real_cabinet(self, machine_id: int, is_real: bool = False) -> bool:
        sql = machine.update(machine.c.id == machine_id).values(is_cab = is_real)
        
        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to update machine {machine_id} is_cab to {is_real}")
            return False
        return True

    async def set_machine_can_ota(self, machine_id: int, can_ota: bool = False) -> bool:
        sql = machine.update(machine.c.id == machine_id).values(ota_enable = can_ota)
        
        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to update machine {machine_id} ota_enable to {can_ota}")
            return False
        return True

    async def set_machine_memo(self, machine_id: int, new_memo: Optional[str]) -> bool:
        sql = machine.update(machine.c.id == machine_id).values(memo = new_memo)
        
        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to update machine {machine_id} memo")
            return False
        return True

    async def get_arcade(self, id: int) -> Optional[Row]:
        sql = arcade.select(arcade.c.id == id)
        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()
    
    async def get_arcade_machines(self, id: int) -> Optional[List[Row]]:
        sql = machine.select(machine.c.arcade == id)
        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def create_arcade(
        self,
        name: Optional[str] = None,
        nickname: Optional[str] = None,
        country: str = "JPN",
        country_id: int = 1,
        state: str = "",
        city: str = "",
        region_id: int = 1,
    ) -> Optional[int]:
        if nickname is None:
            nickname = name

        sql = arcade.insert().values(
            name=name,
            nickname=nickname,
            country=country,
            country_id=country_id,
            state=state,
            city=city,
            region_id=region_id,
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.lastrowid

    async def get_arcades_managed_by_user(self, user_id: int) -> Optional[List[Row]]:
        sql = select(arcade).join(arcade_owner, arcade_owner.c.arcade == arcade.c.id).where(arcade_owner.c.user == user_id)
        result = await self.execute(sql)
        if result is None:
            return False
        return result.fetchall()
    
    async def get_manager_permissions(self, user_id: int, arcade_id: int) -> Optional[int]:
        sql = select(arcade_owner.c.permissions).where(and_(arcade_owner.c.user == user_id, arcade_owner.c.arcade == arcade_id))
        result = await self.execute(sql)
        if result is None:
            return None
        row =  result.fetchone()
        if row:
            return row['permissions']
        return None

    async def get_arcade_owners(self, arcade_id: int) -> Optional[Row]:
        sql = select(arcade_owner).where(arcade_owner.c.arcade == arcade_id)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def add_arcade_owner(self, arcade_id: int, user_id: int, permissions: int = 1) -> Optional[int]:
        sql = insert(arcade_owner).values(arcade=arcade_id, user=user_id, permissions=permissions)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.lastrowid

    async def set_arcade_owner_permissions(self, arcade_id: int, user_id: int, new_permissions: int = 1) -> bool:
        sql = arcade_owner.update(
            and_(arcade_owner.c.arcade == arcade_id, arcade_owner.c.user == user_id)
        ).values(permissions = new_permissions)

        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to update arcade owner permissions to {new_permissions} for user {user_id} arcade {arcade_id}")
            return False
        return True

    async def get_arcade_by_name(self, name: str) -> Optional[List[Row]]:
        sql = arcade.select(or_(arcade.c.name.like(f"%{name}%"), arcade.c.nickname.like(f"%{name}%")))
        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_arcades_by_ip(self, ip: str) -> Optional[List[Row]]:
        sql = arcade.select().where(arcade.c.ip == ip)
        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def set_arcade_name_nickname(self, arcade_id: int, new_name: Optional[str], new_nickname: Optional[str]) -> bool:
        sql = arcade.update(arcade.c.id == arcade_id).values(name = new_name, nickname = new_nickname)
        
        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to update arcade {arcade_id} name to {new_name}/{new_nickname}")
            return False
        return True

    async def set_arcade_region_info(self, arcade_id: int, new_country: Optional[str], new_state: Optional[str], new_city: Optional[str], new_region_id: Optional[int], new_country_id: Optional[int]) -> bool:
        sql = arcade.update(arcade.c.id == arcade_id).values(
            country = new_country,
            state = new_state,
            city = new_city,
            region_id = new_region_id,
            country_id = new_country_id
        )
        
        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to update arcade {arcade_id} regional info to {new_country}/{new_state}/{new_city}/{new_region_id}/{new_country_id}")
            return False
        return True

    async def set_arcade_timezone(self, arcade_id: int, new_timezone: Optional[str]) -> bool:
        sql = arcade.update(arcade.c.id == arcade_id).values(timezone = new_timezone)
        
        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to update arcade {arcade_id} timezone to {new_timezone}")
            return False
        return True

    async def set_arcade_vpn_ip(self, arcade_id: int, new_ip: Optional[str]) -> bool:
        sql = arcade.update(arcade.c.id == arcade_id).values(ip = new_ip)

        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to update arcade {arcade_id} VPN address to {new_ip}")
            return False
        return True

    async def get_num_generated_keychips(self) -> Optional[int]:
        result = await self.execute(select(func.count("serial LIKE 'A69A%'")).select_from(machine))
        if result:
            return result.fetchone()['count_1']
        self.logger.error("Failed to count machine serials that start with A69A!")

    def format_serial(
        self, platform_code: str, platform_rev: int, serial_letter: str, serial_num: int, append: int, dash: bool = False
    ) -> str:
        return f"{platform_code}{'-' if dash else ''}{platform_rev:02d}{serial_letter}{serial_num:04d}{append:04d}"

    def validate_keychip_format(self, serial: str) -> bool:
        # For the 2nd letter, E and X are the only "real" values that have been observed (A is used for generated keychips)
        if re.fullmatch(r"^A[0-9]{2}[A-Z][-]?[0-9]{2}[A-HJ-NP-Z][0-9]{4}([0-9]{4})?$", serial) is None:
            return False
        
        return True
    
    # Thanks bottersnike!
    def get_keychip_suffix(self, year: int, month: int) -> str:
        assert year > 1957
        assert 1 <= month <= 12

        year -= 1957
        # Jan/Feb/Mar are from the previous tax year
        if month < 4:
            year -= 1
        assert year >= 1 and year <= 99

        month = ((month - 1) + 9) % 12  # Offset so April=0
        return f"{year:02}{month // 6:01}{month % 6 + 1:01}"


    def parse_keychip_suffix(self, suffix: str) -> tuple[int, int]:
        year = int(suffix[0:2])
        half = int(suffix[2])
        assert half in (0, 1)
        period = int(suffix[3])
        assert period in (1, 2, 3, 4, 5, 6)

        month = half * 6 + (period - 1)
        month = ((month + 3) % 12) + 1  # Offset so Jan=1

        # Jan/Feb/Mar are from the previous tax year
        if month < 4:
            year += 1
        year += 1957

        return (year, month)
