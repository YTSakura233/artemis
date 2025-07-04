from core.data.schema.base import BaseData, metadata

from typing import Optional, Dict, List
from sqlalchemy import Table, Column, UniqueConstraint, PrimaryKeyConstraint, and_
from sqlalchemy.types import Integer, String, TIMESTAMP, Boolean, JSON, Float
from sqlalchemy.schema import ForeignKey
from sqlalchemy.sql import func, select
from sqlalchemy.engine import Row
from sqlalchemy.dialects.mysql import insert
from datetime import datetime

event = Table(
    "mai2_static_event",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer, nullable=False),
    Column("eventId", Integer),
    Column("type", Integer),
    Column("name", String(255)),
    Column("startDate", TIMESTAMP, server_default=func.now()),
    Column("enabled", Boolean, server_default="1"),
    UniqueConstraint("version", "eventId", "type", name="mai2_static_event_uk"),
    mysql_charset="utf8mb4",
)

music = Table(
    "mai2_static_music",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer, nullable=False),
    Column("songId", Integer),
    Column("chartId", Integer),
    Column("title", String(255)),
    Column("artist", String(255)),
    Column("genre", String(255)),
    Column("bpm", Integer),
    Column("addedVersion", String(255)),
    Column("difficulty", Float),
    Column("noteDesigner", String(255)),
    UniqueConstraint("songId", "chartId", "version", name="mai2_static_music_uk"),
    mysql_charset="utf8mb4",
)

ticket = Table(
    "mai2_static_ticket",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer, nullable=False),
    Column("ticketId", Integer),
    Column("kind", Integer),
    Column("name", String(255)),
    Column("price", Integer, server_default="1"),
    Column("enabled", Boolean, server_default="1"),
    UniqueConstraint("version", "ticketId", name="mai2_static_ticket_uk"),
    mysql_charset="utf8mb4",
)

cards = Table(
    "mai2_static_cards",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer, nullable=False),
    Column("cardId", Integer, nullable=False),
    Column("cardName", String(255), nullable=False),
    Column("startDate", TIMESTAMP, server_default="2018-01-01 00:00:00.0"),
    Column("endDate", TIMESTAMP, server_default="2038-01-01 00:00:00.0"),
    Column("noticeStartDate", TIMESTAMP, server_default="2018-01-01 00:00:00.0"),
    Column("noticeEndDate", TIMESTAMP, server_default="2038-01-01 00:00:00.0"),
    Column("enabled", Boolean, server_default="1"),
    UniqueConstraint("version", "cardId", "cardName", name="mai2_static_cards_uk"),
    mysql_charset="utf8mb4",
)

tournament = Table(
    "mai2_static_tournament",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("tournamentId", Integer, nullable=False),
    Column("tournamentName", String(255), nullable=False),
    Column("rankingKind", Integer, nullable=False),
    Column("scoreType", Integer, nullable=False),
    Column("noticeStartDate", TIMESTAMP, server_default="2038-01-01 00:00:00.0"),
    Column("noticeEndDate", TIMESTAMP, server_default="2038-01-01 00:00:00.0"),
    Column("startDate", TIMESTAMP, server_default="2038-01-01 00:00:00.0"),
    Column("endDate", TIMESTAMP, server_default="2038-01-01 00:00:00.0"),
    Column("entryStartDate", TIMESTAMP, server_default="2038-01-01 00:00:00.0"),
    Column("entryEndDate", TIMESTAMP, server_default="2038-01-01 00:00:00.0"),
    Column("gameTournamentMusicList", JSON, nullable=False),
    mysql_charset="utf8mb4",
)


