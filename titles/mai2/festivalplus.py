from typing import Dict

from core.config import CoreConfig
from titles.mai2.festival import Mai2Festival
from titles.mai2.const import Mai2Constants
from titles.mai2.config import Mai2Config


class Mai2FestivalPlus(Mai2Festival):
    def __init__(self, cfg: CoreConfig, game_cfg: Mai2Config) -> None:
        super().__init__(cfg, game_cfg)
        self.version = Mai2Constants.VER_MAIMAI_DX_FESTIVAL_PLUS

    async def handle_cm_get_user_preview_api_request(self, data: Dict) -> Dict:
        user_data = await super().handle_cm_get_user_preview_api_request(data)

        # hardcode lastDataVersion for CardMaker
        user_data["lastDataVersion"] = "1.35.00"
        return user_data
