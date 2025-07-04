import json
from typing import Dict, List, Optional
from sqlalchemy import Table, Column, UniqueConstraint, and_
from sqlalchemy.types import Integer, String, Boolean, JSON, BigInteger
from sqlalchemy.schema import ForeignKey
from sqlalchemy.engine import Row
from sqlalchemy.sql import select, delete
from sqlalchemy.dialects.mysql import insert

from core.data.schema import BaseData, metadata

profile = Table(
    "chuni_profile_data",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("version", Integer, nullable=False),
    Column("exp", Integer),
    Column("level", Integer),
    Column("point", Integer),
    Column("frameId", Integer),
    Column("isMaimai", Boolean),
    Column("trophyId", Integer),
    Column("userName", String(25)),
    Column("isWebJoin", Boolean),
    Column("playCount", Integer),
    Column("lastGameId", String(25)),
    Column("totalPoint", BigInteger),
    Column("characterId", Integer),
    Column("firstGameId", String(25)),
    Column("friendCount", Integer),
    Column("lastPlaceId", Integer),
    Column("nameplateId", Integer),
    Column("totalMapNum", BigInteger),
    Column("lastAllNetId", Integer),
    Column("lastClientId", String(25)),
    Column("lastPlayDate", String(25)),
    Column("lastRegionId", Integer),
    Column("playerRating", Integer),
    Column("totalHiScore", BigInteger),
    Column("webLimitDate", String(25)),
    Column("firstPlayDate", String(25)),
    Column("highestRating", Integer),
    Column("lastPlaceName", String(25)),
    Column("multiWinCount", Integer),
    Column("acceptResCount", Integer),
    Column("lastRegionName", String(25)),
    Column("lastRomVersion", String(25)),
    Column("multiPlayCount", Integer),
    Column("firstRomVersion", String(25)),
    Column("lastDataVersion", String(25)),
    Column("requestResCount", Integer),
    Column("successResCount", Integer),
    Column("eventWatchedDate", String(25)),
    Column("firstDataVersion", String(25)),
    Column("reincarnationNum", Integer),
    Column("playedTutorialBit", Integer),
    Column("totalBasicHighScore", BigInteger),
    Column("totalExpertHighScore", BigInteger),
    Column("totalMasterHighScore", BigInteger),
    Column("totalRepertoireCount", BigInteger),
    Column("firstTutorialCancelNum", Integer),
    Column("totalAdvancedHighScore", BigInteger),
    Column("masterTutorialCancelNum", Integer),
    Column("ext1", Integer),  # Added in chunew
    Column("ext2", Integer),
    Column("ext3", Integer),
    Column("ext4", Integer),
    Column("ext5", Integer),
    Column("ext6", Integer),
    Column("ext7", Integer),
    Column("ext8", Integer),
    Column("ext9", Integer),
    Column("ext10", Integer),
    Column("extStr1", String(255)),
    Column("extStr2", String(255)),
    Column("extLong1", Integer),
    Column("extLong2", Integer),
    Column("mapIconId", Integer),
    Column("compatibleCmVersion", String(25)),
    Column("medal", Integer),
    Column("voiceId", Integer),
    Column(
        "teamId",
        Integer,
        ForeignKey("chuni_profile_team.id", ondelete="SET NULL", onupdate="SET NULL"),
    ),
    Column("eliteRankPoint", Integer, server_default="0"),
    Column("stockedGridCount", Integer, server_default="0"),
    Column("netBattleLoseCount", Integer, server_default="0"),
    Column("netBattleHostErrCnt", Integer, server_default="0"),
    Column("netBattle4thCount", Integer, server_default="0"),
    Column("overPowerRate", Integer, server_default="0"),
    Column("battleRewardStatus", Integer, server_default="0"),
    Column("netBattle1stCount", Integer, server_default="0"),
    Column("charaIllustId", Integer, server_default="0"),
    Column("userNameEx", String(8), server_default=""),
    Column("netBattleWinCount", Integer, server_default="0"),
    Column("netBattleCorrection", Integer, server_default="0"),
    Column("classEmblemMedal", Integer, server_default="0"),
    Column("overPowerPoint", Integer, server_default="0"),
    Column("netBattleErrCnt", Integer, server_default="0"),
    Column("battleRankId", Integer, server_default="0"),
    Column("netBattle3rdCount", Integer, server_default="0"),
    Column("netBattleConsecutiveWinCount", Integer, server_default="0"),
    Column("overPowerLowerRank", Integer, server_default="0"),
    Column("classEmblemBase", Integer, server_default="0"),
    Column("battleRankPoint", Integer, server_default="0"),
    Column("netBattle2ndCount", Integer, server_default="0"),
    Column("totalUltimaHighScore", BigInteger, server_default="0"),
    Column("skillId", Integer, server_default="0"),
    Column("lastCountryCode", String(5), server_default="JPN"),
    Column("isNetBattleHost", Boolean, server_default="0"),
    Column("battleRewardCount", Integer, server_default="0"),
    Column("battleRewardIndex", Integer, server_default="0"),
    Column("netBattlePlayCount", Integer, server_default="0"),
    Column("exMapLoopCount", Integer, server_default="0"),
    Column("netBattleEndState", Integer, server_default="0"),
    Column("rankUpChallengeResults", JSON),
    Column("avatarBack", Integer, server_default="0"),
    Column("avatarFace", Integer, server_default="0"),
    Column("avatarPoint", Integer, server_default="0"),
    Column("avatarItem", Integer, server_default="0"),
    Column("avatarWear", Integer, server_default="0"),
    Column("avatarFront", Integer, server_default="0"),
    Column("avatarSkin", Integer, server_default="0"),
    Column("avatarHead", Integer, server_default="0"),
    UniqueConstraint("user", "version", name="chuni_profile_profile_uk"),
    mysql_charset="utf8mb4",
)

