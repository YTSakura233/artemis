from typing import Dict, List, Optional

from sqlalchemy import Column, Table, UniqueConstraint
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.engine import Row
from sqlalchemy.schema import ForeignKey
from sqlalchemy.sql import select, func
from sqlalchemy.types import TIMESTAMP, Boolean, Float, Integer, String

from core.data.schema import BaseData, metadata

from datetime import datetime, timedelta

score_best: Table = Table(
    "ongeki_score_best",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("musicId", Integer, nullable=False),
    Column("level", Integer, nullable=False),
    Column("playCount", Integer, nullable=False),
    Column("techScoreMax", Integer, nullable=False),
    Column("techScoreRank", Integer, nullable=False),
    Column("battleScoreMax", Integer, nullable=False),
    Column("battleScoreRank", Integer, nullable=False),
    Column("maxComboCount", Integer, nullable=False),
    Column("maxOverKill", Float, nullable=False),
    Column("maxTeamOverKill", Float, nullable=False),
    Column("isFullBell", Boolean, nullable=False),
    Column("isFullCombo", Boolean, nullable=False),
    Column("isAllBreake", Boolean, nullable=False),
    Column("isLock", Boolean, nullable=False),
    Column("clearStatus", Integer, nullable=False),
    Column("isStoryWatched", Boolean, nullable=False),
    Column("platinumScoreMax", Integer),
    UniqueConstraint("user", "musicId", "level", name="ongeki_best_score_uk"),
    mysql_charset="utf8mb4",
)

playlog = Table(
    "ongeki_score_playlog",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("sortNumber", Integer),
    Column("placeId", Integer),
    Column("placeName", String(255)),
    Column("playDate", TIMESTAMP),
    Column("userPlayDate", TIMESTAMP),
    Column("musicId", Integer),
    Column("level", Integer),
    Column("playKind", Integer),
    Column("eventId", Integer),
    Column("eventName", String(255)),
    Column("eventPoint", Integer),
    Column("playedUserId1", Integer),
    Column("playedUserId2", Integer),
    Column("playedUserId3", Integer),
    Column("playedUserName1", String(8)),
    Column("playedUserName2", String(8)),
    Column("playedUserName3", String(8)),
    Column("playedMusicLevel1", Integer),
    Column("playedMusicLevel2", Integer),
    Column("playedMusicLevel3", Integer),
    Column("cardId1", Integer),
    Column("cardId2", Integer),
    Column("cardId3", Integer),
    Column("cardLevel1", Integer),
    Column("cardLevel2", Integer),
    Column("cardLevel3", Integer),
    Column("cardAttack1", Integer),
    Column("cardAttack2", Integer),
    Column("cardAttack3", Integer),
    Column("bossCharaId", Integer),
    Column("bossLevel", Integer),
    Column("bossAttribute", Integer),
    Column("clearStatus", Integer),
    Column("techScore", Integer),
    Column("techScoreRank", Integer),
    Column("battleScore", Integer),
    Column("battleScoreRank", Integer),
    Column("maxCombo", Integer),
    Column("judgeMiss", Integer),
    Column("judgeHit", Integer),
    Column("judgeBreak", Integer),
    Column("judgeCriticalBreak", Integer),
    Column("rateTap", Integer),
    Column("rateHold", Integer),
    Column("rateFlick", Integer),
    Column("rateSideTap", Integer),
    Column("rateSideHold", Integer),
    Column("bellCount", Integer),
    Column("totalBellCount", Integer),
    Column("damageCount", Integer),
    Column("overDamage", Integer),
    Column("isTechNewRecord", Boolean),
    Column("isBattleNewRecord", Boolean),
    Column("isOverDamageNewRecord", Boolean),
    Column("isFullCombo", Boolean),
    Column("isFullBell", Boolean),
    Column("isAllBreak", Boolean),
    Column("playerRating", Integer),
    Column("battlePoint", Integer),
    Column("platinumScore", Integer),
    Column("platinumScoreMax", Integer),
    mysql_charset="utf8mb4",
)

tech_count = Table(
    "ongeki_score_tech_count",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("levelId", Integer, nullable=False),
    Column("allBreakCount", Integer),
    Column("allBreakPlusCount", Integer),
    UniqueConstraint("user", "levelId", name="ongeki_tech_count_uk"),
    mysql_charset="utf8mb4",
)


class OngekiScoreData(BaseData):
    async def get_tech_count(self, aime_id: int) -> Optional[List[Dict]]:
        sql = select(tech_count).where(tech_count.c.user == aime_id)
        
        result = await self.execute(sql)
        
        if result is None:
            return None
        return result.fetchall()

    async def put_tech_count(self, aime_id: int, tech_count_data: Dict) -> Optional[int]:
        tech_count_data["user"] = aime_id

        sql = insert(tech_count).values(**tech_count_data)
        conflict = sql.on_duplicate_key_update(**tech_count_data)
        result = await self.execute(conflict)

        if result is None:
            self.logger.warning(f"put_tech_count: Failed to update! aime_id: {aime_id}")
            return None
        return result.lastrowid

    async def get_best_scores(
        self,
        aime_id: int,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Optional[List[Row]]:
        cond = score_best.c.user == aime_id

        if limit is None and offset is None:
            sql = (
                select(score_best)
                .where(cond)
                .order_by(score_best.c.musicId, score_best.c.level)
            )
        else:
            subq = (
                select(score_best.c.musicId)
                .distinct()
                .where(cond)
                .order_by(score_best.c.musicId)
            )

            if limit is not None:
                subq = subq.limit(limit)
            if offset is not None:
                subq = subq.offset(offset)
            
            subq = subq.subquery()

            sql = (
                select(score_best)
                .join(subq, score_best.c.musicId == subq.c.musicId)
                .where(cond)
                .order_by(score_best.c.musicId, score_best.c.level)
            )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_best_score(
        self, aime_id: int, song_id: int, chart_id: int = None
    ) -> Optional[List[Dict]]:
        return []

    async def put_best_score(self, aime_id: int, music_detail: Dict) -> Optional[int]:
        music_detail["user"] = aime_id

        sql = insert(score_best).values(**music_detail)
        conflict = sql.on_duplicate_key_update(**music_detail)
        result = await self.execute(conflict)

        if result is None:
            self.logger.warning(f"put_best_score: Failed to add score! aime_id: {aime_id}")
            return None
        return result.lastrowid

    async def get_rankings(self, date: datetime) -> Optional[List[Row]]:
        sql = (
            select([func.count(playlog.c.id), playlog.c.musicId])
                .where(playlog.c.playDate == date.date())
                .group_by(playlog.c.musicId)
                .order_by(func.count(playlog.c.id).desc())
                .limit(10)
        )
        result = await self.execute(sql)
        if result:
            return result.fetchall()

    async def put_playlog(self, aime_id: int, playlog_data: Dict) -> Optional[int]:
        playlog_data["user"] = aime_id

        sql = insert(playlog).values(**playlog_data)

        result = await self.execute(sql)
        if result is None:
            self.logger.warning(f"put_playlog: Failed to add playlog! aime_id: {aime_id}")
            return None
        return result.lastrowid
