from configparser import Interpolation
from typing import Dict, List, Optional

from sqlalchemy import Column, Table, UniqueConstraint, and_, text
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.engine import Row
from sqlalchemy.schema import ForeignKey
from sqlalchemy.sql import func, select, update
from sqlalchemy.types import JSON, BigInteger, Boolean, Integer, String, TIMESTAMP

from core.data.schema import BaseData, metadata

best_score: Table = Table(
    "mai2_score_best",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("musicId", Integer),
    Column("level", Integer),
    Column("playCount", Integer),
    Column("achievement", Integer),
    Column("comboStatus", Integer),
    Column("syncStatus", Integer),
    Column("deluxscoreMax", Integer),
    Column("scoreRank", Integer),
    Column("extNum1", Integer, server_default="0"),
    UniqueConstraint("user", "musicId", "level", name="mai2_score_best_uk"),
    mysql_charset="utf8mb4",
)

playlog = Table(
    "mai2_playlog",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("userId", BigInteger),
    Column("orderId", Integer),
    Column("playlogId", BigInteger),
    Column("version", Integer),
    Column("placeId", Integer),
    Column("placeName", String(255)),
    Column("loginDate", BigInteger),
    Column("playDate", String(255)),
    Column("userPlayDate", String(255)),
    Column("type", Integer),
    Column("musicId", Integer),
    Column("level", Integer),
    Column("trackNo", Integer),
    Column("vsMode", Integer),
    Column("vsUserName", String(255)),
    Column("vsStatus", Integer),
    Column("vsUserRating", Integer),
    Column("vsUserAchievement", Integer),
    Column("vsUserGradeRank", Integer),
    Column("vsRank", Integer),
    Column("playerNum", Integer),
    Column("playedUserId1", BigInteger),
    Column("playedUserName1", String(255)),
    Column("playedMusicLevel1", Integer),
    Column("playedUserId2", BigInteger),
    Column("playedUserName2", String(255)),
    Column("playedMusicLevel2", Integer),
    Column("playedUserId3", BigInteger),
    Column("playedUserName3", String(255)),
    Column("playedMusicLevel3", Integer),
    Column("characterId1", Integer),
    Column("characterLevel1", Integer),
    Column("characterAwakening1", Integer),
    Column("characterId2", Integer),
    Column("characterLevel2", Integer),
    Column("characterAwakening2", Integer),
    Column("characterId3", Integer),
    Column("characterLevel3", Integer),
    Column("characterAwakening3", Integer),
    Column("characterId4", Integer),
    Column("characterLevel4", Integer),
    Column("characterAwakening4", Integer),
    Column("characterId5", Integer),
    Column("characterLevel5", Integer),
    Column("characterAwakening5", Integer),
    Column("achievement", Integer),
    Column("deluxscore", Integer),
    Column("scoreRank", Integer),
    Column("maxCombo", Integer),
    Column("totalCombo", Integer),
    Column("maxSync", Integer),
    Column("totalSync", Integer),
    Column("tapCriticalPerfect", Integer),
    Column("tapPerfect", Integer),
    Column("tapGreat", Integer),
    Column("tapGood", Integer),
    Column("tapMiss", Integer),
    Column("holdCriticalPerfect", Integer),
    Column("holdPerfect", Integer),
    Column("holdGreat", Integer),
    Column("holdGood", Integer),
    Column("holdMiss", Integer),
    Column("slideCriticalPerfect", Integer),
    Column("slidePerfect", Integer),
    Column("slideGreat", Integer),
    Column("slideGood", Integer),
    Column("slideMiss", Integer),
    Column("touchCriticalPerfect", Integer),
    Column("touchPerfect", Integer),
    Column("touchGreat", Integer),
    Column("touchGood", Integer),
    Column("touchMiss", Integer),
    Column("breakCriticalPerfect", Integer),
    Column("breakPerfect", Integer),
    Column("breakGreat", Integer),
    Column("breakGood", Integer),
    Column("breakMiss", Integer),
    Column("isTap", Boolean),
    Column("isHold", Boolean),
    Column("isSlide", Boolean),
    Column("isTouch", Boolean),
    Column("isBreak", Boolean),
    Column("isCriticalDisp", Boolean),
    Column("isFastLateDisp", Boolean),
    Column("fastCount", Integer),
    Column("lateCount", Integer),
    Column("isAchieveNewRecord", Boolean),
    Column("isDeluxscoreNewRecord", Boolean),
    Column("comboStatus", Integer),
    Column("syncStatus", Integer),
    Column("isClear", Boolean),
    Column("beforeRating", Integer),
    Column("afterRating", Integer),
    Column("beforeGrade", Integer),
    Column("afterGrade", Integer),
    Column("afterGradeRank", Integer),
    Column("beforeDeluxRating", Integer),
    Column("afterDeluxRating", Integer),
    Column("isPlayTutorial", Boolean),
    Column("isEventMode", Boolean),
    Column("isFreedomMode", Boolean),
    Column("playMode", Integer),
    Column("isNewFree", Boolean),
    Column("extNum1", Integer),
    Column("extNum2", Integer),
    Column("extNum4", Integer),
    Column("extBool1", Boolean), # new with buddies
    Column("extBool2", Boolean), # new with prism
    Column("extBool3", Boolean), # new with prism+
    Column("trialPlayAchievement", Integer),
    mysql_charset="utf8mb4",
)

