from typing import Dict

from core.config import CoreConfig
from titles.mai2.buddiesplus import Mai2BuddiesPlus
from titles.mai2.const import Mai2Constants
from titles.mai2.config import Mai2Config


class Mai2Prism(Mai2BuddiesPlus):
    def __init__(self, cfg: CoreConfig, game_cfg: Mai2Config) -> None:
        super().__init__(cfg, game_cfg)
        self.version = Mai2Constants.VER_MAIMAI_DX_PRISM

    async def handle_cm_get_user_preview_api_request(self, data: Dict) -> Dict:
        user_data = await super().handle_cm_get_user_preview_api_request(data)

        # hardcode lastDataVersion for CardMaker
        user_data["lastDataVersion"] = "1.50.00"
        return user_data


    async def handle_get_user_new_item_list_api_request(self, data: Dict) -> Dict:
        return {
            "user_id": data["userId"],
            "userItemList": []
        }

    #seems to be used for downloading music scores online
    async def handle_get_game_music_score_api_request(self, data: Dict) -> Dict:
        return {
            "gameMusicScore": {
                "musicId": data["musicId"],
                "level": data["level"],
                "type": data["type"],
                "scoreData": ""
            }
        }

    async def handle_get_game_kaleidx_scope_api_request(self, data: Dict) -> Dict:
        return {
            "gameKaleidxScopeList": [
                {"gateId": 1, "phaseId": 6},
                {"gateId": 2, "phaseId": 6},
                {"gateId": 3, "phaseId": 6},
                {"gateId": 4, "phaseId": 6},
            ]
        }

    async def handle_get_user_kaleidx_scope_api_request(self, data: Dict) -> Dict:
        # kaleidxscope keyget condition judgement
        # player may get key before GateFound
        for gate in range(1,5):
            if gate == 1 or gate == 4:
                condition_satisfy = 0
                for condition in Mai2Constants.KALEIDXSCOPE_KEY_CONDITION[gate]:
                    score_list = await self.data.score.get_best_scores(user_id=data["userId"], song_id=condition)
                    if score_list:
                        condition_satisfy = condition_satisfy + 1
                if len(Mai2Constants.KALEIDXSCOPE_KEY_CONDITION[gate]) == condition_satisfy:
                    new_kaleidxscope = {'gateId': gate, "isKeyFound": True}
                    await self.data.score.put_user_kaleidxscope(data["userId"], new_kaleidxscope)

            elif gate == 2:
                user_profile = await self.data.profile.get_profile_detail(user_id=data["userId"], version=self.version)
                user_frame = user_profile["frameId"]
                if user_frame == 459504:
                    playlogs = await self.data.score.get_playlogs(user_id=data["userId"], idx=0, limit=0)

                    playlog_dict = {}
                    for playlog in playlogs:
                        playlog_id = playlog["playlogId"]
                        if playlog_id not in playlog_dict:
                            playlog_dict[playlog_id] = []
                        playlog_dict[playlog_id].append(playlog["musicId"])
                    valid_playlogs = []
                    allowed_music = set(Mai2Constants.KALEIDXSCOPE_KEY_CONDITION[2])
                    for playlog_id, music_ids in playlog_dict.items():

                        if len(music_ids) != len(set(music_ids)):
                            continue
                        all_valid = True
                        for mid in music_ids:
                            if mid not in allowed_music:
                                all_valid = False
                                break
                        if all_valid:
                            valid_playlogs.append(playlog_id)

                    if valid_playlogs:
                        new_kaleidxscope = {'gateId': 2, "isKeyFound": True}
                        await self.data.score.put_user_kaleidxscope(data["userId"], new_kaleidxscope)

        kaleidxscope = await self.data.score.get_user_kaleidxscope_list(data["userId"])

        if kaleidxscope is None:
            return {"userId": data["userId"], "userKaleidxScopeList":[]}

        kaleidxscope_list = []
        for kaleidxscope_data in kaleidxscope:
            tmp = kaleidxscope_data._asdict()
            tmp.pop("user")
            tmp.pop("id")
            kaleidxscope_list.append(tmp)
        return {
            "userId": data["userId"],
            "userKaleidxScopeList": kaleidxscope_list
        }


    async def handle_get_game_ng_word_list_api_request(self, data: Dict) -> Dict:
        # for maimai DX China version
        return {
            "ngWordExactMatchLength":0,
            "ngWordExactMatchList":[],
            "ngWordPartialMatchLength":0,
            "ngWordPartialMatchList":[]
        }