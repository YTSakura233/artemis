from datetime import datetime
from random import randint
from typing import Dict

from core.config import CoreConfig
from titles.ongeki.base import OngekiBase
from titles.ongeki.config import OngekiConfig
from titles.ongeki.const import OngekiConstants


class OngekiBright(OngekiBase):
    def __init__(self, core_cfg: CoreConfig, game_cfg: OngekiConfig) -> None:
        super().__init__(core_cfg, game_cfg)
        self.version = OngekiConstants.VER_ONGEKI_BRIGHT

    async def handle_get_game_setting_api_request(self, data: Dict) -> Dict:
        ret = await super().handle_get_game_setting_api_request(data)
        ret["gameSetting"]["dataVersion"] = "1.30.00"
        ret["gameSetting"]["onlineDataVersion"] = "1.30.00"
        return ret

    async def handle_cm_get_user_data_api_request(self, data: Dict) -> Dict:
        # check for a bright profile
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

        # add access code that we don't store
        user_data["accessCode"] = cards[0]["access_code"]

        # add the compatible card maker version from config
        card_maker_ver = self.game_cfg.version.version(self.version)
        if card_maker_ver and card_maker_ver.get("card_maker"):
            # Card Maker 1.30 = 1.30.01+
            # Card Maker 1.35 = 1.35.03+
            user_data["compatibleCmVersion"] = card_maker_ver.get("card_maker")

        return {"userId": data["userId"], "userData": user_data}

    async def handle_printer_login_api_request(self, data: Dict):
        return {"returnCode": 1}

    async def handle_printer_logout_api_request(self, data: Dict):
        return {"returnCode": 1}

    async def handle_cm_get_user_card_api_request(self, data: Dict) -> Dict:
        user_id: int = data["userId"]
        max_ct: int = data["maxCount"]
        next_idx: int = data["nextIndex"]

        rows = await self.data.item.get_cards(
            user_id, limit=max_ct + 1, offset=next_idx
        )

        if rows is None:
            return {}
        
        card_list = []

        for row in rows[:max_ct]:
            card = row._asdict()
            card.pop("id")
            card.pop("user")
            card_list.append(card)
        
        if len(rows) > max_ct:
            next_idx += max_ct
        else:
            next_idx = 0

        return {
            "userId": data["userId"],
            "length": len(card_list),
            "nextIndex": next_idx,
            "userCardList": card_list,
        }

    async def handle_cm_get_user_character_api_request(self, data: Dict) -> Dict:
        user_id: int = data["userId"]
        max_ct: int = data["maxCount"]
        next_idx: int = data["nextIndex"]

        rows = await self.data.item.get_characters(
            user_id, limit=max_ct + 1, offset=next_idx
        )

        if rows is None:
            return {
                "userId": user_id,
                "length": 0,
                "nextIndex": 0,
                "userCharacterList": [],
            }

        character_list = []

        for row in rows[:max_ct]:
            character = row._asdict()
            character.pop("id")
            character.pop("user")
            character_list.append(character)

        if len(rows) > max_ct:
            next_idx += max_ct
        else:
            next_idx = 0

        return {
            "userId": data["userId"],
            "length": len(character_list),
            "nextIndex": next_idx,
            "userCharacterList": character_list,
        }

    async def handle_get_user_gacha_api_request(self, data: Dict) -> Dict:
        user_gachas = await self.data.item.get_user_gachas(data["userId"])
        if user_gachas is None:
            return {"userId": data["userId"], "length": 0, "userGachaList": []}

        user_gacha_list = []
        for gacha in user_gachas:
            tmp = gacha._asdict()
            tmp.pop("id")
            tmp.pop("user")
            tmp["dailyGachaDate"] = datetime.strftime(tmp["dailyGachaDate"], "%Y-%m-%d")
            user_gacha_list.append(tmp)

        return {
            "userId": data["userId"],
            "length": len(user_gacha_list),
            "userGachaList": user_gacha_list,
        }

    async def handle_cm_get_user_item_api_request(self, data: Dict) -> Dict:
        return await self.handle_get_user_item_api_request(data)

    async def handle_cm_get_user_gacha_supply_api_request(self, data: Dict) -> Dict:
        # not used for now? not sure what it even does
        user_gacha_supplies = await self.data.item.get_user_gacha_supplies(data["userId"])
        if user_gacha_supplies is None:
            return {"supplyId": 1, "length": 0, "supplyCardList": []}

        supply_list = [gacha["cardId"] for gacha in user_gacha_supplies]

        return {
            "supplyId": 1,
            "length": len(supply_list),
            "supplyCardList": supply_list,
        }

    async def handle_get_game_gacha_api_request(self, data: Dict) -> Dict:
        """
        returns all current active banners (gachas)
        "Select Gacha" requires maxSelectPoint set and isCeiling set to 1
        """
        game_gachas = []
        # for every gacha_id in the OngekiConfig, grab the banner from the db
        for gacha_id in self.game_cfg.gachas.enabled_gachas:
            game_gacha = await self.data.static.get_gacha(self.version, gacha_id)
            if game_gacha:
                game_gachas.append(game_gacha)

        # clean the database rows
        game_gacha_list = []
        for gacha in game_gachas:
            tmp = gacha._asdict()
            tmp.pop("id")
            tmp.pop("version")
            tmp["startDate"] = datetime.strftime(tmp["startDate"], "%Y-%m-%d %H:%M:%S")
            tmp["endDate"] = datetime.strftime(tmp["endDate"], "%Y-%m-%d %H:%M:%S")
            tmp["noticeStartDate"] = datetime.strftime(
                tmp["noticeStartDate"], "%Y-%m-%d %H:%M:%S"
            )
            tmp["noticeEndDate"] = datetime.strftime(
                tmp["noticeEndDate"], "%Y-%m-%d %H:%M:%S"
            )
            tmp["convertEndDate"] = datetime.strftime(
                tmp["convertEndDate"], "%Y-%m-%d %H:%M:%S"
            )

            # make sure to only show gachas for the current version
            # so only up to bright, 1140 is the first bright memory gacha
            if self.version >= OngekiConstants.VER_ONGEKI_BRIGHT_MEMORY:
                game_gacha_list.append(tmp)
            elif (
                self.version == OngekiConstants.VER_ONGEKI_BRIGHT
                and tmp["gachaId"] < 1140
            ):
                game_gacha_list.append(tmp)

        return {
            "length": len(game_gacha_list),
            "gameGachaList": game_gacha_list,
            # no clue
            "registIdList": [],
        }

    async def handle_roll_gacha_api_request(self, data: Dict) -> Dict:
        """
        Handle a gacha roll API request
        """
        gacha_id = data["gachaId"]
        num_rolls = data["times"]
        # change_rate is the 5 gacha rool SR gurantee once a week
        change_rate = data["changeRate"]
        # SSR book which guarantees a SSR card, itemKind=15, itemId=1
        book_used = data["bookUseCount"]
        if num_rolls not in {1, 5, 11}:
            return {}

        # https://gamerch.com/ongeki/entry/462978

        # 77% chance of gett ing a R card
        # 20% chance of getting a SR card
        # 3% chance of getting a SSR card
        rarity = [1 for _ in range(77)]
        rarity += [2 for _ in range(20)]
        rarity += [3 for _ in range(3)]

        # gachaId 1011 is "無料ガチャ" (free gacha), which requires GatchaTickets
        # itemKind=11, itemId=1 and appearenty sucks
        # 94% chance of getting a R card
        # 5% chance of getting a SR card
        # 1% chance of getting a SSR card
        if gacha_id == 1011:
            rarity = [1 for _ in range(94)]
            rarity += [2 for _ in range(5)]
            rarity += [3 for _ in range(1)]

        # gachaId 1012 is "無料ガチャ（SR確定）" (SR confirmed! free gacha), which
        # requires GatchaTickets itemKind=11, itemId=4 and always guarantees
        # a SR card or higher
        # 92% chance of getting a SR card
        # 8% chance of getting a SSR card
        elif gacha_id == 1012:
            rarity = [2 for _ in range(92)]
            rarity += [3 for _ in range(8)]

        assert len(rarity) == 100

        # uniform distribution to get the rarity of the card
        rolls = [rarity[randint(0, len(rarity) - 1)] for _ in range(num_rolls)]

        # if SSR book used, make sure you always get one SSR
        if book_used == 1:
            if rolls.count(3) == 0:
                # if there is no SSR, re-roll
                return self.handle_roll_gacha_api_request(data)
        # make sure that 11 rolls always have at least 1 SR or SSR
        elif (num_rolls == 5 and change_rate is True) or num_rolls == 11:
            if rolls.count(2) == 0 and rolls.count(3) == 0:
                # if there is no SR or SSR, re-roll
                return self.handle_roll_gacha_api_request(data)

        # get a list of cards for each rarity
        cards_r = await self.data.static.get_cards_by_rarity(self.version, 1)
        cards_sr, cards_ssr = [], []

        # free gachas are only allowed to get their specific cards! (R irrelevant)
        if gacha_id in {1011, 1012}:
            gacha_cards = await self.data.static.get_gacha_cards(gacha_id)
            for card in gacha_cards:
                if card["rarity"] == 3:
                    cards_sr.append({"cardId": card["cardId"], "rarity": 2})
                elif card["rarity"] == 4:
                    cards_ssr.append({"cardId": card["cardId"], "rarity": 3})
        else:
            cards_sr = await self.data.static.get_cards_by_rarity(self.version, 2)
            cards_ssr = await self.data.static.get_cards_by_rarity(self.version, 3)

            # get the promoted cards for that gacha and add them multiple
            # times to increase chances by factor chances
            chances = 10

            gacha_cards = await self.data.static.get_gacha_cards(gacha_id)
            for card in gacha_cards:
                # make sure to add the cards to the corresponding rarity
                if card["rarity"] == 2:
                    cards_r += [{"cardId": card["cardId"], "rarity": 1}] * chances
                if card["rarity"] == 3:
                    cards_sr += [{"cardId": card["cardId"], "rarity": 2}] * chances
                elif card["rarity"] == 4:
                    cards_ssr += [{"cardId": card["cardId"], "rarity": 3}] * chances

        # get the card id for each roll
        rolled_cards = []
        for i in range(len(rolls)):
            if rolls[i] == 1:
                rolled_cards.append(cards_r[randint(0, len(cards_r) - 1)])
            elif rolls[i] == 2:
                rolled_cards.append(cards_sr[randint(0, len(cards_sr) - 1)])
            elif rolls[i] == 3:
                rolled_cards.append(cards_ssr[randint(0, len(cards_ssr) - 1)])

        game_gacha_card_list = []
        for card in rolled_cards:
            game_gacha_card_list.append(
                {
                    "gachaId": data["gachaId"],
                    "cardId": card["cardId"],
                    # +1 because Card Maker is weird
                    "rarity": card["rarity"] + 1,
                    "weight": 1,
                    "isPickup": False,
                    "isSelect": False,
                }
            )

        return {
            "length": len(game_gacha_card_list),
            "gameGachaCardList": game_gacha_card_list,
        }

    async def handle_cm_upsert_user_gacha_api_request(self, data: Dict):
        upsert = data["cmUpsertUserGacha"]
        user_id = data["userId"]

        gacha_id = data["gachaId"]
        gacha_count = data["gachaCnt"]
        play_date = datetime.strptime(data["playDate"][:10], "%Y-%m-%d")
        select_point = data["selectPoint"]

        total_gacha_count, ceiling_gacha_count = 0, 0
        # 0 = can still use Gacha Select, 1 = already used Gacha Select
        use_select_point = 0
        daily_gacha_cnt, five_gacha_cnt, eleven_gacha_cnt = 0, 0, 0
        daily_gacha_date = datetime.strptime("2000-01-01", "%Y-%m-%d")

        # check if the user previously rolled the exact same gacha
        user_gacha = await self.data.item.get_user_gacha(user_id, gacha_id)
        if user_gacha:
            total_gacha_count = user_gacha["totalGachaCnt"]
            ceiling_gacha_count = user_gacha["ceilingGachaCnt"]
            daily_gacha_cnt = user_gacha["dailyGachaCnt"]
            five_gacha_cnt = user_gacha["fiveGachaCnt"]
            eleven_gacha_cnt = user_gacha["elevenGachaCnt"]
            # if the Gacha Select has been used, make sure to keep it
            if user_gacha["useSelectPoint"] == 1:
                use_select_point = 1
            # parse just the year, month and date
            daily_gacha_date = user_gacha["dailyGachaDate"]

        # if the saved dailyGachaDate is different from the roll,
        # reset dailyGachaCnt and change the date
        if daily_gacha_date != play_date:
            daily_gacha_date = play_date
            daily_gacha_cnt = 0

        await self.data.item.put_user_gacha(
            user_id,
            gacha_id,
            totalGachaCnt=total_gacha_count + gacha_count,
            ceilingGachaCnt=ceiling_gacha_count + gacha_count,
            selectPoint=select_point,
            useSelectPoint=use_select_point,
            dailyGachaCnt=daily_gacha_cnt + gacha_count,
            fiveGachaCnt=five_gacha_cnt + 1 if gacha_count == 5 else five_gacha_cnt,
            elevenGachaCnt=eleven_gacha_cnt + 1
            if gacha_count == 11
            else eleven_gacha_cnt,
            dailyGachaDate=daily_gacha_date,
        )

        if "userData" in upsert and len(upsert["userData"]) > 0:
            # check if the profile is a bright memory profile
            p = await self.data.profile.get_profile_data(data["userId"], self.version)
            if p is not None:
                # save the bright memory profile
                await self.data.profile.put_profile_data(
                    user_id, self.version, upsert["userData"][0]
                )
            else:
                # save the bright profile
                await self.data.profile.put_profile_data(
                    user_id, self.version, upsert["userData"][0]
                )

        if "userCharacterList" in upsert:
            for x in upsert["userCharacterList"]:
                await self.data.item.put_character(user_id, x)

        if "userItemList" in upsert:
            for x in upsert["userItemList"]:
                await self.data.item.put_item(user_id, x)

        if "userCardList" in upsert:
            for x in upsert["userCardList"]:
                await self.data.item.put_card(user_id, x)

        # TODO?
        # if "gameGachaCardList" in upsert:
        #    for x in upsert["gameGachaCardList"]:

        return {"returnCode": 1, "apiName": "CMUpsertUserGachaApi"}

    async def handle_cm_upsert_user_select_gacha_api_request(self, data: Dict) -> Dict:
        upsert = data["cmUpsertUserSelectGacha"]
        user_id = data["userId"]

        if "userData" in upsert and len(upsert["userData"]) > 0:
            # check if the profile is a bright memory profile
            p = await self.data.profile.get_profile_data(data["userId"], self.version)
            if p is not None:
                # save the bright memory profile
                await self.data.profile.put_profile_data(
                    user_id, self.version, upsert["userData"][0]
                )
            else:
                # save the bright profile
                await self.data.profile.put_profile_data(
                    user_id, self.version, upsert["userData"][0]
                )

        if "userCharacterList" in upsert:
            for x in upsert["userCharacterList"]:
                await self.data.item.put_character(user_id, x)

        if "userCardList" in upsert:
            for x in upsert["userCardList"]:
                await self.data.item.put_card(user_id, x)

        if "selectGachaLogList" in data:
            for x in data["selectGachaLogList"]:
                await self.data.item.put_user_gacha(
                    user_id,
                    x["gachaId"],
                    selectPoint=0,
                    useSelectPoint=x["useSelectPoint"],
                )

        return {"returnCode": 1, "apiName": "cmUpsertUserSelectGacha"}

    async def handle_get_game_gacha_card_by_id_api_request(self, data: Dict) -> Dict:
        game_gacha_cards = await self.data.static.get_gacha_cards(data["gachaId"])
        if game_gacha_cards == []:
            # fallback to be at least able to select that gacha
            return {
                "gachaId": data["gachaId"],
                "length": 6,
                "isPickup": False,
                "gameGachaCardList": [
                    {
                        "gachaId": data["gachaId"],
                        "cardId": 100984,
                        "rarity": 4,
                        "weight": 1,
                        "isPickup": False,
                        "isSelect": True,
                    },
                    {
                        "gachaId": data["gachaId"],
                        "cardId": 100997,
                        "rarity": 3,
                        "weight": 2,
                        "isPickup": False,
                        "isSelect": True,
                    },
                    {
                        "gachaId": data["gachaId"],
                        "cardId": 100998,
                        "rarity": 3,
                        "weight": 2,
                        "isPickup": False,
                        "isSelect": True,
                    },
                    {
                        "gachaId": data["gachaId"],
                        "cardId": 101020,
                        "rarity": 2,
                        "weight": 3,
                        "isPickup": False,
                        "isSelect": True,
                    },
                    {
                        "gachaId": data["gachaId"],
                        "cardId": 101021,
                        "rarity": 2,
                        "weight": 3,
                        "isPickup": False,
                        "isSelect": True,
                    },
                    {
                        "gachaId": data["gachaId"],
                        "cardId": 101022,
                        "rarity": 2,
                        "weight": 3,
                        "isPickup": False,
                        "isSelect": True,
                    },
                ],
                "emissionList": [],
                "afterCalcList": [],
                "ssrBookCalcList": [],
            }

        game_gacha_card_list = []
        for gacha_card in game_gacha_cards:
            tmp = gacha_card._asdict()
            tmp.pop("id")
            game_gacha_card_list.append(tmp)

        return {
            "gachaId": data["gachaId"],
            "length": len(game_gacha_card_list),
            "isPickup": False,
            "gameGachaCardList": game_gacha_card_list,
            # again no clue
            "emissionList": [],
            "afterCalcList": [],
            "ssrBookCalcList": [],
        }

    async def handle_get_game_theater_api_request(self, data: Dict) -> Dict:
        """
        shows a banner after every print, not sure what its used for
        """

        """
        return {
            "length": 1,
            "gameTheaterList": [{
                "theaterId": 1,
                "theaterName": "theaterName",
                "startDate": "2018-01-01 00:00:00.0",
                "endDate": "2038-01-01 00:00:00.0",
                "gameSubTheaterList": [{
                    "theaterId": 1,
                    "id": 2,
                    "no": 4
                }]
            }
            ],
            "registIdList": []
        }
        """

        return {"length": 0, "gameTheaterList": [], "registIdList": []}

    async def handle_cm_upsert_user_print_playlog_api_request(self, data: Dict) -> Dict:
        return {
            "returnCode": 1,
            "orderId": 0,
            "serialId": "11111111111111111111",
            "apiName": "CMUpsertUserPrintPlaylogApi",
        }

    async def handle_cm_upsert_user_printlog_api_request(self, data: Dict) -> Dict:
        return {
            "returnCode": 1,
            "orderId": 0,
            "serialId": "11111111111111111111",
            "apiName": "CMUpsertUserPrintlogApi",
        }

    async def handle_cm_upsert_user_print_api_request(self, data: Dict) -> Dict:
        user_print_detail = data["userPrintDetail"]

        # generate random serial id
        serial_id = "".join([str(randint(0, 9)) for _ in range(20)])

        # not needed because are either zero or unset
        user_print_detail.pop("orderId")
        user_print_detail.pop("printNumber")
        user_print_detail.pop("serialId")
        user_print_detail["printDate"] = datetime.strptime(
            user_print_detail["printDate"], "%Y-%m-%d"
        )

        # add the entry to the user print table with the random serialId
        await self.data.item.put_user_print_detail(
            data["userId"], serial_id, user_print_detail
        )

        return {
            "returnCode": 1,
            "serialId": serial_id,
            "apiName": "CMUpsertUserPrintApi",
        }

    async def handle_cm_upsert_user_all_api_request(self, data: Dict) -> Dict:
        upsert = data["cmUpsertUserAll"]
        user_id = data["userId"]

        if "userData" in upsert and len(upsert["userData"]) > 0:
            # check if the profile is a bright memory profile
            p = await self.data.profile.get_profile_data(data["userId"], self.version)
            if p is not None:
                # save the bright memory profile
                await self.data.profile.put_profile_data(
                    user_id, self.version, upsert["userData"][0]
                )
            else:
                # save the bright profile
                await self.data.profile.put_profile_data(
                    user_id, self.version, upsert["userData"][0]
                )

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

        if "userItemList" in upsert:
            for x in upsert["userItemList"]:
                await self.data.item.put_item(user_id, x)

        if "userCardList" in upsert:
            for x in upsert["userCardList"]:
                await self.data.item.put_card(user_id, x)

        return {"returnCode": 1, "apiName": "cmUpsertUserAll"}