# new with buddies
playlog_2p = Table(
    "mai2_playlog_2p",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    # TODO: ForeignKey to aime_user?
    Column("userId1", Integer),
    Column("userId2", Integer),
    # TODO: ForeignKey to mai2_profile_detail?
    Column("userName1", String(25)),
    Column("userName2", String(25)),
    Column("regionId", Integer),
    Column("placeId", Integer),
    Column("user2pPlaylogDetailList", JSON),
    mysql_charset="utf8mb4",
)

kaleidxscope = Table(
    "mai2_score_kaleidxscope",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("gateId", Integer),
    Column("isGateFound", Boolean),
    Column("isKeyFound", Boolean),
    Column("isClear", Boolean),
    Column("totalRestLife", Integer),
    Column("totalAchievement", Integer),
    Column("totalDeluxscore", Integer),
    Column("bestAchievement", Integer),
    Column("bestDeluxscore", Integer),
    Column("bestAchievementDate", String(25)),
    Column("bestDeluxscoreDate", String(25)),
    Column("playCount", Integer),
    Column("clearDate", String(25)),
    Column("lastPlayDate", String(25)),
    Column("isInfoWatched", Boolean),
    UniqueConstraint("user", "gateId", name="mai2_score_best_uk"),
    mysql_charset="utf8mb4"
)

course = Table(
    "mai2_score_course",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("courseId", Integer),
    Column("isLastClear", Boolean),
    Column("totalRestlife", Integer),
    Column("totalAchievement", Integer),
    Column("totalDeluxscore", Integer),
    Column("playCount", Integer),
    Column("clearDate", String(25)),
    Column("lastPlayDate", String(25)),
    Column("bestAchievement", Integer),
    Column("bestAchievementDate", String(25)),
    Column("bestDeluxscore", Integer),
    Column("bestDeluxscoreDate", String(25)),
    UniqueConstraint("user", "courseId", name="mai2_score_best_uk"),
    mysql_charset="utf8mb4",
)

playlog_old = Table(
    "maimai_playlog",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("version", Integer),
    # Pop access code
    Column("orderId", Integer),
    Column("sortNumber", Integer),
    Column("placeId", Integer),
    Column("placeName", String(255)),
    Column("country", String(255)),
    Column("regionId", Integer),
    Column("playDate", String(255)),
    Column("userPlayDate", String(255)),
    Column("musicId", Integer),
    Column("level", Integer),
    Column("gameMode", Integer),
    Column("rivalNum", Integer),
    Column("track", Integer),
    Column("eventId", Integer),
    Column("isFreeToPlay", Boolean),
    Column("playerRating", Integer),
    Column("playedUserId1", Integer),
    Column("playedUserId2", Integer),
    Column("playedUserId3", Integer),
    Column("playedUserName1", String(255)),
    Column("playedUserName2", String(255)),
    Column("playedUserName3", String(255)),
    Column("playedMusicLevel1", Integer),
    Column("playedMusicLevel2", Integer),
    Column("playedMusicLevel3", Integer),
    Column("achievement", Integer),
    Column("score", Integer),
    Column("tapScore", Integer),
    Column("holdScore", Integer),
    Column("slideScore", Integer),
    Column("breakScore", Integer),
    Column("syncRate", Integer),
    Column("vsWin", Integer),
    Column("isAllPerfect", Boolean),
    Column("fullCombo", Integer),
    Column("maxFever", Integer),
    Column("maxCombo", Integer),
    Column("tapPerfect", Integer),
    Column("tapGreat", Integer),
    Column("tapGood", Integer),
    Column("tapBad", Integer),
    Column("holdPerfect", Integer),
    Column("holdGreat", Integer),
    Column("holdGood", Integer),
    Column("holdBad", Integer),
    Column("slidePerfect", Integer),
    Column("slideGreat", Integer),
    Column("slideGood", Integer),
    Column("slideBad", Integer),
    Column("breakPerfect", Integer),
    Column("breakGreat", Integer),
    Column("breakGood", Integer),
    Column("breakBad", Integer),
    Column("judgeStyle", Integer),
    Column("isTrackSkip", Boolean),
    Column("isHighScore", Boolean),
    Column("isChallengeTrack", Boolean),
    Column("challengeLife", Integer),
    Column("challengeRemain", Integer),
    Column("isAllPerfectPlus", Integer),
    mysql_charset="utf8mb4",
)