class Mai2StaticData(BaseData):
    async def get_game_tournament(self):
        sql = select(tournament)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def put_game_event(
        self, version: int, type: int, event_id: int, name: str
    ) -> Optional[int]:
        sql = insert(event).values(
            version=version,
            type=type,
            eventId=event_id,
            name=name,
        )

        conflict = sql.on_duplicate_key_update(eventId=event_id)

        result = await self.execute(conflict)
        if result is None:
            self.logger.warning(
                f"put_game_event: Failed to insert event! event_id {event_id} type {type} name {name}"
            )
        return result.lastrowid

    async def get_game_events(self, version: int) -> Optional[List[Row]]:
        sql = event.select(event.c.version == version)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_enabled_events(self, version: int) -> Optional[List[Row]]:
        sql = select(event).where(
            and_(event.c.version == version, event.c.enabled == True)
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def toggle_game_event(
        self, version: int, event_id: int, toggle: bool
    ) -> Optional[List]:
        sql = event.update(
            and_(event.c.version == version, event.c.eventId == event_id)
        ).values(enabled=int(toggle))

        result = await self.execute(sql)
        if result is None:
            self.logger.warning(
                f"toggle_game_event: Failed to update event! event_id {event_id} toggle {toggle}"
            )
        return result.last_updated_params()

    async def put_game_music(
        self,
        version: int,
        song_id: int,
        chart_id: int,
        title: str,
        artist: str,
        genre: str,
        bpm: str,
        added_version: str,
        difficulty: float,
        note_designer: str,
    ) -> None:
        sql = insert(music).values(
            version=version,
            songId=song_id,
            chartId=chart_id,
            title=title,
            artist=artist,
            genre=genre,
            bpm=bpm,
            addedVersion=added_version,
            difficulty=difficulty,
            noteDesigner=note_designer,
        )

        conflict = sql.on_duplicate_key_update(
            title=title,
            artist=artist,
            genre=genre,
            bpm=bpm,
            addedVersion=added_version,
            difficulty=difficulty,
            noteDesigner=note_designer,
        )

        result = await self.execute(conflict)
        if result is None:
            self.logger.warning(f"Failed to insert song {song_id} chart {chart_id}")
            return None
        return result.lastrowid

    async def put_game_ticket(
        self,
        version: int,
        ticket_id: int,
        ticket_type: int,
        ticket_price: int,
        name: str,
    ) -> Optional[int]:
        sql = insert(ticket).values(
            version=version,
            ticketId=ticket_id,
            kind=ticket_type,
            price=ticket_price,
            name=name,
        )

        conflict = sql.on_duplicate_key_update(price=ticket_price)

        conflict = sql.on_duplicate_key_update(price=ticket_price)

        result = await self.execute(conflict)
        if result is None:
            self.logger.warning(f"Failed to insert charge {ticket_id} type {ticket_type}")
            return None
        return result.lastrowid

    async def get_enabled_tickets(
        self, version: int, kind: int = None
    ) -> Optional[List[Row]]:
        if kind is not None:
            sql = select(ticket).where(
                and_(
                    ticket.c.version == version,
                    ticket.c.enabled == True,
                    ticket.c.kind == kind,
                )
            )
        else:
            sql = select(ticket).where(
                and_(ticket.c.version == version, ticket.c.enabled == True)
            )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_music_chart(
        self, version: int, song_id: int, chart_id: int
    ) -> Optional[List[Row]]:
        sql = select(music).where(
            and_(
                music.c.version == version,
                music.c.songId == song_id,
                music.c.chartId == chart_id,
            )
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()

    async def put_card(self, version: int, card_id: int, card_name: str, **card_data) -> int:
        sql = insert(cards).values(
            version=version, cardId=card_id, cardName=card_name, **card_data
        )

        conflict = sql.on_duplicate_key_update(**card_data)

        result = await self.execute(conflict)
        if result is None:
            self.logger.warning(f"Failed to insert card {card_id}")
            return None
        return result.lastrowid

    async def get_enabled_cards(self, version: int) -> Optional[List[Row]]:
        sql = cards.select(and_(cards.c.version == version, cards.c.enabled == True))

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_event_by_id(self, table_id: int) -> Optional[Row]:
        result = await self.execute(event.select(event.c.id == table_id))
        if result:
            return result.fetchone()

    async def get_events_by_event_id(self, event_id: int) -> Optional[List[Row]]:
        result = await self.execute(event.select(event.c.eventId == event_id))
        if result:
            return result.fetchall()

    async def update_event_by_id(self, table_id: int, is_enable: bool, start_date: datetime) -> None:
        result = await self.execute(event.update(event.c.id == table_id).values(enabled=is_enable, startDate = start_date))
        if not result:
            self.logger.error(f"Failed to update event {table_id} - {is_enable} {start_date}")
