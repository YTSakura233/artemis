import itertools
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List

import pytz

from core.config import CoreConfig
from titles.ongeki.config import OngekiConfig
from titles.ongeki.const import OngekiConstants
from titles.ongeki.database import OngekiData


class OngekiBattleGrade(Enum):
    FAILED = 0
    DRAW = 1
    USUALLY = 2
    GOOD = 3
    GREAT = 4
    EXCELLENT = 5
    UNBELIEVABLE_GOLD = 6
    UNBELIEVABLE_RAINBOW = 7


class OngekiBattlePointGrade(Enum):
    FRESHMAN = 0
    KYU10 = 1
    KYU9 = 2
    KYU8 = 3
    KYU7 = 4
    KYU6 = 5
    KYU5 = 6
    KYU4 = 7
    KYU3 = 8
    KYU2 = 9
    KYU1 = 10
    DAN1 = 11
    DAN2 = 12
    DAN3 = 13
    DAN4 = 14
    DAN5 = 15
    DAN6 = 16
    DAN7 = 17
    DAN8 = 18
    DAN9 = 19
    DAN10 = 20
    SODEN = 21


class OngekiTechnicalGrade(Enum):
    D = 0
    C = 1
    B = 2
    BB = 3
    BBB = 4
    A = 5
    AA = 6
    AAA = 7
    S = 8
    SS = 9
    SSS = 10
    SSSp = 11


class OngekiDifficulty(Enum):
    BASIC = 0
    ADVANCED = 1
    EXPERT = 2
    MASTER = 3
    LUNATIC = 10


class OngekiGPLogKind(Enum):
    NONE = 0
    BUY1_START = 1
    BUY2_START = 2
    BUY3_START = 3
    BUY1_ADD = 4
    BUY2_ADD = 5
    BUY3_ADD = 6
    FIRST_PLAY = 7
    COMPENSATION = 8

    PAY_PLAY = 11
    PAY_TIME = 12
    PAY_MAS_UNLOCK = 13
    PAY_MONEY = 14


