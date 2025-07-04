from starlette.routing import Route
import yaml
import logging, coloredlogs
from logging.handlers import TimedRotatingFileHandler
import logging
import json
from hashlib import md5
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from typing import Dict, Tuple, List
from os import path
import traceback
import sys

from core import CoreConfig, Utils
from core.data import Data
from core.title import BaseServlet
from .config import WaccaConfig
from .config import WaccaConfig
from .const import WaccaConstants
from .reverse import WaccaReverse
from .lilyr import WaccaLilyR
from .lily import WaccaLily
from .s import WaccaS
from .base import WaccaBase
from .handlers.base import BaseResponse, BaseRequest
from .handlers.helpers import Version

class WaccaServlet(BaseServlet):
    def __init__(self, core_cfg: CoreConfig, cfg_dir: str) -> None:
        self.core_cfg = core_cfg
        self.game_cfg = WaccaConfig()
        if path.exists(f"{cfg_dir}/{WaccaConstants.CONFIG_NAME}"):
            self.game_cfg.update(
                yaml.safe_load(open(f"{cfg_dir}/{WaccaConstants.CONFIG_NAME}"))
            )
        self.data = Data(core_cfg)

        self.versions = [
            WaccaBase(core_cfg, self.game_cfg),
            WaccaS(core_cfg, self.game_cfg),
            WaccaLily(core_cfg, self.game_cfg),
            WaccaLilyR(core_cfg, self.game_cfg),
            WaccaReverse(core_cfg, self.game_cfg),
        ]

        self.logger = logging.getLogger("wacca")
        log_fmt_str = "[%(asctime)s] Wacca | %(levelname)s | %(message)s"
        log_fmt = logging.Formatter(log_fmt_str)
        fileHandler = TimedRotatingFileHandler(
            "{0}/{1}.log".format(self.core_cfg.server.log_dir, "wacca"),
            encoding="utf8",
            when="d",
            backupCount=10,
        )

        fileHandler.setFormatter(log_fmt)

        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(log_fmt)

        self.logger.addHandler(fileHandler)
        self.logger.addHandler(consoleHandler)

        self.logger.setLevel(self.game_cfg.server.loglevel)
        coloredlogs.install(
            level=self.game_cfg.server.loglevel, logger=self.logger, fmt=log_fmt_str
        )
    
    def get_routes(self) -> List[Route]:
        return [
            Route("/WaccaServlet/api/{api:str}/{endpoint:str}", self.render_POST, methods=['POST']),
            Route("/WaccaServlet/api/{api:str}/{branch:str}/{endpoint:str}", self.render_POST, methods=['POST']),
        ]

    @classmethod
    def is_game_enabled(cls, game_code: str, core_cfg: CoreConfig, cfg_dir: str) -> bool:
        game_cfg = WaccaConfig()
        if path.exists(f"{cfg_dir}/{WaccaConstants.CONFIG_NAME}"):
            game_cfg.update(
                yaml.safe_load(open(f"{cfg_dir}/{WaccaConstants.CONFIG_NAME}"))
            )

        if not game_cfg.server.enable:
            return False

        return True
    
    def get_allnet_info(self, game_code: str, game_ver: int, keychip: str) -> Tuple[str, str]:
        if not self.core_cfg.server.is_using_proxy and Utils.get_title_port(self.core_cfg) != 80:
            return (
                f"http://{self.core_cfg.server.hostname}:{Utils.get_title_port(self.core_cfg)}/WaccaServlet",
                self.core_cfg.server.hostname,
            )

        return (f"http://{self.core_cfg.server.hostname}/WaccaServlet", self.core_cfg.server.hostname)
    
    async def render_POST(self, request: Request) -> bytes:
        def end(resp: Dict) -> bytes:
            hash = md5(json.dumps(resp, ensure_ascii=False).encode()).digest()
            return Response(content=json.dumps(resp, ensure_ascii=False), headers={"X-Wacca-Hash": hash.hex()})

        api = request.path_params.get('api', '')
        branch = request.path_params.get('branch', '')
        endpoint = request.path_params.get('endpoint', '')
        client_ip = Utils.get_ip_addr(request)
        bod = await request.body()
        
        if branch:
            url_path = f"{api}/{branch}/{endpoint}"
            func_to_find = f"handle_{api}_{branch}_{endpoint}_request"

        else:
            url_path = f"{api}/{endpoint}"
            func_to_find = f"handle_{api}_{endpoint}_request"

        try:
            req_json = json.loads(bod)
            version_full = Version(req_json["appVersion"])
            req = BaseRequest(req_json)
        
        except KeyError as e:
            self.logger.error(
                f"Failed to parse request to {bod} -> Missing required value {e}"
            )
            resp = BaseResponse()
            resp.status = 1
            resp.message = "不正なリクエスト エラーです"
            return end(resp.make())
        
        except Exception as e:
            self.logger.error(
                f"Failed to parse request to {url_path} -> {bod} -> {e}"
            )
            resp = BaseResponse()
            resp.status = 1
            resp.message = "不正なリクエスト エラーです"
            return end(resp.make())
        
        if not self.core_cfg.server.allow_unregistered_serials:
            mech = await self.data.arcade.get_machine(req.chipId)
            if not mech:
                self.logger.error(f"Blocked request from unregistered serial {req.chipId} to {url_path}")
                resp = BaseResponse()
                resp.status = 1
                resp.message = "機械エラーです"
                return end(resp.make())

        ver_search = int(version_full)

        if ver_search < 15000:
            internal_ver = WaccaConstants.VER_WACCA

        elif ver_search >= 15000 and ver_search < 20000:
            internal_ver = WaccaConstants.VER_WACCA_S

        elif ver_search >= 20000 and ver_search < 25000:
            internal_ver = WaccaConstants.VER_WACCA_LILY

        elif ver_search >= 25000 and ver_search < 30000:
            internal_ver = WaccaConstants.VER_WACCA_LILY_R

        elif ver_search >= 30000:
            internal_ver = WaccaConstants.VER_WACCA_REVERSE

        else:
            self.logger.warning(
                f"Unsupported version ({req.appVersion}) request {url_path} - {req_json}"
            )
            resp = BaseResponse()
            resp.status = 1
            resp.message = "不正なアプリバージョンエラーです"
            return end(resp.make())

        self.logger.info(
            f"v{req.appVersion} {url_path} request from {client_ip} with chipId {req.chipId}"
        )
        self.logger.debug(req_json)

        if not hasattr(self.versions[internal_ver], func_to_find):
            self.logger.warning(
                f"{req_json['appVersion']} has no handler for {func_to_find}"
            )
            resp = BaseResponse().make()
            return end(resp)

        try:
            handler = getattr(self.versions[internal_ver], func_to_find)
            resp = await handler(req_json)

            self.logger.debug(f"{req.appVersion} response {resp}")
            return end(resp)

        except Exception as e:
            self.logger.error(
                f"{req.appVersion} Error handling method {url_path} -> {e}"
            )
            if self.logger.level == logging.DEBUG:
                tp, val, tb  = sys.exc_info()
                traceback.print_exception(tp, val, tb, limit=3)
                with open("{0}/{1}.log".format(self.core_cfg.server.log_dir, "wacca"), "a") as f:
                    traceback.print_exception(tp, val, tb, limit=3, file=f)

            resp = BaseResponse()
            resp.status = 1
            resp.message = "A server error occoured."
            return end(resp.make())
