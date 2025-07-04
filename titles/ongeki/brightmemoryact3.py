from typing import Dict

from core.config import CoreConfig
from titles.ongeki.brightmemory import OngekiBrightMemory
from titles.ongeki.const import OngekiConstants
from titles.ongeki.config import OngekiConfig


class OngekiBrightMemoryAct3(OngekiBrightMemory):
    def __init__(self, core_cfg: CoreConfig, game_cfg: OngekiConfig) -> None:
        super().__init__(core_cfg, game_cfg)
        self.version = OngekiConstants.VER_ONGEKI_BRIGHT_MEMORY_ACT3

    async def handle_get_game_setting_api_request(self, data: Dict) -> Dict:
        ret = await super().handle_get_game_setting_api_request(data)
        ret["gameSetting"]["dataVersion"] = "1.45.00"
        ret["gameSetting"]["onlineDataVersion"] = "1.45.00"
        ret["gameSetting"]["maxCountCharacter"] = 50
        ret["gameSetting"]["maxCountCard"] = 300
        ret["gameSetting"]["maxCountItem"] = 300
        ret["gameSetting"]["maxCountMusic"] = 50
        ret["gameSetting"]["maxCountMusicItem"] = 300
        ret["gameSetting"]["maxCountRivalMusic"] = 300
        return ret