class OngekiBase:
    def __init__(self, core_cfg: CoreConfig, game_cfg: OngekiConfig) -> None:
        self.core_cfg = core_cfg
        self.game_cfg = game_cfg
        self.data = OngekiData(core_cfg)
        self.date_time_format = "%Y-%m-%d %H:%M:%S"
        self.date_time_format_ext = (
            "%Y-%m-%d %H:%M:%S.%f"  # needs to be lopped off at [:-5]
        )
        self.date_time_format_short = "%Y-%m-%d"
        self.logger = logging.getLogger("ongeki")
        self.game = OngekiConstants.GAME_CODE
        self.version = OngekiConstants.VER_ONGEKI

    async def handle_get_game_setting_api_request(self, data: Dict) -> Dict:
        # if reboot start/end time is not defined use the default behavior of being a few hours ago
        if self.core_cfg.title.reboot_start_time == "" or self.core_cfg.title.reboot_end_time == "":
            reboot_start = datetime.strftime(
                datetime.utcnow() + timedelta(hours=6), self.date_time_format
            )
            reboot_end = datetime.strftime(
                datetime.utcnow() + timedelta(hours=7), self.date_time_format
            )
        else:
            # get current datetime in JST
            current_jst = datetime.now(pytz.timezone('Asia/Tokyo')).date()

            # parse config start/end times into datetime
            reboot_start_time = datetime.strptime(self.core_cfg.title.reboot_start_time, "%H:%M")
            reboot_end_time = datetime.strptime(self.core_cfg.title.reboot_end_time, "%H:%M")

            # offset datetimes with current date/time
            reboot_start_time = reboot_start_time.replace(year=current_jst.year, month=current_jst.month, day=current_jst.day, tzinfo=pytz.timezone('Asia/Tokyo'))
            reboot_end_time = reboot_end_time.replace(year=current_jst.year, month=current_jst.month, day=current_jst.day, tzinfo=pytz.timezone('Asia/Tokyo'))

            # create strings for use in gameSetting
            reboot_start = reboot_start_time.strftime(self.date_time_format)
            reboot_end = reboot_end_time.strftime(self.date_time_format)

        return {
            "gameSetting": {
                "dataVersion": "1.00.00",
                "onlineDataVersion": "1.00.00",
                "isMaintenance": "false",
                "requestInterval": 10,
                "rebootStartTime": reboot_start,
                "rebootEndTime": reboot_end,
                "isBackgroundDistribute": "false",
                "maxCountCharacter": 50,
                "maxCountCard": 300,
                "maxCountItem": 300,
                "maxCountMusic": 50,
                "maxCountMusicItem": 300,
                "macCountRivalMusic": 300,
            },
            "isDumpUpload": "false",
            "isAou": "true",
        }

    async def handle_get_game_idlist_api_request(self, data: Dict) -> Dict:
        """
        Gets lists of song IDs, either disabled songs or recomended songs depending on type?
        """
        # type - int
        # id - int
        return {"type": data["type"], "length": 0, "gameIdlistList": []}

    async def handle_get_game_ranking_api_request(self, data: Dict) -> Dict:
        try:
            date = datetime.now(pytz.timezone('Asia/Tokyo')) - timedelta(days=1,hours=7)

            # type 1 - current ranking; type 2 - previous ranking
            if data["type"] == 2:
                date = date - timedelta(1)

            rankings = await self.data.score.get_rankings(date)

            if not rankings or (data["type"] == 1 and len(rankings) < 10):
                return {"type": data["type"], "gameRankingList": []}

            ranking_list = []
            for count, music_id in rankings:
                ranking_list.append({"id": music_id, "point": count, "userName": ""})

            return {"type": data["type"], "gameRankingList": ranking_list}

        except Exception as e:
            self.logger.error(f"Error while getting game ranking: {e}")
            return {"type": data["type"], "gameRankingList": []}

    async def handle_get_game_point_api_request(self, data: Dict) -> Dict:
        get_game_point = await self.data.static.get_static_game_point()
        game_point = []

        if not get_game_point:
            self.logger.info(f"GP table is empty, inserting defaults")
            await self.data.static.put_static_game_point_defaults()
            get_game_point = await self.data.static.get_static_game_point()
            for gp in get_game_point:
                tmp = gp._asdict()
                game_point.append(tmp)
            return {
                "length": len(game_point),
                "gamePointList": game_point,
                }
        for gp in get_game_point:
            tmp = gp._asdict()
            game_point.append(tmp)
        return {
            "length": len(game_point),
            "gamePointList": game_point,
        }
        
    async def handle_game_login_api_request(self, data: Dict) -> Dict:
        return {"returnCode": 1, "apiName": "gameLogin"}

    async def handle_game_logout_api_request(self, data: Dict) -> Dict:
        return {"returnCode": 1, "apiName": "gameLogout"}

    async def handle_extend_lock_time_api_request(self, data: Dict) -> Dict:
        return {"returnCode": 1, "apiName": "ExtendLockTimeApi"}

    async def handle_get_game_reward_api_request(self, data: Dict) -> Dict:
        get_game_rewards = await self.data.static.get_reward_list(self.version)

        reward_list = []
        for reward in get_game_rewards:
            tmp = reward._asdict()
            tmp.pop("id")
            tmp.pop("version")
            tmp.pop("rewardname")
            reward_list.append(tmp)

        if reward_list is None:
            return {"length": 0, "gameRewardList": []}
        return {
            "length": len(reward_list),
            "gameRewardList": reward_list,
        }

    async def handle_get_game_present_api_request(self, data: Dict) -> Dict:
        get_present = await self.data.static.get_present_list(self.version)

        present_list = []
        for present in get_present:
            tmp = present._asdict()
            tmp.pop("id")
            tmp.pop("version")
            present_list.append(tmp)

        if present_list is None:
            return {"length": 0, "gamePresentList": []}
        return {
            "length": len(present_list),
            "gamePresentList": present_list,
        }

    async def handle_get_game_message_api_request(self, data: Dict) -> Dict:
        return {"length": 0, "gameMessageList": []}

    async def handle_get_game_sale_api_request(self, data: Dict) -> Dict:
        return {"length": 0, "gameSaleList": []}

    async def handle_get_game_tech_music_api_request(self, data: Dict) -> Dict:
        music_list = await self.data.static.get_tech_music(self.version)

        prep_music_list = []
        for music in music_list:
            tmp = music._asdict()
            tmp.pop("id")
            tmp.pop("version")
            prep_music_list.append(tmp)

        if prep_music_list is None:
            return {"length": 0, "gameTechMusicList": []}

        return {
            "length": len(prep_music_list),
            "gameTechMusicList": prep_music_list,
        }

    async def handle_upsert_client_setting_api_request(self, data: Dict) -> Dict:
        if self.core_cfg.server.is_develop:
            return {"returnCode": 1, "apiName": "UpsertClientSettingApi"}

        client_id = data["clientId"]
        client_setting_data = data["clientSetting"]
        cab = await self.data.arcade.get_machine(client_id)
        if cab is not None:
            await self.data.static.put_client_setting_data(cab['id'], client_setting_data)
        return {"returnCode": 1, "apiName": "UpsertClientSettingApi"}

    async def handle_upsert_client_testmode_api_request(self, data: Dict) -> Dict:
        if self.core_cfg.server.is_develop:
            return {"returnCode": 1, "apiName": "UpsertClientTestmodeApi"}

        region_id = data["regionId"]
        client_testmode_data = data["clientTestmode"]
        await self.data.static.put_client_testmode_data(region_id, client_testmode_data)
        return {"returnCode": 1, "apiName": "UpsertClientTestmodeApi"}

    async def handle_upsert_client_bookkeeping_api_request(self, data: Dict) -> Dict:
        return {"returnCode": 1, "apiName": "upsertClientBookkeeping"}

    async def handle_upsert_client_develop_api_request(self, data: Dict) -> Dict:
        return {"returnCode": 1, "apiName": "upsertClientDevelop"}

    async def handle_upsert_client_error_api_request(self, data: Dict) -> Dict:
        return {"returnCode": 1, "apiName": "upsertClientError"}

    async def handle_upsert_user_gplog_api_request(self, data: Dict) -> Dict:
        user = data["userId"]

        # If playing as guest, the user ID is or(0x1000000000001, (placeId & 65535) << 32)
        if user & 0x1000000000001 == 0x1000000000001:
            user = None

        await self.data.log.put_gp_log(
            user,
            data["usedCredit"],
            data["placeName"],
            data["userGplog"]["trxnDate"],
            data["userGplog"]["placeId"],
            data["userGplog"]["kind"],
            data["userGplog"]["pattern"],
            data["userGplog"]["currentGP"],
        )

        return {"returnCode": 1, "apiName": "UpsertUserGplogApi"}

    async def handle_extend_lock_time_api_request(self, data: Dict) -> Dict:
        return {"returnCode": 1, "apiName": "ExtendLockTimeApi"}

    async def handle_get_game_event_api_request(self, data: Dict) -> Dict:
        evts = await self.data.static.get_enabled_events(self.version)

        if evts is None:
            return {
            "type": data["type"],
            "length": 0,
            "gameEventList": [],
        } 

        evt_list = []
        for event in evts:
            evt_list.append(
                {
                    "type": event["type"],
                    "id": event["eventId"],
                    # actually use the startDate from the import so it
                    # properly shows all the events when new ones are imported
                    "startDate": datetime.strftime(event["startDate"], "%Y-%m-%d %H:%M:%S.0"),
                    #"endDate": "2099-12-31 00:00:00.0",
                    "endDate": datetime.strftime(event["endDate"], "%Y-%m-%d %H:%M:%S.0"),
                }
            )
        
        return {
            "type": data["type"],
            "length": len(evt_list),
            "gameEventList": evt_list,
        }

    async def handle_get_game_id_list_api_request(self, data: Dict) -> Dict:
        game_idlist: List[str, Any] = []  # 1 to 230 & 8000 to 8050

        if data["type"] == 1:
            for i in range(1, 231):
                game_idlist.append({"type": 1, "id": i})
            return {
                "type": data["type"],
                "length": len(game_idlist),
                "gameIdlistList": game_idlist,
            }
        elif data["type"] == 2:
            for i in range(8000, 8051):
                game_idlist.append({"type": 2, "id": i})
            return {
                "type": data["type"],
                "length": len(game_idlist),
                "gameIdlistList": game_idlist,
            }

    async def handle_get_user_region_api_request(self, data: Dict) -> Dict:
        return {"userId": data["userId"], "length": 0, "userRegionList": []}

    async def handle_get_user_preview_api_request(self, data: Dict) -> Dict:
        profile = await self.data.profile.get_profile_preview(data["userId"], self.version)

        if profile is None:
            return {
                "userId": data["userId"],
                "isLogin": False,
                "lastLoginDate": "0000-00-00 00:00:00",
                "userName": "",
                "reincarnationNum": 0,
                "level": 0,
                "exp": 0,
                "playerRating": 0,
                "lastGameId": "",
                "lastRomVersion": "",
                "lastDataVersion": "",
                "lastPlayDate": "",
                "nameplateId": 0,
                "trophyId": 0,
                "cardId": 0,
                "dispPlayerLv": 0,
                "dispRating": 0,
                "dispBP": 0,
                "headphone": 0,
                "banStatus": 0,
                "isWarningConfirmed": True,
            }

        return {
            "userId": data["userId"],
            "isLogin": False,
            "lastLoginDate": profile["lastPlayDate"],
            "userName": profile["userName"],
            "reincarnationNum": profile["reincarnationNum"],
            "level": profile["level"],
            "exp": profile["exp"],
            "playerRating": profile["playerRating"],
            "lastGameId": profile["lastGameId"],
            "lastRomVersion": profile["lastRomVersion"],
            "lastDataVersion": profile["lastDataVersion"],
            "lastPlayDate": profile["lastPlayDate"],
            "nameplateId": profile["nameplateId"],
            "trophyId": profile["trophyId"],
            "cardId": profile["cardId"],
            "dispPlayerLv": profile["dispPlayerLv"],
            "dispRating": profile["dispRating"],
            "dispBP": profile["dispBP"],
            "headphone": profile["headphone"],
            "banStatus": profile["banStatus"],
            "isWarningConfirmed": True,
        }

    async def handle_get_user_tech_count_api_request(self, data: Dict) -> Dict:
        """
        Gets the number of AB and ABPs a player has per-difficulty (7, 7+, 8, etc)
        The game sends this in upsert so we don't have to calculate it all out thankfully
        """
        utcl = await self.data.score.get_tech_count(data["userId"])
        userTechCountList = []

        for tc in utcl:
            tmp = tc._asdict()
            tmp.pop("id")
            tmp.pop("user")
            userTechCountList.append(tmp)

        return {
            "userId": data["userId"],
            "length": len(userTechCountList),
            "userTechCountList": userTechCountList,
        }

    async def handle_get_user_tech_event_api_request(self, data: Dict) -> Dict:
        user_tech_event_list = await self.data.item.get_tech_event(self.version, data["userId"])
        if user_tech_event_list is None:
            return {}

        tech_evt = []
        for evt in user_tech_event_list:
            tmp = evt._asdict()
            tmp.pop("id")
            tmp.pop("user")
            tmp.pop("version")
            tech_evt.append(tmp)

        return {
            "userId": data["userId"],
            "length": len(tech_evt),
            "userTechEventList": tech_evt,
        }

    async def handle_get_user_tech_event_ranking_api_request(self, data: Dict) -> Dict:
        user_tech_event_ranks = await self.data.item.get_tech_event_ranking(self.version, data["userId"])
        if user_tech_event_ranks is None: 
            return {
            "userId": data["userId"],
            "length": 0,
            "userTechEventRankingList": [],
        }

        # collect the whole table and clear other players, to preserve proper ranking
        evt_ranking = []
        for evt in user_tech_event_ranks:
            tmp = evt._asdict()
            if tmp["user"] != data["userId"]:
                tmp.clear()
            else:
                tmp.pop("id")
                tmp.pop("user")
                evt_ranking.append(tmp)

        return {
            "userId": data["userId"],
            "length": len(evt_ranking),
            "userTechEventRankingList": evt_ranking,
        }

    async def handle_get_user_kop_api_request(self, data: Dict) -> Dict:
        kop_list = await self.data.profile.get_kop(data["userId"])
        if kop_list is None:
            return {}

        for kop in kop_list:
            kop.pop("user")
            kop.pop("id")

        return {
            "userId": data["userId"],
            "length": len(kop_list),
            "userKopList": kop_list,
        }

    async def handle_get_user_music_api_request(self, data: Dict) -> Dict:
        user_id: int = data["userId"]
        next_idx: int = data["nextIndex"]
        max_ct: int = data["maxCount"]

        rows = await self.data.score.get_best_scores(
            user_id, limit=max_ct + 1, offset=next_idx
        )

        if rows is None:
            return {
                "userId": user_id,
                "length": 0,
                "nextIndex": 0,
                "userMusicList": [],
            }

        music_details = [row._asdict() for row in rows]
        returned_count = 0
        music_list = []

        for _music_id, details_iter in itertools.groupby(music_details, key=lambda d: d["musicId"]):
            details: list[dict[Any, Any]] = []

            for d in details_iter:
                d.pop("id")
                d.pop("user")
                
                details.append(d)

            music_list.append({"length": len(details), "userMusicDetailList": details})
            returned_count += len(details)

            if len(music_list) >= max_ct:
                break
        
        if returned_count < len(rows):
            next_idx += max_ct
        else:
            next_idx = 0

        return {
            "userId": user_id,
            "length": len(music_list),
            "nextIndex": next_idx,
            "userMusicList": music_list,
        }

    async def handle_get_user_item_api_request(self, data: Dict) -> Dict:
        user_id: int = data["userId"]
        next_idx: int = data["nextIndex"]
        max_ct: int = data["maxCount"]

        kind = next_idx // 10000000000
        next_idx = next_idx % 10000000000

        rows = await self.data.item.get_items(
            user_id, kind, limit=max_ct + 1, offset=next_idx
        )

        if rows is None:
            return {
                "userId": user_id,
                "nextIndex": 0,
                "itemKind": kind,
                "length": 0,
                "userItemList": [],
            }

        items: List[Dict[str, Any]] = []

        for row in rows[:max_ct]:
            item = row._asdict()
            
            item.pop("id")
            item.pop("user")
            
            items.append(item)

        if len(rows) > max_ct:
            next_idx = kind * 10000000000 + next_idx + max_ct
        else:
            next_idx = 0

        return {
            "userId": user_id,
            "nextIndex": next_idx,
            "itemKind": kind,
            "length": len(items),
            "userItemList": items,
        }

    async def handle_get_user_option_api_request(self, data: Dict) -> Dict:
        o = await self.data.profile.get_profile_options(data["userId"])
        if o is None:
            return {}

        # get the dict representation of the row so we can modify values
        user_opts = o._asdict()

        # remove the values the game doesn't want
        user_opts.pop("id")
        user_opts.pop("user")

        return {"userId": data["userId"], "userOption": user_opts}

    async def handle_get_user_data_api_request(self, data: Dict) -> Dict:
        p = await self.data.profile.get_profile_data(data["userId"], self.version)
        if p is None:
            return {}

        cards = await self.data.card.get_user_cards(data["userId"])
        if cards is None or len(cards) == 0:
            # This should never happen
            self.logger.error(
                f"handle_get_user_data_api_request: Internal error - No cards found for user id {data['userId']}"
            )
            return {}

        # get the dict representation of the row so we can modify values
        user_data = p._asdict()

        # remove the values the game doesn't want
        user_data.pop("id")
        user_data.pop("user")
        user_data.pop("version")

        # TODO: replace datetime objects with strings

        # add access code that we don't store
        user_data["accessCode"] = cards[0]["access_code"]

        return {"userId": data["userId"], "userData": user_data}

    async def handle_get_user_event_ranking_api_request(self, data: Dict) -> Dict:
        user_event_ranking_list = await self.data.item.get_ranking_event_ranks(self.version, data["userId"])
        if user_event_ranking_list is None:
            return {}

        # We collect the whole ranking table, and clear out any not needed data, this way we preserve the proper ranking 
        # In official spec this should be done server side, in maintenance period
        prep_event_ranking = []
        for evt in user_event_ranking_list:
            tmp = evt._asdict()
            if tmp["user"] != data["userId"]:
                tmp.clear()
            else:
                tmp.pop("id")
                tmp.pop("user")
                prep_event_ranking.append(tmp)

        return {
            "userId": data["userId"],
            "length": len(prep_event_ranking),
            "userEventRankingList": prep_event_ranking,
        }

    async def handle_get_user_login_bonus_api_request(self, data: Dict) -> Dict:
        user_login_bonus_list = await self.data.item.get_login_bonuses(data["userId"])
        if user_login_bonus_list is None:
            return {}

        login_bonuses = []
        for scenerio in user_login_bonus_list:
            tmp = scenerio._asdict()
            tmp.pop("id")
            tmp.pop("user")
            login_bonuses.append(tmp)

        return {
            "userId": data["userId"],
            "length": len(login_bonuses),
            "userLoginBonusList": login_bonuses,
        }

    async def handle_get_user_bp_base_request(self, data: Dict) -> Dict:
        p = await self.data.profile.get_profile(
            self.game, self.version, user_id=data["userId"]
        )
        if p is None:
            return {}
        profile = json.loads(p["data"])
        return {
            "userId": data["userId"],
            "length": len(profile["userBpBaseList"]),
            "userBpBaseList": profile["userBpBaseList"],
        }

    async def handle_get_user_recent_rating_api_request(self, data: Dict) -> Dict:
        recent_rating = await self.data.profile.get_profile_recent_rating(data["userId"])
        if recent_rating is None:
            return {
                "userId": data["userId"],
                "length": 0,
                "userRecentRatingList": [],
            }

        userRecentRatingList = recent_rating["recentRating"]

        return {
            "userId": data["userId"],
            "length": len(userRecentRatingList),
            "userRecentRatingList": userRecentRatingList,
        }

    async def handle_get_user_activity_api_request(self, data: Dict) -> Dict:
        activity = await self.data.profile.get_profile_activity(data["userId"], data["kind"])
        if activity is None:
            return {}

        user_activity = []

        for act in activity:
            user_activity.append(
                {
                    "kind": act["kind"],
                    "id": act["activityId"],
                    "sortNumber": act["sortNumber"],
                    "param1": act["param1"],
                    "param2": act["param2"],
                    "param3": act["param3"],
                    "param4": act["param4"],
                }
            )

        return {
            "userId": data["userId"],
            "length": len(user_activity),
            "kind": data["kind"],
            "userActivityList": user_activity,
        }

    async def handle_get_user_story_api_request(self, data: Dict) -> Dict:
        user_stories = await self.data.item.get_stories(data["userId"])
        if user_stories is None:
            return {}

        story_list = []
        for story in user_stories:
            tmp = story._asdict()
            tmp.pop("id")
            tmp.pop("user")
            story_list.append(tmp)

        return {
            "userId": data["userId"],
            "length": len(story_list),
            "userStoryList": story_list,
        }

    async def handle_get_user_chapter_api_request(self, data: Dict) -> Dict:
        user_chapters = await self.data.item.get_chapters(data["userId"])
        if user_chapters is None:
            return {}

        chapter_list = []
        for chapter in user_chapters:
            tmp = chapter._asdict()
            tmp.pop("id")
            tmp.pop("user")
            chapter_list.append(tmp)

        return {
            "userId": data["userId"],
            "length": len(chapter_list),
            "userChapterList": chapter_list,
        }

    async def handle_get_user_training_room_by_key_api_request(self, data: Dict) -> Dict:
        return {
            "userId": data["userId"],
            "length": 0,
            "userTrainingRoomList": [],
        }

    async def handle_get_user_character_api_request(self, data: Dict) -> Dict:
        user_characters = await self.data.item.get_characters(data["userId"])
        if user_characters is None:
            return {}

        character_list = []
        for character in user_characters:
            tmp = character._asdict()
            tmp.pop("id")
            tmp.pop("user")
            character_list.append(tmp)

        return {
            "userId": data["userId"],
            "length": len(character_list),
            "userCharacterList": character_list,
        }

    async def handle_get_user_card_api_request(self, data: Dict) -> Dict:
        user_cards = await self.data.item.get_cards(data["userId"])
        if user_cards is None:
            return {}

        card_list = []
        for card in user_cards:
            tmp = card._asdict()
            tmp.pop("id")
            tmp.pop("user")
            card_list.append(tmp)

        return {
            "userId": data["userId"],
            "length": len(card_list),
            "userCardList": card_list,
        }

    async def handle_get_user_deck_by_key_api_request(self, data: Dict) -> Dict:
        # Auth key doesn't matter, it just wants all the decks
        decks = await self.data.item.get_decks(data["userId"])
        if decks is None:
            return {}

        deck_list = []
        for deck in decks:
            tmp = deck._asdict()
            tmp.pop("user")
            tmp.pop("id")
            deck_list.append(tmp)

        return {
            "userId": data["userId"],
            "length": len(deck_list),
            "userDeckList": deck_list,
        }

    async def handle_get_user_trade_item_api_request(self, data: Dict) -> Dict:
        user_trade_items = await self.data.item.get_trade_items(data["userId"])
        if user_trade_items is None:
            return {}

        trade_item_list = []
        for trade_item in user_trade_items:
            tmp = trade_item._asdict()
            tmp.pop("id")
            tmp.pop("user")
            trade_item_list.append(tmp)

        return {
            "userId": data["userId"],
            "length": len(trade_item_list),
            "userTradeItemList": trade_item_list,
        }

    async def handle_get_user_scenario_api_request(self, data: Dict) -> Dict:
        user_scenerio = await self.data.item.get_scenerios(data["userId"])
        if user_scenerio is None:
            return {}

        scenerio_list = []
        for scenerio in user_scenerio:
            tmp = scenerio._asdict()
            tmp.pop("id")
            tmp.pop("user")
            scenerio_list.append(tmp)

        return {
            "userId": data["userId"],
            "length": len(scenerio_list),
            "userScenarioList": scenerio_list,
        }

    async def handle_get_user_ratinglog_api_request(self, data: Dict) -> Dict:
        rating_log = await self.data.profile.get_profile_rating_log(data["userId"])
        if rating_log is None:
            return {}

        userRatinglogList = []
        for rating in rating_log:
            tmp = rating._asdict()
            tmp.pop("id")
            tmp.pop("user")
            userRatinglogList.append(tmp)

        return {
            "userId": data["userId"],
            "length": len(userRatinglogList),
            "userRatinglogList": userRatinglogList,
        }

    async def handle_get_user_mission_point_api_request(self, data: Dict) -> Dict:
        user_mission_point_list = await self.data.item.get_mission_points(self.version, data["userId"])
        if user_mission_point_list is None:
            return {}

        mission_point_list = []
        for evt_music in user_mission_point_list:
            tmp = evt_music._asdict()
            tmp.pop("id")
            tmp.pop("user")
            tmp.pop("version")
            mission_point_list.append(tmp)


        return {
            "userId": data["userId"],
            "length": len(mission_point_list),
            "userMissionPointList": mission_point_list,
        }

    async def handle_get_user_event_point_api_request(self, data: Dict) -> Dict:
        user_event_point_list = await self.data.item.get_event_points(data["userId"])
        if user_event_point_list is None:
            return {}

        event_point_list = []
        for evt_music in user_event_point_list:
            tmp = evt_music._asdict()
            tmp.pop("id")
            tmp.pop("user")
            # pop other stuff event_point doesn't want
            tmp.pop("rank")
            tmp.pop("type")
            tmp.pop("date")
            event_point_list.append(tmp)

        return {
            "userId": data["userId"],
            "length": len(event_point_list),
            "userEventPointList": event_point_list,
        }

    async def handle_get_user_music_item_api_request(self, data: Dict) -> Dict:
        user_music_item_list = await self.data.item.get_music_items(data["userId"])
        if user_music_item_list is None:
            return {}

        music_item_list = []
        for evt_music in user_music_item_list:
            tmp = evt_music._asdict()
            tmp.pop("id")
            tmp.pop("user")
            music_item_list.append(tmp)

        return {
            "userId": data["userId"],
            "length": len(music_item_list),
            "userMusicItemList": music_item_list,
        }

    async def handle_get_user_event_music_api_request(self, data: Dict) -> Dict:
        user_evt_music_list = await self.data.item.get_event_music(data["userId"])
        if user_evt_music_list is None:
            return {}

        evt_music_list = []
        for evt_music in user_evt_music_list:
            tmp = evt_music._asdict()
            tmp.pop("id")
            tmp.pop("user")
            evt_music_list.append(tmp)

        return {
            "userId": data["userId"],
            "length": len(evt_music_list),
            "userEventMusicList": evt_music_list,
        }

    async def handle_get_user_boss_api_request(self, data: Dict) -> Dict:
        p = await self.data.item.get_bosses(data["userId"])
        if p is None:
            return {}

        boss_list = []
        for boss in p:
            tmp = boss._asdict()
            tmp.pop("id")
            tmp.pop("user")
            boss_list.append(tmp)

        return {
            "userId": data["userId"],
            "length": len(boss_list),
            "userBossList": boss_list,
        }

    async def handle_upsert_user_all_api_request(self, data: Dict) -> Dict:
        upsert = data["upsertUserAll"]
        user_id = data["userId"]

        if user_id & 0x1000000000001 == 0x1000000000001:
            place_id = int(user_id) & 0xFFFC00000000
            
            self.logger.info("Guest play from place ID %d, ignoring.", place_id)
            return {"returnCode": 1, "apiName": "UpsertUserAllApi"}

        # The isNew fields are new as of Red and up. We just won't use them for now.

        if "userData" in upsert and len(upsert["userData"]) > 0:
            await self.data.profile.put_profile_data(
                user_id, self.version, upsert["userData"][0]
            )

        if "userOption" in upsert and len(upsert["userOption"]) > 0:
            await self.data.profile.put_profile_options(user_id, upsert["userOption"][0])

        if "userPlaylogList" in upsert:
            for playlog in upsert["userPlaylogList"]:
                await self.data.score.put_playlog(user_id, playlog)

        if "userActivityList" in upsert:
            for act in upsert["userActivityList"]:
                await self.data.profile.put_profile_activity(
                    user_id,
                    act["kind"],
                    act["id"],
                    act["sortNumber"],
                    act["param1"],
                    act["param2"],
                    act["param3"],
                    act["param4"],
                )

        if "userRecentRatingList" in upsert:
            await self.data.profile.put_profile_recent_rating(
                user_id, upsert["userRecentRatingList"]
            )

        if "userBpBaseList" in upsert:
            await self.data.profile.put_profile_bp_list(user_id, upsert["userBpBaseList"])

        if "userMusicDetailList" in upsert:
            for x in upsert["userMusicDetailList"]:
                await self.data.score.put_best_score(user_id, x)

        if "userCharacterList" in upsert:
            for x in upsert["userCharacterList"]:
                await self.data.item.put_character(user_id, x)

        if "userCardList" in upsert:
            for x in upsert["userCardList"]:
                await self.data.item.put_card(user_id, x)

        if "userDeckList" in upsert:
            for x in upsert["userDeckList"]:
                await self.data.item.put_deck(user_id, x)

        if "userTrainingRoomList" in upsert:
            for x in upsert["userTrainingRoomList"]:
                await self.data.profile.put_training_room(user_id, x)

        if "userStoryList" in upsert:
            for x in upsert["userStoryList"]:
                await self.data.item.put_story(user_id, x)

        if "userChapterList" in upsert:
            for x in upsert["userChapterList"]:
                await self.data.item.put_chapter(user_id, x)

        if "userMemoryChapterList" in upsert:
            for x in upsert["userMemoryChapterList"]:
                await self.data.item.put_memorychapter(user_id, x)

        if "userItemList" in upsert:
            for x in upsert["userItemList"]:
                await self.data.item.put_item(user_id, x)

        if "userMusicItemList" in upsert:
            for x in upsert["userMusicItemList"]:
                await self.data.item.put_music_item(user_id, x)

        if "userLoginBonusList" in upsert:
            for x in upsert["userLoginBonusList"]:
                await self.data.item.put_login_bonus(user_id, x)

        if "userEventPointList" in upsert:
            for x in upsert["userEventPointList"]:
                await self.data.item.put_event_point(user_id, self.version, x)

        if "userMissionPointList" in upsert:
            for x in upsert["userMissionPointList"]:
                await self.data.item.put_mission_point(user_id, self.version, x)

        if "userRatinglogList" in upsert:
            for x in upsert["userRatinglogList"]:
                await self.data.profile.put_profile_rating_log(
                    user_id, x["dataVersion"], x["highestRating"]
                )

        if "userBossList" in upsert:
            for x in upsert["userBossList"]:
                await self.data.item.put_boss(user_id, x)

        if "userTechCountList" in upsert:
            for x in upsert["userTechCountList"]:
                await self.data.score.put_tech_count(user_id, x)

        if "userScenerioList" in upsert:
            for x in upsert["userScenerioList"]:
                await self.data.item.put_scenerio(user_id, x)

        if "userTradeItemList" in upsert:
            for x in upsert["userTradeItemList"]:
                await self.data.item.put_trade_item(user_id, x)

        if "userEventMusicList" in upsert:
            for x in upsert["userEventMusicList"]:
                await self.data.item.put_event_music(user_id, x)

        if "userTechEventList" in upsert:
            for x in upsert["userTechEventList"]:
                await self.data.item.put_tech_event(user_id, self.version, x)

                # This should be updated once a day in maintenance window, but for time being we will push the update on each upsert
                await self.data.item.put_tech_event_ranking(user_id, self.version, x)

        if "userKopList" in upsert:
            for x in upsert["userKopList"]:
                await self.data.profile.put_kop(user_id, x)
            
        for rating_type in {
            "userRatingBaseBestList",
            "userRatingBaseBestNewList",
            "userRatingBaseHotList",
            "userRatingBaseNextList",
            "userRatingBaseNextNewList",
            "userRatingBaseHotNextList",
        }:
            if rating_type not in upsert:
                continue

            await self.data.profile.put_profile_rating(
                user_id,
                self.version,
                rating_type,
                upsert[rating_type],
            )

        return {"returnCode": 1, "apiName": "upsertUserAll"}

    async def handle_get_user_rival_api_request(self, data: Dict) -> Dict:
        """
        Added in Bright
        """

        rival_list = []
        user_rivals = await self.data.profile.get_rivals(data["userId"])
        for rival in user_rivals:
            tmp = {}
            tmp["rivalUserId"] = rival[0]
            rival_list.append(tmp)

        if user_rivals is None or len(rival_list) < 1:
            return {
                "userId": data["userId"],
                "length": 0,
                "userRivalList": [],
            }
        return {
            "userId": data["userId"],
            "length": len(rival_list),
            "userRivalList": rival_list,
        }

    async def handle_get_user_rival_data_api_request(self, data: Dict) -> Dict:
        """
        Added in Bright
        """
        rivals = []
        for rival in data["userRivalList"]:
            name = await self.data.profile.get_profile_name(
                rival["rivalUserId"], self.version
            )
            if name is None:
                continue
            rivals.append({"rivalUserId": rival["rivalUserId"], "rivalUserName": name})
        return {
            "userId": data["userId"],
            "length": len(rivals),
            "userRivalDataList": rivals,
        }

    async def handle_get_user_rival_music_api_request(self, data: Dict) -> Dict:
        """
        Added in Bright
        """
        user_id: int = data["userId"]
        rival_id: int = data["rivalUserId"]
        next_idx: int = data["nextIndex"]
        max_ct: int = data["maxCount"]

        rows = await self.data.score.get_best_scores(
            rival_id, limit=max_ct + 1, offset=next_idx
        )

        if rows is None:
            return {
                "userId": user_id,
                "rivalUserId": rival_id,
                "nextIndex": 0,
                "length": 0,
                "userRivalMusicList": [],
            }
        
        music_details = [row._asdict() for row in rows]
        returned_count = 0
        music_list = []

        for _music_id, details_iter in itertools.groupby(music_details, key=lambda d: d["musicId"]):
            details: list[dict[Any, Any]] = []

            for d in details_iter:
                d.pop("id")
                d.pop("user")
                d.pop("playCount")
                d.pop("isLock")
                d.pop("clearStatus")
                d.pop("isStoryWatched")

                details.append(d)

            music_list.append({"length": len(details), "userRivalMusicDetailList": details})
            returned_count += len(details)

            if len(music_list) >= max_ct:
                break
        
        if returned_count < len(rows):
            next_idx += max_ct
        else:
            next_idx = 0

        return {
            "userId": user_id,
            "rivalUserId": rival_id,
            "nextIndex": next_idx,
            "length": len(music_list),
            "userRivalMusicList": music_list,
        }