profile_ex = Table(
    "chuni_profile_data_ex",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("version", Integer, nullable=False),
    Column("ext1", Integer),
    Column("ext2", Integer),
    Column("ext3", Integer),
    Column("ext4", Integer),
    Column("ext5", Integer),
    Column("ext6", Integer),
    Column("ext7", Integer),
    Column("ext8", Integer),
    Column("ext9", Integer),
    Column("ext10", Integer),
    Column("ext11", Integer),
    Column("ext12", Integer),
    Column("ext13", Integer),
    Column("ext14", Integer),
    Column("ext15", Integer),
    Column("ext16", Integer),
    Column("ext17", Integer),
    Column("ext18", Integer),
    Column("ext19", Integer),
    Column("ext20", Integer),
    Column("medal", Integer),
    Column("extStr1", String(255)),
    Column("extStr2", String(255)),
    Column("extStr3", String(255)),
    Column("extStr4", String(255)),
    Column("extStr5", String(255)),
    Column("voiceId", Integer),
    Column("extLong1", Integer),
    Column("extLong2", Integer),
    Column("extLong3", Integer),
    Column("extLong4", Integer),
    Column("extLong5", Integer),
    Column("mapIconId", Integer),
    Column("compatibleCmVersion", String(25)),
    UniqueConstraint("user", "version", name="chuni_profile_data_ex_uk"),
    mysql_charset="utf8mb4",
)

