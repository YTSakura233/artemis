from typing import Dict, Any, Optional
import logging, coloredlogs
from logging.handlers import TimedRotatingFileHandler
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from datetime import datetime
from Crypto.Cipher import Blowfish
import pytz

from .config import CoreConfig
from .utils import Utils
from .title import TitleServlet
from .data import Data
from .const import *

class MuchaServlet:
    mucha_registry: Dict[str, Dict[str, str]] = {}
    def __init__(self, cfg: CoreConfig, cfg_dir: str) -> None:
        self.config = cfg
        self.config_dir = cfg_dir

        self.logger = logging.getLogger("mucha")
        log_fmt_str = "[%(asctime)s] Mucha | %(levelname)s | %(message)s"
        log_fmt = logging.Formatter(log_fmt_str)

        fileHandler = TimedRotatingFileHandler(
            "{0}/{1}.log".format(self.config.server.log_dir, "mucha"),
            when="d",
            backupCount=10,
        )
        fileHandler.setFormatter(log_fmt)

        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(log_fmt)

        self.logger.addHandler(fileHandler)
        self.logger.addHandler(consoleHandler)

        self.logger.setLevel(cfg.mucha.loglevel)
        coloredlogs.install(level=cfg.mucha.loglevel, logger=self.logger, fmt=log_fmt_str)
        
        self.data = Data(cfg)

        for _, mod in TitleServlet.title_registry.items():
            enabled, game_cds, netids = mod.get_mucha_info(self.config, self.config_dir)
            if enabled:
                for x in range(len(game_cds)):
                    self.mucha_registry[game_cds[x]] = { "netid_prefix": netids[x] }

        self.logger.info(f"Serving {len(self.mucha_registry)} games")

    async def handle_boardauth(self, request: Request) -> bytes:
        bod = await request.body()
        req_dict = self.mucha_preprocess(bod)
        client_ip = Utils.get_ip_addr(request)

        if req_dict is None:
            self.logger.error(
                f"Error processing mucha request {bod}"
            )
            return PlainTextResponse("RESULTS=000")

        req = MuchaAuthRequest(req_dict)
        self.logger.debug(f"Mucha request {vars(req)}")
        
        if not req.gameCd or not req.gameVer or not req.sendDate or not req.countryCd or not req.serialNum:
            self.logger.warning(f"Missing required fields - {vars(req)}")
            return PlainTextResponse("RESULTS=000")

        minfo = self.mucha_registry.get(req.gameCd, {})

        if not minfo:
            self.logger.warning(f"Unknown gameCd {req.gameCd} from {client_ip}")
            return PlainTextResponse("RESULTS=000")

        b_key = b""
        for x in range(8):
            b_key += req.sendDate[(x - 1) & 7].encode()
        
        b_iv = b_key # what the fuck namco

        cipher = Blowfish.new(b_key, Blowfish.MODE_CBC, b_iv)
        try:
            sn_decrypt = cipher.decrypt(bytes.fromhex(req.serialNum))[:12].decode()
        except Exception as e:
            self.logger.error(f"Decrypt SN {req.serialNum} failed! - {e}")
            return PlainTextResponse("RESULTS=000")

        self.logger.info(f"Boardauth request from {sn_decrypt} ({client_ip}) for {req.gameVer}")

        resp = MuchaAuthResponse(
            f"{self.config.server.hostname}{':' + str(self.config.server.port) if not self.config.server.is_using_proxy else ''}"
        )

        netid = minfo.get('netid_prefix', "ABxN") + sn_decrypt[5:]

        cab = await self.data.arcade.get_machine(netid)
        if cab:
            arcade = await self.data.arcade.get_arcade(cab['id'])
            if not arcade:
                self.logger.error(f"Failed to get arcade with id {cab['id']}")
                return PlainTextResponse("RESULTS=000")

            resp.AREA_0 = arcade["region_id"] or AllnetJapanRegionId.AICHI.name
            resp.AREA_0_EN = arcade["region_id"] or AllnetJapanRegionId.AICHI.name
            resp.AREA_FULL_0 = arcade["region_id"] or AllnetJapanRegionId.AICHI.name
            resp.AREA_FULL_0_EN = arcade["region_id"] or AllnetJapanRegionId.AICHI.name
            
            resp.AREA_1 = arcade["country"] or cab['country'] or AllnetCountryCode.JAPAN.value
            resp.AREA_1_EN = arcade["country"] or cab['country'] or AllnetCountryCode.JAPAN.value
            resp.AREA_FULL_1 = arcade["country"] or cab['country'] or AllnetCountryCode.JAPAN.value
            resp.AREA_FULL_1_EN = arcade["country"] or cab['country'] or AllnetCountryCode.JAPAN.value

            resp.AREA_2 = arcade["city"] if arcade["city"] else ""
            resp.AREA_2_EN = arcade["city"] if arcade["city"] else ""
            resp.AREA_FULL_2 = arcade["city"] if arcade["city"] else ""
            resp.AREA_FULL_2_EN = arcade["city"] if arcade["city"] else ""

            resp.AREA_3 = ""
            resp.AREA_3_EN = ""
            resp.AREA_FULL_3 = ""
            resp.AREA_FULL_3_EN = ""

            resp.PREFECTURE_ID = arcade['region_id']
            resp.COUNTRY_CD = arcade['country'] or cab['country'] or AllnetCountryCode.JAPAN.value
            resp.PLACE_ID = req.placeId if req.placeId else f"{arcade['country'] or cab['country'] or AllnetCountryCode.JAPAN.value}{arcade['id']:04X}"
            resp.SHOP_NAME = arcade['name']
            resp.SHOP_NAME_EN = arcade['name']
            resp.SHOP_NICKNAME = arcade['nickname']
            resp.SHOP_NICKNAME_EN = arcade['nickname']

        elif self.config.server.allow_unregistered_serials:
            self.logger.info(f"Allow unknown serial {netid} ({sn_decrypt}) to auth")
        
        else:
            self.logger.warning(f'Auth failed for NetID {netid}')
            return PlainTextResponse("RESULTS=000")

        self.logger.debug(f"Mucha response {vars(resp)}")

        return PlainTextResponse(self.mucha_postprocess(vars(resp)))

    async def handle_updatecheck(self, request: Request) -> bytes:
        bod = await request.body()
        req_dict = self.mucha_preprocess(bod)
        client_ip = Utils.get_ip_addr(request)

        if req_dict is None:
            self.logger.error(
                f"Error processing mucha request {bod}"
            )
            return PlainTextResponse("RESULTS=000")

        req = MuchaUpdateRequest(req_dict)
        self.logger.info(f"Updatecheck request from {req.serialNum} ({client_ip}) for {req.gameVer}")        
        self.logger.debug(f"Mucha request {vars(req)}")

        if req.gameCd not in self.mucha_registry:
            self.logger.warning(f"Unknown gameCd {req.gameCd}")
            return PlainTextResponse("RESULTS=000")

        resp = MuchaUpdateResponse(req.gameVer, f"{self.config.server.hostname}{':' + str(self.config.server.port) if not self.config.server.is_using_proxy else ''}")

        self.logger.debug(f"Mucha response {vars(resp)}")

        return PlainTextResponse(self.mucha_postprocess(vars(resp)))

    async def handle_dlstate(self, request: Request) -> bytes:
        bod = await request.body()
        req_dict = self.mucha_preprocess(bod)
        client_ip = Utils.get_ip_addr(request)

        if req_dict is None:
            self.logger.error(
                f"Error processing mucha request {bod}"
            )
            return PlainTextResponse("RESULTS=000")
        
        req = MuchaDownloadStateRequest(req_dict)
        self.logger.info(f"DownloadState request from {req.serialNum} ({client_ip}) for {req.gameCd} -> {req.updateVer}")        
        self.logger.debug(f"request {vars(req)}")
        return PlainTextResponse("RESULTS=001")

    def mucha_preprocess(self, data: bytes) -> Optional[Dict]:
        try:
            ret: Dict[str, Any] = {}

            for x in data.decode().split("&"):
                kvp = x.split("=")
                if len(kvp) == 2:
                    ret[kvp[0]] = kvp[1]

            return ret

        except Exception:
            self.logger.error(f"Error processing mucha request {data}")
            return None

    def mucha_postprocess(self, data: dict) -> Optional[bytes]:
        try:
            urlencode = "&".join(f"{k}={v}" for k, v in data.items())

            return urlencode.encode()

        except Exception:
            self.logger.error("Error processing mucha response")
            return None


