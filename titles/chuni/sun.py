from typing import Dict, Any

from core.config import CoreConfig
from titles.chuni.newplus import ChuniNewPlus
from titles.chuni.const import ChuniConstants
from titles.chuni.config import ChuniConfig


class ChuniSun(ChuniNewPlus):
    def __init__(self, core_cfg: CoreConfig, game_cfg: ChuniConfig) -> None:
        super().__init__(core_cfg, game_cfg)
        self.version = ChuniConstants.VER_CHUNITHM_SUN

    async def handle_cm_get_user_preview_api_request(self, data: Dict) -> Dict:
        user_data = await super().handle_cm_get_user_preview_api_request(data)

        # hardcode lastDataVersion for CardMaker 1.35 A032
        user_data["lastDataVersion"] = "2.10.00"
        return user_data

    #SDGS Exclusive
    async def handle_get_user_cto_c_play_api_request(self, data: Dict) -> Dict:
        return {
            "userId": data["userId"],
            "orderBy": "0",
            "count": "0",
            #game request c2c play history while login but seem unused(?)
            "userCtoCPlayList": [],
        }