best_score_old: Table = Table(
    "maimai_score_best",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("musicId", Integer),
    Column("level", Integer),
    Column("playCount", Integer),
    Column("achievement", Integer),
    Column("scoreMax", Integer),
    Column("syncRateMax", Integer),
    Column("isAllPerfect", Boolean),
    Column("isAllPerfectPlus", Integer),
    Column("fullCombo", Integer),
    Column("maxFever", Integer),
    UniqueConstraint("user", "musicId", "level", name="maimai_score_best_uk"),
    mysql_charset="utf8mb4",
)

tournament_ranking = Table(
    "mai2_score_tournament_ranking",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("tournamentId", Integer, nullable=False),
    Column("userId", Integer, nullable=False),
    Column("totalScore", Integer, nullable=False),
    Column("deluxScore", Integer, nullable=False),
    Column("rankingDate", TIMESTAMP, server_default=func.now(), nullable=False),
    mysql_charset="utf8mb4",
)

class Mai2ScoreData(BaseData):
    async def get_tournament_score(self, user_id: int, tournament_id: int) -> Optional[List[all]]:
        sql = tournament_ranking.select(
            and_(
                tournament_ranking.c.tournamentId == tournament_id,
                tournament_ranking.c.userId == user_id,
            )
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def put_tournament_score(self, user_id: int, tournament_id: int, total_score: int, delux_score: int) -> Optional[int]:
        user_ranking = await self.get_tournament_score(user_id, tournament_id)
        if user_ranking is None:
            sql = insert(tournament_ranking).values(
                tournamentId = tournament_id,
                userId = user_id,
                totalScore = total_score,
                deluxScore = delux_score,
                rankingDate = func.now()
            )

            result = await self.execute(sql)
            if result is None:
                self.logger.error(
                    f"put score_ranking fail, userId:{user_id}"
                )
                return None

            return result.lastrowid
        else:
            for score in user_ranking:
                score._asdict()
                if score['totalScore'] >= total_score:
                    self.logger.info(f"is not the best score, userId:{user_id}")
                    return None
                else:
                    sql = update(tournament_ranking).values(
                        tournamentId=tournament_id,
                        userId=user_id,
                        totalScore=total_score,
                        deluxScore=delux_score,
                        rankingDate=func.now()
                    )
                    result = await self.execute(sql)
                    if result is None:
                        self.logger.error(f"put score_ranking fail, userId:{user_id}")
                        return None

                    return result.lastrowid

    async def get_user_score_ranking(self, userId: int, tournamentId: int):
        sql = text("""
                   SELECT *,
                          RANK() OVER (
                              ORDER BY totalScore DESC, deluxScore DESC, rankingDate ASC
                              ) AS ranking
                   FROM mai2_score_tournament_ranking
                   WHERE tournamentId = :tournamentId
                   """)

        result = await self.execute(sql, {"tournamentId": tournamentId})
        rows = result.fetchall() if result else []

        for row in rows:
            if row['userId'] == userId:
                return {
                "tournamentId": row["tournamentId"],
                "totalScore": row["totalScore"],
                "ranking": row["ranking"],
                "rankingDate": row["rankingDate"].strftime("%Y-%m-%d %H:%M:%S")
            }
            else:
                return None

        return None

    async def put_best_score(self, user_id: int, score_data: Dict, is_dx: bool = True) -> Optional[int]:
        score_data["user"] = user_id

        if is_dx:
            sql = insert(best_score).values(**score_data)
        else:
            sql = insert(best_score_old).values(**score_data)
        conflict = sql.on_duplicate_key_update(**score_data)

        result = await self.execute(conflict)
        if result is None:
            self.logger.error(
                f"put_best_score:  Failed to insert best score! user_id {user_id} is_dx {is_dx}"
            )
            return None
        return result.lastrowid

    async def get_best_scores(
        self,
        user_id: int,
        song_id: Optional[int] = None,
        is_dx: bool = True,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        levels: Optional[list[int]] = None,
    ) -> Optional[List[Row]]:
        if is_dx:
            table = best_score
        else:
            table = best_score_old

        cond = table.c.user == user_id

        if song_id is not None:
            cond &= table.c.musicId == song_id
        
        if levels is not None:
            cond &= table.c.level.in_(levels)
        
        if limit is None and offset is None:
            sql = (
                select(table)
                .where(cond)
                .order_by(table.c.musicId, table.c.level)
            )
        else:
            subq = (
                select(table.c.musicId)
                .distinct()
                .where(cond)
                .order_by(table.c.musicId)
            )

            if limit is not None:
                subq = subq.limit(limit)
            if offset is not None:
                subq = subq.offset(offset)
            
            subq = subq.subquery()

            sql = (
                select(table)
                .join(subq, table.c.musicId == subq.c.musicId)
                .where(cond)
                .order_by(table.c.musicId, table.c.level)
            )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_best_score(
        self, user_id: int, song_id: int, chart_id: int
    ) -> Optional[Row]:
        sql = best_score.select(
            and_(
                best_score.c.user == user_id,
                best_score.c.song_id == song_id,
                best_score.c.chart_id == chart_id,
            )
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()

    async def put_playlog(self, user_id: int, playlog_data: Dict, is_dx: bool = True) -> Optional[int]:
        playlog_data["user"] = user_id

        if is_dx:
            sql = insert(playlog).values(**playlog_data)
        else:
            sql = insert(playlog_old).values(**playlog_data)

        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"put_playlog:  Failed to insert! user_id {user_id} is_dx {is_dx}")
            return None
        return result.lastrowid
    
    async def put_playlog_2p(self, user_id: int, playlog_2p_data: Dict) -> Optional[int]:
        playlog_2p_data["user"] = user_id
        sql = insert(playlog_2p).values(**playlog_2p_data)

        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"put_playlog_2p:  Failed to insert! user_id {user_id}")
            return None
        return result.lastrowid

    async def put_course(self, user_id: int, course_data: Dict) -> Optional[int]:
        course_data["user"] = user_id
        sql = insert(course).values(**course_data)

        conflict = sql.on_duplicate_key_update(**course_data)

        result = await self.execute(conflict)
        if result is None:
            self.logger.error(f"put_course:  Failed to insert! user_id {user_id}")
            return None
        return result.lastrowid

    async def get_courses(self, user_id: int) -> Optional[List[Row]]:
        sql = course.select(course.c.user == user_id)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_playlogs(self, user_id: int, idx: int = 0, limit: int = 0) -> Optional[List[Row]]:
        if user_id is not None:
            sql = playlog.select(playlog.c.user == user_id)
        else:
            sql = playlog.select()
            
        if limit:
            sql = sql.limit(limit)
            if idx:
                sql = sql.offset(idx * limit)
        
        result = await self.execute(sql)
        if result:
            return result.fetchall()

    async def get_user_playlogs_count(self, aime_id: int) -> Optional[Row]:
        sql = select(func.count()).where(playlog.c.user == aime_id)
        result = await self.execute(sql)
        if result is None:
            self.logger.warning(f"aime_id {aime_id} has no playlog ")
            return None
        return result.scalar()

    async def get_user_kaleidxscope_list(self, user_id: int) -> Optional[List[Row]]:
        sql = kaleidxscope.select(kaleidxscope.c.user == user_id)
        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def put_user_kaleidxscope(self, user_id: int, user_kaleidxscope_data: Dict) -> Optional[int]:
        user_kaleidxscope_data["user"] = user_id
        sql = insert(kaleidxscope).values(**user_kaleidxscope_data)

        conflict = sql.on_duplicate_key_update(**user_kaleidxscope_data)

        result = await self.execute(conflict)
        if result is None:
            self.logger.error(f"put_user_kaleidxscope:  Failed to insert! user_id {user_id}")
            return None
        return result.lastrowid