option = Table(
    "chuni_profile_option",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("speed", Integer),
    Column("bgInfo", Integer),
    Column("rating", Integer),
    Column("privacy", Integer),
    Column("judgePos", Integer),
    Column("matching", Integer),
    Column("guideLine", Integer),
    Column("headphone", Integer),
    Column("optionSet", Integer),
    Column("fieldColor", Integer),
    Column("guideSound", Integer),
    Column("successAir", Integer),
    Column("successTap", Integer),
    Column("judgeAttack", Integer),
    Column("playerLevel", Integer),
    Column("soundEffect", Integer),
    Column("judgeJustice", Integer),
    Column("successExTap", Integer),
    Column("successFlick", Integer),
    Column("successSkill", Integer),
    Column("successSlideHold", Integer),
    Column("successTapTimbre", Integer),
    Column("ext1", Integer),  # Added in chunew
    Column("ext2", Integer),
    Column("ext3", Integer),
    Column("ext4", Integer),
    Column("ext5", Integer),
    Column("ext6", Integer),
    Column("ext7", Integer),
    Column("ext8", Integer),
    Column("ext9", Integer),
    Column("ext10", Integer),
    Column("categoryDetail", Integer, server_default="0"),
    Column("judgeTimingOffset_120", Integer, server_default="0"),
    Column("resultVoiceShort", Integer, server_default="0"),
    Column("judgeAppendSe", Integer, server_default="0"),
    Column("judgeCritical", Integer, server_default="0"),
    Column("trackSkip", Integer, server_default="0"),
    Column("selectMusicFilterLv", Integer, server_default="0"),
    Column("sortMusicFilterLv", Integer, server_default="0"),
    Column("sortMusicGenre", Integer, server_default="0"),
    Column("speed_120", Integer, server_default="0"),
    Column("judgeTimingOffset", Integer, server_default="0"),
    Column("mirrorFumen", Integer, server_default="0"),
    Column("playTimingOffset_120", Integer, server_default="0"),
    Column("hardJudge", Integer, server_default="0"),
    Column("notesThickness", Integer, server_default="0"),
    Column("fieldWallPosition", Integer, server_default="0"),
    Column("playTimingOffset", Integer, server_default="0"),
    Column("fieldWallPosition_120", Integer, server_default="0"),
    UniqueConstraint("user", name="chuni_profile_option_uk"),
    mysql_charset="utf8mb4",
)

option_ex = Table(
    "chuni_profile_option_ex",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("ext1", Integer),
    Column("ext2", Integer),
    Column("ext3", Integer),
    Column("ext4", Integer),
    Column("ext5", Integer),
    Column("ext6", Integer),
    Column("ext7", Integer),
    Column("ext8", Integer),
    Column("ext9", Integer),
    Column("ext10", Integer),
    Column("ext11", Integer),
    Column("ext12", Integer),
    Column("ext13", Integer),
    Column("ext14", Integer),
    Column("ext15", Integer),
    Column("ext16", Integer),
    Column("ext17", Integer),
    Column("ext18", Integer),
    Column("ext19", Integer),
    Column("ext20", Integer),
    UniqueConstraint("user", name="chuni_profile_option_ex_uk"),
    mysql_charset="utf8mb4",
)

recent_rating = Table(
    "chuni_profile_recent_rating",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("recentRating", JSON),
    UniqueConstraint("user", name="chuni_profile_recent_rating_uk"),
    mysql_charset="utf8mb4",
)

region = Table(
    "chuni_profile_region",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("regionId", Integer),
    Column("playCount", Integer),
    UniqueConstraint("user", "regionId", name="chuni_profile_region_uk"),
    mysql_charset="utf8mb4",
)

activity = Table(
    "chuni_profile_activity",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("kind", Integer),
    Column(
        "activityId", Integer
    ),  # Reminder: Change this to ID in base.py or the game will be sad
    Column("sortNumber", Integer),
    Column("param1", Integer),
    Column("param2", Integer),
    Column("param3", Integer),
    Column("param4", Integer),
    UniqueConstraint("user", "kind", "activityId", name="chuni_profile_activity_uk"),
    mysql_charset="utf8mb4",
)

charge = Table(
    "chuni_profile_charge",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("chargeId", Integer),
    Column("stock", Integer),
    Column("purchaseDate", String(25)),
    Column("validDate", String(25)),
    Column("param1", Integer),
    Column("param2", Integer),
    Column("paramDate", String(25)),
    UniqueConstraint("user", "chargeId", name="chuni_profile_charge_uk"),
    mysql_charset="utf8mb4",
)