class MuchaAuthRequest:
    def __init__(self, request: Dict) -> None:
        # gameCd + boardType + countryCd + version
        self.gameVer = request.get("gameVer", "")
        self.sendDate = request.get("sendDate", "")  # %Y%m%d
        self.serialNum = request.get("serialNum", "")
        self.gameCd = request.get("gameCd", "")
        self.boardType = request.get("boardType", "")
        self.boardId = request.get("boardId", "")
        self.mac = request.get("mac", "")
        self.placeId = request.get("placeId", "")
        self.storeRouterIp = request.get("storeRouterIp", "")
        self.countryCd = request.get("countryCd", "")
        self.useToken = request.get("useToken", "")
        self.allToken = request.get("allToken", "")


class MuchaAuthResponse:
    def __init__(self, mucha_url: str) -> None:
        self.RESULTS = "001"
        self.AUTH_INTERVAL = "86400"
        self.SERVER_TIME = datetime.strftime(datetime.now(), "%Y%m%d%H%M")
        self.SERVER_TIME_UTC = datetime.strftime(datetime.now(pytz.UTC), "%Y%m%d%H%M")

        self.CHARGE_URL = f"https://{mucha_url}/charge/"
        self.FILE_URL = f"https://{mucha_url}/file/"
        self.URL_1 = f"https://{mucha_url}/url1/"
        self.URL_2 = f"https://{mucha_url}/url2/"
        self.URL_3 = f"https://{mucha_url}/url3/"

        self.PLACE_ID = "JPN123"
        self.COUNTRY_CD = "JPN"
        self.SHOP_NAME = "TestShop!"
        self.SHOP_NICKNAME = "TestShop"
        self.AREA_0 = "008"
        self.AREA_1 = "009"
        self.AREA_2 = "010"
        self.AREA_3 = "011"
        self.AREA_FULL_0 = ""
        self.AREA_FULL_1 = ""
        self.AREA_FULL_2 = ""
        self.AREA_FULL_3 = ""

        self.SHOP_NAME_EN = "TestShop!"
        self.SHOP_NICKNAME_EN = "TestShop"
        self.AREA_0_EN = "008"
        self.AREA_1_EN = "009"
        self.AREA_2_EN = "010"
        self.AREA_3_EN = "011"
        self.AREA_FULL_0_EN = ""
        self.AREA_FULL_1_EN = ""
        self.AREA_FULL_2_EN = ""
        self.AREA_FULL_3_EN = ""

        self.PREFECTURE_ID = "1"
        self.EXPIRATION_DATE = "null"
        self.USE_TOKEN = "0"
        self.CONSUME_TOKEN = "0"
        self.DONGLE_FLG = "1"
        self.FORCE_BOOT = "0"


