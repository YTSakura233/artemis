from titles.mai2.index import Mai2Servlet
from titles.mai2.const import Mai2Constants
from titles.mai2.database import Mai2Data
from titles.mai2.read import Mai2Reader
from .frontend import Mai2Frontend

index = Mai2Servlet
database = Mai2Data
reader = Mai2Reader
frontend = Mai2Frontend
game_codes = [
    Mai2Constants.GAME_CODE_DX,
    Mai2Constants.GAME_CODE_FINALE,
    Mai2Constants.GAME_CODE_MILK,
    Mai2Constants.GAME_CODE_MURASAKI,
    Mai2Constants.GAME_CODE_PINK,
    Mai2Constants.GAME_CODE_ORANGE,
    Mai2Constants.GAME_CODE_GREEN,
    Mai2Constants.GAME_CODE,
    Mai2Constants.GAME_CODE_DX_INT,
    Mai2Constants.GAME_CODE_DX_CHN,
]