emoney = Table(
    "chuni_profile_emoney",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("ext1", Integer),
    Column("ext2", Integer),
    Column("ext3", Integer),
    Column("type", Integer),
    Column("emoneyBrand", Integer),
    Column("emoneyCredit", Integer),
    UniqueConstraint("user", "emoneyBrand", name="chuni_profile_emoney_uk"),
    mysql_charset="utf8mb4",
)

overpower = Table(
    "chuni_profile_overpower",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("genreId", Integer),
    Column("difficulty", Integer),
    Column("rate", Integer),
    Column("point", Integer),
    UniqueConstraint("user", "genreId", "difficulty", name="chuni_profile_emoney_uk"),
    mysql_charset="utf8mb4",
)

team = Table(
    "chuni_profile_team",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("teamName", String(255)),
    Column("teamPoint", Integer),
    Column("userTeamPoint", JSON),
    mysql_charset="utf8mb4",
)

rating = Table(
    "chuni_profile_rating",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("version", Integer, nullable=False),
    Column("type", String(255), nullable=False),
    Column("index", Integer, nullable=False),
    Column("musicId", Integer),
    Column("difficultId", Integer),
    Column("romVersionCode", Integer),
    Column("score", Integer),
    UniqueConstraint("user", "version", "type", "index", name="chuni_profile_rating_best_uk"),
    mysql_charset="utf8mb4",
)