class MuchaUpdateRequest:
    def __init__(self, request: Dict) -> None:
        self.gameVer = request.get("gameVer", "")
        self.gameCd = request.get("gameCd", "")
        self.serialNum = request.get("serialNum", "")
        self.countryCd = request.get("countryCd", "")
        self.placeId = request.get("placeId", "")
        self.storeRouterIp = request.get("storeRouterIp", "")


class MuchaUpdateResponse:
    def __init__(self, game_ver: str, mucha_url: str) -> None:
        self.RESULTS = "001"        
        self.EXE_VER = game_ver

        self.UPDATE_VER_1 = game_ver
        self.UPDATE_URL_1 = f"http://{mucha_url}/updUrl1/"
        self.UPDATE_SIZE_1 = "20"

        self.CHECK_CRC_1 = "0000000000000000"
        self.CHECK_URL_1 = f"http://{mucha_url}/checkUrl/"
        self.CHECK_SIZE_1 = "20"

        self.INFO_SIZE_1 = "0"
        self.COM_SIZE_1 = "0"
        self.COM_TIME_1 = "0"
        self.LAN_INFO_SIZE_1 = "0"

        self.USER_ID = ""
        self.PASSWORD = ""

"""
RESULTS
EXE_VER

UPDATE_VER_%d
UPDATE_URL_%d
UPDATE_SIZE_%d

CHECK_CRC_%d
CHECK_URL_%d
CHECK_SIZE_%d

INFO_SIZE_1
COM_SIZE_1
COM_TIME_1
LAN_INFO_SIZE_1

USER_ID
PASSWORD
"""
class MuchaUpdateResponseStub:
    def __init__(self, game_ver: str) -> None:
        self.RESULTS = "001"
        self.UPDATE_VER_1 = game_ver

