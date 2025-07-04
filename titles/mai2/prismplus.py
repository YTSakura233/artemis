from typing import Dict

from core.config import CoreConfig
from titles.mai2.prism import Mai2Prism
from titles.mai2.const import Mai2Constants
from titles.mai2.config import Mai2Config



class Mai2PrismPlus(Mai2Prism):
    def __init__(self, cfg: CoreConfig, game_cfg: Mai2Config) -> None:
        super().__init__(cfg, game_cfg)
        self.version = Mai2Constants.VER_MAIMAI_DX_PRISM_PLUS

    async def handle_cm_get_user_preview_api_request(self, data: Dict) -> Dict:
        user_data = await super().handle_cm_get_user_preview_api_request(data)

        # hardcode lastDataVersion for CardMaker
        user_data["lastDataVersion"] = "1.55.00"
        return user_data

    async def handle_upsert_client_play_time_api_request(self, data: Dict) -> Dict:
        return{
            "returnCode": 1,
            "apiName": "UpsertClientPlayTimeApi"
        }