net_battle = Table(
    "chuni_profile_net_battle",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("user", Integer, ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"), nullable=False, unique=True),
    Column("isRankUpChallengeFailed", Boolean),
    Column("highestBattleRankId", Integer),
    Column("battleIconId", Integer),
    Column("battleIconNum", Integer),
    Column("avatarEffectPoint", Integer),
    mysql_charset="utf8mb4",
)

class ChuniProfileData(BaseData):
    async def update_name(self, user_id: int, new_name: str) -> bool:
        sql = profile.update(profile.c.user == user_id).values(
            userName=new_name
        )
        result = await self.execute(sql)

        if result is None:
            self.logger.warning(f"Failed to set user {user_id} name to {new_name}")
            return False
        return True

    async def update_map_icon(self, user_id: int, version: int, new_map_icon: int) -> bool:
        sql = profile.update((profile.c.user == user_id) & (profile.c.version == version)).values(
            mapIconId=new_map_icon
        )
        result = await self.execute(sql)

        if result is None:
            self.logger.warning(f"Failed to set user {user_id} map icon")
            return False
        return True

    async def update_system_voice(self, user_id: int, version: int, new_system_voice: int) -> bool:
        sql = profile.update((profile.c.user == user_id) & (profile.c.version == version)).values(
            voiceId=new_system_voice
        )
        result = await self.execute(sql)

        if result is None:
            self.logger.warning(f"Failed to set user {user_id} system voice")
            return False
        return True

    async def update_userbox(self, user_id: int, version: int, new_nameplate: int, new_trophy: int, new_character: int) -> bool:
        sql = profile.update((profile.c.user == user_id) & (profile.c.version == version)).values(
            nameplateId=new_nameplate,
            trophyId=new_trophy,
            charaIllustId=new_character
        )
        result = await self.execute(sql)

        if result is None:
            self.logger.warning(f"Failed to set user {user_id} userbox")
            return False
        return True

    async def update_avatar(self, user_id: int, version: int, new_wear: int, new_face: int, new_head: int, new_skin: int, new_item: int, new_front: int, new_back: int) -> bool:
        sql = profile.update((profile.c.user == user_id) & (profile.c.version == version)).values(
            avatarWear=new_wear,
            avatarFace=new_face,
            avatarHead=new_head,
            avatarSkin=new_skin,
            avatarItem=new_item,
            avatarFront=new_front,
            avatarBack=new_back
        )
        result = await self.execute(sql)

        if result is None:
            self.logger.warning(f"Failed to set user {user_id} avatar")
            return False
        return True

    async def put_profile_data(
        self, aime_id: int, version: int, profile_data: Dict
    ) -> Optional[int]:
        profile_data["user"] = aime_id
        profile_data["version"] = version
        if "accessCode" in profile_data:
            profile_data.pop("accessCode")

        profile_data = self.fix_bools(profile_data)

        sql = insert(profile).values(**profile_data)
        conflict = sql.on_duplicate_key_update(**profile_data)
        result = await self.execute(conflict)

        if result is None:
            self.logger.warning(f"put_profile_data: Failed to update! aime_id: {aime_id}")
            return None
        return result.lastrowid

    async def get_profile_preview(self, aime_id: int, version: int) -> Optional[Row]:
        sql = (
            select([profile, option])
            .join(option, profile.c.user == option.c.user)
            .filter(and_(profile.c.user == aime_id, profile.c.version <= version))
        ).order_by(profile.c.version.desc())

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()

    async def get_profile_data(self, aime_id: int, version: int) -> Optional[Row]:
        sql = select(profile).where(
            and_(
                profile.c.user == aime_id,
                profile.c.version <= version,
            )
        ).order_by(profile.c.version.desc())

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()

    async def put_profile_data_ex(
        self, aime_id: int, version: int, profile_ex_data: Dict
    ) -> Optional[int]:
        profile_ex_data["user"] = aime_id
        profile_ex_data["version"] = version
        if "accessCode" in profile_ex_data:
            profile_ex_data.pop("accessCode")

        sql = insert(profile_ex).values(**profile_ex_data)
        conflict = sql.on_duplicate_key_update(**profile_ex_data)
        result = await self.execute(conflict)

        if result is None:
            self.logger.warning(
                f"put_profile_data_ex: Failed to update! aime_id: {aime_id}"
            )
            return None
        return result.lastrowid

    async def get_profile_data_ex(self, aime_id: int, version: int) -> Optional[Row]:
        sql = select(profile_ex).where(
            and_(
                profile_ex.c.user == aime_id,
                profile_ex.c.version <= version,
            )
        ).order_by(profile_ex.c.version.desc())

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()

    async def put_profile_option(self, aime_id: int, option_data: Dict) -> Optional[int]:
        option_data["user"] = aime_id

        sql = insert(option).values(**option_data)
        conflict = sql.on_duplicate_key_update(**option_data)
        result = await self.execute(conflict)

        if result is None:
            self.logger.warning(
                f"put_profile_option: Failed to update! aime_id: {aime_id}"
            )
            return None
        return result.lastrowid

    async def get_profile_option(self, aime_id: int) -> Optional[Row]:
        sql = select(option).where(option.c.user == aime_id)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()

    async def put_profile_option_ex(
        self, aime_id: int, option_ex_data: Dict
    ) -> Optional[int]:
        option_ex_data["user"] = aime_id

        sql = insert(option_ex).values(**option_ex_data)
        conflict = sql.on_duplicate_key_update(**option_ex_data)
        result = await self.execute(conflict)

        if result is None:
            self.logger.warning(
                f"put_profile_option_ex: Failed to update! aime_id: {aime_id}"
            )
            return None
        return result.lastrowid

    async def get_profile_option_ex(self, aime_id: int) -> Optional[Row]:
        sql = select(option_ex).where(option_ex.c.user == aime_id)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()

    async def put_profile_recent_rating(
        self, aime_id: int, recent_rating_data: List[Dict]
    ) -> Optional[int]:
        sql = insert(recent_rating).values(
            user=aime_id, recentRating=recent_rating_data
        )
        conflict = sql.on_duplicate_key_update(recentRating=recent_rating_data)

        result = await self.execute(conflict)
        if result is None:
            self.logger.warning(
                f"put_profile_recent_rating: Failed to update! aime_id: {aime_id}"
            )
            return None
        return result.lastrowid

    async def get_profile_recent_rating(self, aime_id: int) -> Optional[Row]:
        sql = select(recent_rating).where(recent_rating.c.user == aime_id)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()

    async def put_profile_activity(self, aime_id: int, activity_data: Dict) -> Optional[int]:
        # The game just uses "id" but we need to distinguish that from the db column "id"
        activity_data["user"] = aime_id
        activity_data["activityId"] = activity_data["id"]
        activity_data.pop("id")

        sql = insert(activity).values(**activity_data)
        conflict = sql.on_duplicate_key_update(**activity_data)
        result = await self.execute(conflict)

        if result is None:
            self.logger.warning(
                f"put_profile_activity: Failed to update! aime_id: {aime_id}"
            )
            return None
        return result.lastrowid

    async def get_profile_activity(self, aime_id: int, kind: int) -> Optional[List[Row]]:
        sql = (
            select(activity)
            .where(and_(activity.c.user == aime_id, activity.c.kind == kind))
            .order_by(activity.c.sortNumber.desc())  # to get the last played track
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def put_profile_charge(self, aime_id: int, charge_data: Dict) -> Optional[int]:
        charge_data["user"] = aime_id

        sql = insert(charge).values(**charge_data)
        conflict = sql.on_duplicate_key_update(**charge_data)
        result = await self.execute(conflict)

        if result is None:
            self.logger.warning(
                f"put_profile_charge: Failed to update! aime_id: {aime_id}"
            )
            return None
        return result.lastrowid

    async def get_profile_charge(self, aime_id: int) -> Optional[List[Row]]:
        sql = select(charge).where(charge.c.user == aime_id)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def add_profile_region(self, aime_id: int, region_id: int) -> Optional[int]:
        pass

    async def get_profile_regions(self, aime_id: int) -> Optional[List[Row]]:
        pass

    async def put_profile_emoney(self, aime_id: int, emoney_data: Dict) -> Optional[int]:
        emoney_data["user"] = aime_id

        sql = insert(emoney).values(**emoney_data)
        conflict = sql.on_duplicate_key_update(**emoney_data)

        result = await self.execute(conflict)
        if result is None:
            return None
        return result.lastrowid

    async def get_profile_emoney(self, aime_id: int) -> Optional[List[Row]]:
        sql = select(emoney).where(emoney.c.user == aime_id)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def put_profile_overpower(
        self, aime_id: int, overpower_data: Dict
    ) -> Optional[int]:
        overpower_data["user"] = aime_id

        sql = insert(overpower).values(**overpower_data)
        conflict = sql.on_duplicate_key_update(**overpower_data)

        result = await self.execute(conflict)
        if result is None:
            return None
        return result.lastrowid

    async def get_profile_overpower(self, aime_id: int) -> Optional[List[Row]]:
        sql = select(overpower).where(overpower.c.user == aime_id)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_team_by_id(self, team_id: int) -> Optional[Row]:
        sql = select(team).where(team.c.id == team_id)
        result = await self.execute(sql)

        if result is None:
            return None
        return result.fetchone()

    async def get_team_rank(self, team_id: int) -> int:
        # Normal ranking system, likely the one used in the real servers
        # Query all teams sorted by 'teamPoint'
        result = await self.execute(
            select(team.c.id).order_by(team.c.teamPoint.desc())
        )

        # Get the rank of the team with the given team_id
        rank = None
        for i, row in enumerate(result, start=1):
            if row.id == team_id:
                rank = i
                break

        # Return the rank if found, or a default rank otherwise
        return rank if rank is not None else 0

    async def update_team(self, team_id: int, team_data: Dict, user_id: str, user_point_delta: int) -> bool:
        # Update the team data
        team_data["id"] = team_id

        existing_team = self.get_team_by_id(team_id)
        if existing_team is None or "userTeamPoint" not in existing_team:
            self.logger.warning(
                f"update_team: Failed to update team! team id: {team_id}. Existing team data not found."
            )
            return False
        user_team_point_data = []
        if existing_team["userTeamPoint"] is not None and existing_team["userTeamPoint"] != "":
            user_team_point_data = json.loads(existing_team["userTeamPoint"])
        updated = False

        # Try to find the user in the existing data and update their points
        for user_point_data in user_team_point_data:
            if user_point_data["user"] == user_id:
                user_point_data["userPoint"] = str(int(user_point_delta))
                updated = True
                break

        # If the user was not found, add them to the data with the new points
        if not updated:
            user_team_point_data.append({"user": user_id, "userPoint": str(user_point_delta)})

        # Update the team's userTeamPoint field in the team data
        team_data["userTeamPoint"] = json.dumps(user_team_point_data)

        # Update the team in the database
        sql = insert(team).values(**team_data)
        conflict = sql.on_duplicate_key_update(**team_data)

        result = await self.execute(conflict)

        if result is None:
            self.logger.warning(
                f"update_team: Failed to update team! team id: {team_id}"
            )
            return False
        return True

    async def get_rival(self, rival_id: int) -> Optional[Row]:
        sql = select(profile).where(profile.c.user == rival_id)
        result = await self.execute(sql)

        if result is None:
            return None
        return result.fetchone()

    async def get_overview(self) -> Dict:
        # Fetch and add up all the playcounts
        playcount_sql = await self.execute(select(profile.c.playCount))

        if playcount_sql is None:
            self.logger.warning(
                f"get_overview: Couldn't pull playcounts"
            )
            return 0

        total_play_count = 0
        for row in playcount_sql:
            total_play_count += row[0]
        return {
            "total_play_count": total_play_count
        }
    
    async def put_profile_rating(
        self,
        aime_id: int,
        version: int,
        rating_type: str,
        rating_data: List[Dict],
    ):
        inserted_values = [
            {"user": aime_id, "version": version, "type": rating_type, "index": i, **x}
            for (i, x) in enumerate(rating_data)
        ]
        sql = insert(rating).values(inserted_values)
        update_dict = {x.name: x for x in sql.inserted if x.name != "id"}
        sql = sql.on_duplicate_key_update(**update_dict)
        result = await self.execute(sql)

        if result is None:
            self.logger.warning(
                f"put_profile_rating: Could not insert {rating_type}, aime_id: {aime_id}",
            )
            return
        
        return result.lastrowid

    async def get_profile_rating(self, aime_id: int, version: int) -> Optional[List[Row]]:
        sql = select(rating).where(and_(
                rating.c.user == aime_id,
                rating.c.version <= version,
            ))

        result = await self.execute(sql)
        if result is None:
            self.logger.warning(f"Rating of user {aime_id}, version {version} was None")
            return None
        return result.fetchall()

    async def get_all_profile_versions(self, aime_id: int) -> Optional[List[Row]]:
        sql = select([profile.c.version]).where(profile.c.user == aime_id)
        result = await self.execute(sql)
        if result is None:
            self.logger.warning(f"user {aime_id}, has no profile")
            return None
        else:
            versions_raw = result.fetchall()
            versions = [row[0] for row in versions_raw]
        return sorted(versions, reverse=True)

    async def put_net_battle(self, aime_id: int, net_battle_data: Dict) -> Optional[int]:
        sql = insert(net_battle).values(
            user=aime_id,
            isRankUpChallengeFailed=net_battle_data['isRankUpChallengeFailed'],
            highestBattleRankId=net_battle_data['highestBattleRankId'],
            battleIconId=net_battle_data['battleIconId'],
            battleIconNum=net_battle_data['battleIconNum'],
            avatarEffectPoint=net_battle_data['avatarEffectPoint'],
        )

        conflict = sql.on_duplicate_key_update(
            isRankUpChallengeFailed=net_battle_data['isRankUpChallengeFailed'],
            highestBattleRankId=net_battle_data['highestBattleRankId'],
            battleIconId=net_battle_data['battleIconId'],
            battleIconNum=net_battle_data['battleIconNum'],
            avatarEffectPoint=net_battle_data['avatarEffectPoint'],
        )

        result = await self.execute(conflict)
        if result:
            return result.inserted_primary_key['id']
        self.logger.error(f"Failed to put net battle data for user {aime_id}")

    async def get_net_battle(self, aime_id: int) -> Optional[Row]:
        result = await self.execute(net_battle.select(net_battle.c.user == aime_id))
        if result:
            return result.fetchone()