class MuchaDownloadStateRequest:
    def __init__(self, request: Dict) -> None:        
        self.gameCd = request.get("gameCd", "")
        self.updateVer = request.get("updateVer", "")
        self.serialNum = request.get("serialNum", "")
        self.fileSize = request.get("fileSize", "")
        self.compFileSize = request.get("compFileSize", "")
        self.boardId = request.get("boardId", "")
        self.placeId = request.get("placeId", "")
        self.storeRouterIp = request.get("storeRouterIp", "")

class MuchaDownloadErrorRequest:
    def __init__(self, request: Dict) -> None:        
        self.gameCd = request.get("gameCd", "")
        self.updateVer = request.get("updateVer", "")
        self.serialNum = request.get("serialNum", "")
        self.downloadUrl = request.get("downloadUrl", "")
        self.errCd = request.get("errCd", "")
        self.errMessage = request.get("errMessage", "")
        self.boardId = request.get("boardId", "")
        self.placeId = request.get("placeId", "")
        self.storeRouterIp = request.get("storeRouterIp", "")

class MuchaRegiAuthRequest:
    def __init__(self, request: Dict) -> None:        
        self.gameCd = request.get("gameCd", "")
        self.serialNum = request.get("serialNum", "") # Encrypted
        self.countryCd = request.get("countryCd", "")
        self.registrationCd = request.get("registrationCd", "")
        self.sendDate = request.get("sendDate", "")
        self.useToken = request.get("useToken", "")
        self.allToken = request.get("allToken", "")
        self.placeId = request.get("placeId", "")
        self.storeRouterIp = request.get("storeRouterIp", "")

class MuchaRegiAuthResponse:
    def __init__(self) -> None:
        self.RESULTS = "001" # 001 = success, 099, 098, 097 = fail, others = fail
        self.ALL_TOKEN = "0" # Encrypted
        self.ADD_TOKEN = "0" # Encrypted

class MuchaTokenStateRequest:
    def __init__(self, request: Dict) -> None:        
        self.gameCd = request.get("gameCd", "")
        self.serialNum = request.get("serialNum", "")
        self.countryCd = request.get("countryCd", "")
        self.useToken = request.get("useToken", "")
        self.allToken = request.get("allToken", "")
        self.placeId = request.get("placeId", "")
        self.storeRouterIp = request.get("storeRouterIp", "")

class MuchaTokenStateResponse:
    def __init__(self) -> None:
        self.RESULTS = "001"

class MuchaTokenMarginStateRequest:
    def __init__(self, request: Dict) -> None:        
        self.gameCd = request.get("gameCd", "")
        self.serialNum = request.get("serialNum", "")
        self.countryCd = request.get("countryCd", "")
        self.placeId = request.get("placeId", "")
        self.limitLowerToken = request.get("limitLowerToken", 0)
        self.limitUpperToken = request.get("limitUpperToken", 0)
        self.settlementMonth = request.get("settlementMonth", 0)

class MuchaTokenMarginStateResponse:
    def __init__(self) -> None:
        self.RESULTS = "001"
        self.LIMIT_LOWER_TOKEN = 0
        self.LIMIT_UPPER_TOKEN = 0
        self.LAST_SETTLEMENT_MONTH = 0
        self.LAST_LIMIT_LOWER_TOKEN = 0
        self.LAST_LIMIT_UPPER_TOKEN = 0
        self.SETTLEMENT_MONTH = 0
