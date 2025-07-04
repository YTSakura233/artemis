import logging, coloredlogs
from typing import Any, Dict, List, Union, Optional
from starlette.requests import Request
from starlette.routing import Route, Mount
from starlette.responses import Response, PlainTextResponse, RedirectResponse
from starlette.applications import Starlette
from logging.handlers import TimedRotatingFileHandler
import jinja2
import bcrypt
import re
import jwt
import yaml
import secrets
import string
from base64 import b64decode
from enum import Enum
from datetime import datetime, timezone
from os import path, environ, mkdir, W_OK, access

from core import CoreConfig, Utils
from core.data import Data
from core.const import AllnetCountryCode

# A-HJ-NP-Z
SERIAL_LETTERS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
ARTEMIS_SERIAL_PREFIX = "A69A"

class PermissionOffset(Enum):
    USER = 0 # Regular user
    USERMOD = 1 # Can moderate other users
    ACMOD = 2 # Can add arcades and cabs
    SYSADMIN = 3 # Can change settings
    # 4 - 6 reserved for future use
    OWNER = 7 # Can do anything

class ShopPermissionOffset(Enum):
    VIEW = 0 # View info and cabs
    BOOKKEEP = 1 # View bookeeping info
    EDITOR = 2 # Can edit name, settings
    # 3 - 6 reserved for future use
    OWNER = 7 # Can do anything

class ShopOwner():
    def __init__(self, usr_id: int = 0, usr_name: str = "", perms: int = 0) -> None:
        self.user_id = usr_id
        self.username = usr_name
        self.permissions = perms

class UserSession():
    def __init__(self, usr_id: int = 0, ip: str = "", perms: int = 0, ongeki_ver: int = 7, chunithm_ver: int = -1, maimai_version: int = -1):
        self.user_id = usr_id
        self.current_ip = ip
        self.permissions = perms
        self.ongeki_version = ongeki_ver
        self.chunithm_version = chunithm_ver
        self.maimai_version = maimai_version

class FrontendServlet():
    def __init__(self, cfg: CoreConfig, config_dir: str) -> None:
        self.config = cfg
        log_fmt_str = "[%(asctime)s] Frontend | %(levelname)s | %(message)s"
        log_fmt = logging.Formatter(log_fmt_str)
        self.environment = jinja2.Environment(loader=jinja2.FileSystemLoader("."))
        self.game_list: Dict[str, Dict[str, Any]] = {}
        self.sn_cvt: Dict[str, str] = {}
        
        self.logger = logging.getLogger("frontend")
        if not hasattr(self.logger, "inited"):
            fileHandler = TimedRotatingFileHandler(
                "{0}/{1}.log".format(self.config.server.log_dir, "frontend"),
                when="d",
                backupCount=10,
            )
            fileHandler.setFormatter(log_fmt)

            consoleHandler = logging.StreamHandler()
            consoleHandler.setFormatter(log_fmt)

            self.logger.addHandler(fileHandler)
            self.logger.addHandler(consoleHandler)

            self.logger.setLevel(cfg.frontend.loglevel)
            coloredlogs.install(
                level=cfg.frontend.loglevel, logger=self.logger, fmt=log_fmt_str
            )

            self.logger.inited = True
        
        games = Utils.get_all_titles()
        for game_dir, game_mod in games.items():
            if hasattr(game_mod, "frontend") and hasattr(game_mod, "index") and hasattr(game_mod, "game_codes"):
                try:
                    if game_mod.index.is_game_enabled(game_mod.game_codes[0], self.config, config_dir):
                        game_fe = game_mod.frontend(cfg, self.environment, config_dir)
                        self.game_list[game_fe.nav_name] = {"url": f"/{game_dir}", "class": game_fe }
                        
                        if hasattr(game_fe, "SN_PREFIX") and hasattr(game_fe, "NETID_PREFIX"):
                            if len(game_fe.SN_PREFIX) == len(game_fe.NETID_PREFIX):
                                for x in range(len(game_fe.SN_PREFIX)):
                                    self.sn_cvt[game_fe.SN_PREFIX[x]] = game_fe.NETID_PREFIX[x]

                except Exception as e:
                    self.logger.error(
                        f"Failed to import frontend from {game_dir} because {e}"
                    )


        self.environment.globals["game_list"] = self.game_list
        self.environment.globals["sn_cvt"] = self.sn_cvt
        self.base = FE_Base(cfg, self.environment)
        self.gate = FE_Gate(cfg, self.environment)
        self.user = FE_User(cfg, self.environment)
        self.system = FE_System(cfg, self.environment)
        self.arcade = FE_Arcade(cfg, self.environment)
        self.machine = FE_Machine(cfg, self.environment)
    
    def get_routes(self) -> List[Route]:        
        g_routes = []
        for nav_name, g_data in self.environment.globals["game_list"].items():
            g_routes.append(Mount(g_data['url'], routes=g_data['class'].get_routes()))
        return [
            Route("/", self.base.render_GET, methods=['GET']),
            Mount("/user", routes=[
                Route("/", self.user.render_GET, methods=['GET']),
                Route("/{user_id:int}", self.user.render_GET, methods=['GET']),
                Route("/update.pw", self.user.render_POST, methods=['POST']),
                Route("/update.name", self.user.update_username, methods=['POST']),
                Route("/edit.card", self.user.edit_card, methods=['POST']),
                Route("/add.card", self.user.add_card, methods=['POST']),
                Route("/logout", self.user.render_logout, methods=['GET']),
            ]),
            Mount("/gate", routes=[
                Route("/", self.gate.render_GET, methods=['GET', 'POST']),
                Route("/gate.login", self.gate.render_login, methods=['POST']),
                Route("/gate.create", self.gate.render_create, methods=['POST']),
                Route("/create", self.gate.render_create_get, methods=['GET']),
            ]),
            Mount("/sys", routes=[
                Route("/", self.system.render_GET, methods=['GET']),
                Route("/logs", self.system.render_logs, methods=['GET']),
                Route("/lookup.user", self.system.lookup_user, methods=['GET']),
                Route("/lookup.shop", self.system.lookup_shop, methods=['GET']),
                Route("/add.user", self.system.add_user, methods=['POST']),
                Route("/add.card", self.system.add_card, methods=['POST']),
                Route("/add.shop", self.system.add_shop, methods=['POST']),
                Route("/add.cab", self.system.add_cab, methods=['POST']),
            ]),
            Mount("/shop", routes=[
                Route("/", self.arcade.render_GET, methods=['GET']),
                Route("/{shop_id:int}", self.arcade.render_GET, methods=['GET']),
                Route("/{shop_id:int}/info.update", self.arcade.update_shop, methods=['POST']),
            ]),
            Mount("/cab", routes=[
                Route("/", self.machine.render_GET, methods=['GET']),
                Route("/{machine_id:int}", self.machine.render_GET, methods=['GET']),
                Route("/{machine_id:int}/info.update", self.machine.update_cab, methods=['POST']),
                Route("/{machine_id:int}/reassign", self.machine.reassign_cab, methods=['POST']),
            ]),
            Mount("/game", routes=g_routes),            
            Route("/robots.txt", self.robots)
        ]
    
    def startup(self) -> None:
        self.config.update({
            "frontend": {
                "standalone": True, 
                "loglevel": CoreConfig.loglevel_to_str(self.config.frontend.loglevel), 
                "secret": self.config.frontend.secret
            }
        })
        self.logger.info(f"Serving {len(self.game_list)} games")
    
    @classmethod    
    async def robots(cls, request: Request) -> PlainTextResponse:
        return PlainTextResponse("User-agent: *\nDisallow: /\n\nUser-agent: AdsBot-Google\nDisallow: /")

class FE_Base():
    """
    A Generic skeleton class that all frontend handlers should inherit from
    Initializes the environment, data, logger, config, and sets isLeaf to true
    It is expected that game implementations of this class overwrite many of these
    """
    def __init__(self, cfg: CoreConfig, environment: jinja2.Environment) -> None:
        self.core_config = cfg
        self.data = Data(cfg)
        self.logger = logging.getLogger("frontend")
        self.environment = environment
        self.nav_name = "index"
    
    async def render_GET(self, request: Request):
        self.logger.debug(f"{Utils.get_ip_addr(request)} -> {request.url}")
        template = self.environment.get_template("core/templates/index.jinja")
        sesh = self.validate_session(request)
        resp = Response(template.render(
            server_name=self.core_config.server.name,
            title=self.core_config.server.name,
            game_list=self.environment.globals["game_list"],
            sesh=vars(sesh) if sesh is not None else vars(UserSession()),
        ), media_type="text/html; charset=utf-8")
        
        if sesh is None:
            resp.delete_cookie("ARTEMIS_SESH")
        return resp
    
    def get_routes(self) -> List[Route]:
        return []
    
    @classmethod
    def test_perm(cls, permission: int, offset: Union[PermissionOffset, ShopPermissionOffset]) -> bool:
        logging.getLogger('frontend').debug(f"{permission} vs {1 << offset.value}")
        return permission & 1 << offset.value == 1 << offset.value
    
    @classmethod
    def test_perm_minimum(cls, permission: int, offset: Union[PermissionOffset, ShopPermissionOffset]) -> bool:
        return permission >= 1 << offset.value
    
    def decode_session(self, token: str) -> UserSession:
        sesh = UserSession()
        if not token: return sesh
        try:
            tk = jwt.decode(token, b64decode(self.core_config.frontend.secret), options={"verify_signature": True}, algorithms=["HS256"])
            sesh.user_id = tk['user_id']
            sesh.current_ip = tk['current_ip']
            sesh.permissions = tk['permissions']
            sesh.chunithm_version = tk['chunithm_version']
            sesh.maimai_version = tk['maimai_version']
            sesh.ongeki_version = tk['ongeki_version']

            if sesh.user_id <= 0:
                self.logger.error("User session failed to validate due to an invalid ID!")
                return UserSession()
            return sesh
        except jwt.ExpiredSignatureError:
            self.logger.error("User session failed to validate due to an expired signature!")
            return sesh
        except jwt.InvalidSignatureError:
            self.logger.error("User session failed to validate due to an invalid signature!")
            return sesh
        except jwt.DecodeError as e:
            self.logger.error(f"User session failed to decode! {e}")
            return sesh
        except jwt.InvalidTokenError as e:
            self.logger.error(f"User session is invalid! {e}")
            return sesh
        except KeyError as e:
            self.logger.error(f"{e} missing from User session!")
            return UserSession()
        except Exception as e:
            self.logger.error(f"Unknown exception occoured when decoding User session! {e}")
            return UserSession()
    
    def validate_session(self, request: Request) -> Optional[UserSession]:
        sesh = request.cookies.get('ARTEMIS_SESH', "")
        if not sesh:
            return None
        
        usr_sesh = self.decode_session(sesh)
        req_ip = Utils.get_ip_addr(request)
        
        if usr_sesh.current_ip != req_ip:
            self.logger.error(f"User session failed to validate due to mismatched IPs! {usr_sesh.current_ip} -> {req_ip}")
            return None

        if usr_sesh.permissions <= 0 or usr_sesh.permissions > 255:
            self.logger.error(f"User session failed to validate due to an invalid permission value! {usr_sesh.permissions}")
            return None

        return usr_sesh
    
    def encode_session(self, sesh: UserSession, exp_seconds: int = 86400) -> str:
        try:
            return jwt.encode({
                "user_id": sesh.user_id,
                "current_ip": sesh.current_ip,
                "permissions": sesh.permissions,
                "ongeki_version": sesh.ongeki_version,
                "chunithm_version": sesh.chunithm_version,
                "maimai_version": sesh.maimai_version,
                "exp": int(datetime.now(tz=timezone.utc).timestamp()) + exp_seconds }, 
                b64decode(self.core_config.frontend.secret), 
                algorithm="HS256"
            )
        except jwt.InvalidKeyError:
            self.logger.error("Failed to encode User session because the secret is invalid!")
            return ""
        except Exception as e:
            self.logger.error(f"Unknown exception occoured when encoding User session! {e}")
            return ""

class FE_Gate(FE_Base):
    async def render_GET(self, request: Request):
        self.logger.debug(f"{Utils.get_ip_addr(request)} -> {request.url.path}")

        usr_sesh = self.validate_session(request)
        if usr_sesh and usr_sesh.user_id > 0:
            return RedirectResponse("/user/", 303)
        
        
        if "e" in request.query_params:
            try:
                err = int(request.query_params.get("e", ["0"])[0])
            except Exception:
                err = 0

        else:
            err = 0

        template = self.environment.get_template("core/templates/gate/gate.jinja")
        resp = Response(template.render(
            title=f"{self.core_config.server.name} | Login Gate",
            error=err,
            sesh=vars(UserSession()),
        ), media_type="text/html; charset=utf-8")
        resp.delete_cookie("ARTEMIS_SESH")
        return resp
    
    async def render_login(self, request: Request):
        ip = Utils.get_ip_addr(request)
        frm = await request.form()
        access_code: str = frm.get("access_code", None)
        if not access_code:
            return RedirectResponse("/gate/?e=1", 303)
        
        passwd: bytes = frm.get("passwd", "").encode()
        if passwd == b"":
            passwd = None

        uid = await self.data.card.get_user_id_from_card(access_code)
        if uid is None:
            user = await self.data.user.get_user_by_username(access_code) # Lookup as username
            if not user:
                self.logger.debug(f"Failed to find user for card/username {access_code}")
                return RedirectResponse("/gate/?e=1", 303)
            
            uid = user['id']

        user = await self.data.user.get_user(uid)
        if user is None:
            self.logger.error(f"Failed to load user {uid}")
            return RedirectResponse("/gate/?e=1", 303)

        if passwd is None:
            sesh = await self.data.user.check_password(uid)

            if sesh is not None:
                return RedirectResponse(f"/gate/create?ac={access_code}", 303)
            
            return RedirectResponse("/gate/?e=1", 303)

        if not await self.data.user.check_password(uid, passwd):
            self.logger.debug(f"Failed password for access code {access_code}")
            return RedirectResponse("/gate/?e=1", 303)

        self.logger.info(f"Successful login of user {uid} at {ip}")

        sesh = UserSession()
        sesh.user_id = uid
        sesh.current_ip = ip
        sesh.permissions = user['permissions']
        
        usr_sesh = self.encode_session(sesh)
        self.logger.debug(f"Created session with JWT {usr_sesh}")
        resp = RedirectResponse("/user/", 303)
        resp.set_cookie("ARTEMIS_SESH", usr_sesh)

        return resp

    async def render_create(self, request: Request):
        ip = Utils.get_ip_addr(request)
        frm = await request.form()
        access_code: str = frm.get("access_code", "")
        username: str = frm.get("username", "")
        email: str = frm.get("email", "")
        passwd: bytes = frm.get("passwd", "").encode()

        if not access_code or not username or not email or not passwd:
            return RedirectResponse("/gate/?e=1", 303)

        uid = await self.data.card.get_user_id_from_card(access_code)
        if uid is None:
            return RedirectResponse("/gate/?e=1", 303)

        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(passwd, salt)

        result = await self.data.user.create_user(
            uid, username, email.lower(), hashed.decode(), 1
        )
        if result is None:
            return RedirectResponse("/gate/?e=3", 303)

        if not await self.data.user.check_password(uid, passwd):
            return RedirectResponse("/gate/", 303)
        
        sesh = UserSession()
        sesh.user_id = uid
        sesh.current_ip = ip
        sesh.permissions = 1
        
        usr_sesh = self.encode_session(sesh)
        self.logger.debug(f"Created session with JWT {usr_sesh}")
        resp = RedirectResponse("/user/", 303)
        resp.set_cookie("ARTEMIS_SESH", usr_sesh)

        return resp

    async def render_create_get(self, request: Request):
        ac = request.query_params.get("ac", "")
        if len(ac) != 20:
            return RedirectResponse("/gate/?e=2", 303)

        card = await self.data.card.get_card_by_access_code(ac)
        if card is None:
            return RedirectResponse("/gate/?e=1", 303)
        
        user = await self.data.user.get_user(card['user'])
        if user is None:
            self.logger.warning(f"Card {ac} exists with no/invalid associated user ID {card['user']}")
            return RedirectResponse("/gate/?e=0", 303)

        if user['password'] is not None:
            return RedirectResponse("/gate/?e=1", 303)

        template = self.environment.get_template("core/templates/gate/create.jinja")
        return Response(template.render(
            title=f"{self.core_config.server.name} | Create User",
            code=ac,
            sesh={"user_id": 0, "permissions": 0},
        ), media_type="text/html; charset=utf-8")

class FE_User(FE_Base):
    async def render_GET(self, request: Request):
        uri = request.url.path
        user_id = request.path_params.get('user_id', None)
        self.logger.debug(f"{Utils.get_ip_addr(request)} -> {uri}")
        template = self.environment.get_template("core/templates/user/index.jinja")

        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            return RedirectResponse("/gate/", 303)
        
        if user_id:
            if not self.test_perm(usr_sesh.permissions, PermissionOffset.USERMOD) and user_id != usr_sesh.user_id:
                self.logger.warning(f"User {usr_sesh.user_id} does not have permission to view user {user_id}")
                return RedirectResponse("/user/", 303)
        
        else:
            user_id = usr_sesh.user_id
        
        user = await self.data.user.get_user(user_id)
        if user is None:
            self.logger.debug(f"User {user_id} not found")
            return RedirectResponse("/user/", 303)
        
        cards = await self.data.card.get_user_cards(user_id)
        
        card_data = []
        arcade_data = []

        managed_arcades = await self.data.arcade.get_arcades_managed_by_user(user_id)
        if managed_arcades:
            for arcade in managed_arcades:
                ac = await self.data.arcade.get_arcade(arcade['id'])
                if ac:
                    arcade_data.append({
                        "id": ac['id'],
                        "name": ac['name'],
                    })

        for c in cards:
            if c['is_locked']:
                status = 'Locked'
            elif c['is_banned']:
                status = 'Banned'
            else:
                status = 'Active'
            
            #idm = c['idm']
            ac = c['access_code']

            if ac.startswith("5"): #or idm is not None:
                c_type = "AmusementIC"
            elif ac.startswith("3"):
                c_type = "Banapass"
            elif ac.startswith("010"):                
                c_type = "Aime" # TODO: Aime verification
            elif ac.startswith("0008"):
                c_type = "Generated AIC"
            else:
                c_type = "Unknown"
            
            card_data.append({
                'access_code': ac, 
                'status': status, 
                'chip_id': c['chip_id'],
                'idm': c['idm'], 
                'type': c_type, 
                "memo": c['memo'],
                "id": c['id'],
            })

        if "e" in request.query_params:
            try:
                err = int(request.query_params.get("e", 0))
            except Exception:
                err = 0

        else:
            err = 0
        
        if "s" in request.query_params:
            try:
                succ = int(request.query_params.get("s", 0))
            except Exception:
                succ = 0

        else:
            succ = 0

        return Response(template.render(
            title=f"{self.core_config.server.name} | Account", 
            sesh=vars(usr_sesh), 
            cards=card_data,
            error=err,
            success=succ,
            username=user['username'],
            arcades=arcade_data
        ), media_type="text/html; charset=utf-8")
    
    async def render_logout(self, request: Request):
        resp = RedirectResponse("/gate/", 303)
        resp.delete_cookie("ARTEMIS_SESH")
        return resp
    
    async def edit_card(self, request: Request) -> RedirectResponse:
        frm = await request.form()
        usr_sesh = self.validate_session(request)
        if not usr_sesh or not self.test_perm(usr_sesh.permissions, PermissionOffset.USERMOD):
            return RedirectResponse("/gate/", 303)

        frm = await request.form()
        cid = frm.get("card_edit_frm_card_id", None)
        if not cid:
            return RedirectResponse("/user/?e=999", 303)
        
        ac = frm.get("card_edit_frm_access_code", None)
        if not ac:
            return RedirectResponse("/user/?e=999", 303)
        
        card = await self.data.card.get_card_by_id(cid)
        if not card:
            return RedirectResponse("/user/?e=2", 303)
        
        if card['user'] != usr_sesh.user_id and not self.test_perm_minimum(usr_sesh.permissions, PermissionOffset.USERMOD):
            return RedirectResponse("/user/?e=11", 303)

        if frm.get("add_memo", None) or frm.get("add_memo", None) == "":
            memo = frm.get("add_memo")
            if len(memo) > 16:
                return RedirectResponse("/user/?e=4", 303)
            await self.data.card.set_memo_by_access_code(ac, memo)

        if False: # Saving this in case I want to allow editing idm/chip ID down the line
            if frm.get("add_felica_idm", None):
                idm = frm.get('add_felica_idm')
                if not all(c in string.hexdigits for c in idm):
                    return RedirectResponse("/user/?e=4", 303)
                await self.data.card.set_idm_by_access_code(ac, idm)

            if frm.get("add_mifare_chip_id", None):
                chip_id: str = frm.get('add_mifare_chip_id')
                if not all(c in string.hexdigits for c in idm):
                    return RedirectResponse("/user/?e=4", 303)
                await self.data.card.set_chip_id_by_access_code(ac, int(chip_id, 16))

        return RedirectResponse("/user/?s=4", 303)
    
    async def add_card(self, request: Request) -> RedirectResponse:
        frm = await request.form()
        card_type = frm.get("card_add_frm_type", None)
        access_code = frm.get("add_access_code", None)
        idm = frm.get("add_idm", None)
        idm_caps = None
        
        usr_sesh = self.validate_session(request)
        if not usr_sesh or not self.test_perm(usr_sesh.permissions, PermissionOffset.USERMOD):
            return RedirectResponse("/gate/", 303)

        if not len(access_code) == 20 or (not access_code.startswith("5") and not access_code.startswith("3") \
            and not access_code.startswith("010") and not access_code.startswith("0008")):
            return RedirectResponse("/user/?e=4", 303)

        if card_type == "0" and access_code.startswith("5") and len(idm) == 16:
            idm_caps = idm.upper()

            if not all([x in string.hexdigits for x in idm_caps]):
                return RedirectResponse("/user/?e=4", 303)
        
        if access_code.startswith("5") and not idm_caps:
            return RedirectResponse("/user/?e=13", 303)

        test = await self.data.card.get_card_by_access_code(access_code)
        if test:
            return RedirectResponse("/user/?e=12", 303)
        
        if idm_caps:
            test = await self.data.card.get_card_by_idm(idm_caps)
            if test and test['user'] != usr_sesh.user_id:
                return RedirectResponse("/user/?e=12", 303)
            
            test = await self.data.card.get_card_by_access_code(self.data.card.to_access_code(idm_caps))
            if test:
                if test['user'] != usr_sesh.user_id:
                    return RedirectResponse("/user/?e=12", 303)

                await self.data.card.set_access_code_by_access_code(test['access_code'], access_code)
                self.logger.info(f"Update card {test['id']} from {test['access_code']} to {access_code} for user {usr_sesh.user_id}")

                await self.data.card.set_idm_by_access_code(access_code, idm_caps)
                self.logger.info(f"Set IDm for card {access_code} to {idm_caps}")
                return RedirectResponse("/user/?s=1", 303)
        
        if card_type == "0" and access_code.startswith("0008"):
            test = await self.data.card.get_card_by_idm(self.data.card.to_idm(access_code))
            if test:
                return RedirectResponse("/user/?e=12", 303)

        new_card = await self.data.card.create_card(usr_sesh.user_id, access_code)
        self.logger.info(f"Created new card {new_card} with access code {access_code} for user {usr_sesh.user_id}")
        
        if idm_caps:
            await self.data.card.set_idm_by_access_code(access_code, idm_caps)
            self.logger.info(f"Set IDm for card {access_code} to {idm_caps}")
        
        return RedirectResponse("/user/?s=1", 303)

    async def render_POST(self, request: Request):
        frm = await request.form()
        usr_sesh = self.validate_session(request)
        if not usr_sesh or not self.test_perm(usr_sesh.permissions, PermissionOffset.USERMOD):
            return RedirectResponse("/gate/", 303)
        
        old_pw: str = frm.get('current_pw', None)
        pw1: str = frm.get('password1', None)
        pw2: str = frm.get('password2', None)

        if old_pw is None or pw1 is None or pw2 is None:
            return RedirectResponse("/user/?e=4", 303)
        
        if pw1 != pw2:
            return RedirectResponse("/user/?e=6", 303)
        
        if not await self.data.user.check_password(usr_sesh.user_id, old_pw.encode()):
            return RedirectResponse("/user/?e=5", 303)
        
        if len(pw1) < 10 or not any(ele.isupper() for ele in pw1) or not any(ele.islower() for ele in pw1) \
            or not any(ele.isdigit() for ele in pw1) or not any(not ele.isalnum() for ele in pw1):
            return RedirectResponse("/user/?e=7", 303)
        
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(pw1.encode(), salt)
        if not await self.data.user.change_password(usr_sesh.user_id, hashed.decode()):
            return RedirectResponse("/gate/?e=1", 303)
        
        return RedirectResponse("/user/?s=1", 303)
        
    async def update_username(self, request: Request):
        frm = await request.form()
        new_name: bytes = frm.get('new_name', "")
        usr_sesh = self.validate_session(request)
        if not usr_sesh or not self.test_perm(usr_sesh.permissions, PermissionOffset.USERMOD):
            return RedirectResponse("/gate/", 303)
        
        if new_name is None or not new_name:
            return RedirectResponse("/user/?e=4", 303)
        
        if len(new_name) > 10:
            return RedirectResponse("/user/?e=8", 303)

        if not await self.data.user.change_username(usr_sesh.user_id, new_name):
            return RedirectResponse("/user/?e=8", 303)
        
        return RedirectResponse("/user/?s=2", 303)

class FE_System(FE_Base):
    async def render_GET(self, request: Request):
        template = self.environment.get_template("core/templates/sys/index.jinja")
        self.logger.debug(f"{Utils.get_ip_addr(request)} -> {request.url.path}")

        usr_sesh = self.validate_session(request)
        if not usr_sesh or not self.test_perm_minimum(usr_sesh.permissions, PermissionOffset.USERMOD):
            return RedirectResponse("/gate/", 303)
        
        if request.query_params.get("e", None):
            err = int(request.query_params.get("e"))
        else:
            err = 0
        
        return Response(template.render(
            title=f"{self.core_config.server.name} | System", 
            sesh=vars(usr_sesh), 
            usrlist=[],
            error = err
        ), media_type="text/html; charset=utf-8")
        
    async def lookup_user(self, request: Request):
        template = self.environment.get_template("core/templates/sys/index.jinja")
        usrlist: List[Dict] = []
        usr_sesh = self.validate_session(request)
        if not usr_sesh or not self.test_perm(usr_sesh.permissions, PermissionOffset.USERMOD):
            return RedirectResponse("/gate/", 303)
        
        uid_search = request.query_params.get("usrId",  None)
        email_search = request.query_params.get("usrEmail", None)
        uname_search = request.query_params.get("usrName", None)

        if uid_search:
            u = await self.data.user.get_user(uid_search)
            if u is not None:
                usrlist.append(u._asdict())

        elif email_search:
            u = await self.data.user.find_user_by_email(email_search)
            if u is not None:
                usrlist.append(u._asdict())

        elif uname_search:
            ul = await self.data.user.find_user_by_username(uname_search)
            for u in ul:
                usrlist.append(u._asdict())

        return Response(template.render(
            title=f"{self.core_config.server.name} | System", 
            sesh=vars(usr_sesh), 
            usrlist=usrlist,
            shoplist=[],
        ), media_type="text/html; charset=utf-8")

    async def lookup_shop(self, request: Request):
        shoplist = []
        template = self.environment.get_template("core/templates/sys/index.jinja")
        
        usr_sesh = self.validate_session(request)
        if not usr_sesh or not self.test_perm(usr_sesh.permissions, PermissionOffset.ACMOD):
            return RedirectResponse("/gate/", 303)
        
        shopid_search = request.query_params.get("shopId",  None)
        sn_search = request.query_params.get("serialNum", None)
        
        if shopid_search:
            if shopid_search.isdigit():
                shopid_search = int(shopid_search)
                try:
                    sinfo = await self.data.arcade.get_arcade(shopid_search)
                except Exception as e:
                    self.logger.error(f"Failed to fetch shop info for shop {shopid_search} in lookup_shop - {e}")
                    sinfo = None
                if sinfo:
                    shoplist.append({
                        "name": sinfo['name'],
                        "id": sinfo['id']
                    })
            
            else:
                return Response(template.render(
                    title=f"{self.core_config.server.name} | System", 
                    sesh=vars(usr_sesh),
                    usrlist=[],
                    shoplist=shoplist,
                    error=4
                ), media_type="text/html; charset=utf-8")
        
        if sn_search:
            sn_search = sn_search.upper().replace("-", "").strip()
            if sn_search.isdigit() and len(sn_search) == 12:
                prefix = sn_search[:4]
                suffix = sn_search[5:]
                
                netid_prefix = self.environment.globals["sn_cvt"].get(prefix, "")                
                sn_search = netid_prefix + suffix
            
            if re.match(r"^AB[DGL]N\d{7}$", sn_search) or re.match(r"^A\d{2}[EX]\d{2}[A-Z]\d{4,8}$", sn_search):
                cabinfo = await self.data.arcade.get_machine(sn_search)
                if cabinfo is None: sinfo = None
                else:
                    sinfo = await self.data.arcade.get_arcade(cabinfo['arcade'])
                if sinfo:
                    shoplist.append({
                        "name": sinfo['name'],
                        "id": sinfo['id']
                    })
            
            else:
                return Response(template.render(
                    title=f"{self.core_config.server.name} | System", 
                    sesh=vars(usr_sesh),
                    usrlist=[],
                    shoplist=shoplist,
                    error=10
                ), media_type="text/html; charset=utf-8")
            
        
        return Response(template.render(
            title=f"{self.core_config.server.name} | System", 
            sesh=vars(usr_sesh), 
            usrlist=[],
            shoplist=shoplist,
        ), media_type="text/html; charset=utf-8")

    async def add_user(self, request: Request):
        template = self.environment.get_template("core/templates/sys/index.jinja")
        
        usr_sesh = self.validate_session(request)
        if not usr_sesh or not self.test_perm(usr_sesh.permissions, PermissionOffset.ACMOD):
            return RedirectResponse("/gate/", 303)
        
        frm = await request.form()
        username = frm.get("userName", None)
        email = frm.get("userEmail", None)
        perm = frm.get("usrPerm", "1")
        passwd = "".join(
            secrets.choice(string.ascii_letters + string.digits) for i in range(20)
        )
        hash = bcrypt.hashpw(passwd.encode(), bcrypt.gensalt())

        if not email:
            return RedirectResponse("/sys/?e=4", 303)

        uid = await self.data.user.create_user(username=username if username else None, email=email, password=hash.decode(), permission=int(perm))
        return Response(template.render(
            title=f"{self.core_config.server.name} | System", 
            sesh=vars(usr_sesh), 
            usradd={"id": uid, "username": username, "password": passwd},
        ), media_type="text/html; charset=utf-8")

    async def add_card(self, request: Request):
        template = self.environment.get_template("core/templates/sys/index.jinja")
        
        usr_sesh = self.validate_session(request)
        if not usr_sesh or not self.test_perm(usr_sesh.permissions, PermissionOffset.ACMOD):
            return RedirectResponse("/gate/", 303)
        
        frm = await request.form()
        userid = frm.get("cardUsr", None)
        access_code = frm.get("cardAc", None)
        idm = frm.get("cardIdm", None)

        if userid is None or access_code is None or not userid.isdigit() or not len(access_code) == 20 or not access_code.isdigit:
            return RedirectResponse("/sys/?e=4", 303)
        
        cardid = await self.data.card.create_card(int(userid), access_code)
        if not cardid:
            return RedirectResponse("/sys/?e=99", 303)

        if idm is not None:
            # TODO: save IDM
            pass
        
        return Response(template.render(
            title=f"{self.core_config.server.name} | System", 
            sesh=vars(usr_sesh), 
            cardadd={"id": cardid, "user": userid, "access_code": access_code},
        ), media_type="text/html; charset=utf-8")

    async def add_shop(self, request: Request):
        template = self.environment.get_template("core/templates/sys/index.jinja")
        
        usr_sesh = self.validate_session(request)
        if not usr_sesh or not self.test_perm(usr_sesh.permissions, PermissionOffset.ACMOD):
            return RedirectResponse("/gate/", 303)
        
        frm = await request.form()
        name = frm.get("shopName", None)
        country = frm.get("shopCountry", "JPN")
        ip = frm.get("shopIp", None)
        owner = frm.get("shopOwner", None)

        acid = await self.data.arcade.create_arcade(name if name else None, name if name else None, country)
        if not acid:
            return RedirectResponse("/sys/?e=99", 303)
        
        await self.data.arcade.set_arcade_vpn_ip(acid, ip if ip else None)

        if owner:
            await self.data.arcade.add_arcade_owner(acid, int(owner), 255)
        
        return Response(template.render(
            title=f"{self.core_config.server.name} | System", 
            sesh=vars(usr_sesh), 
            shopadd={"id": acid},
        ), media_type="text/html; charset=utf-8")

    async def add_cab(self, request: Request):
        template = self.environment.get_template("core/templates/sys/index.jinja")
        
        usr_sesh = self.validate_session(request)
        if not usr_sesh or not self.test_perm(usr_sesh.permissions, PermissionOffset.ACMOD):
            return RedirectResponse("/gate/", 303)

        frm = await request.form()
        shopid = frm.get("cabShop", None)
        serial = frm.get("cabSerial", None)
        game_code = frm.get("cabGame", None)

        if not shopid or not shopid.isdigit():
            return RedirectResponse("/sys/?e=4", 303)
        
        if not serial:
            append = self.data.arcade.get_keychip_suffix(datetime.now().year, datetime.now().month)
            generated = await self.data.arcade.get_num_generated_keychips()
            if not generated:
                generated = 0
            
            rollover = generated // 9999
            serial_num = (generated % 9999) + 1
            serial_letter = SERIAL_LETTERS[rollover]

            serial_dash = self.data.arcade.format_serial(ARTEMIS_SERIAL_PREFIX, 1, serial_letter, serial_num, int(append), True)
            serial = serial_dash.replace("-", "")
        
        cab_id = await self.data.arcade.create_machine(int(shopid), serial, None, game_code if game_code else None)
        if cab_id is None:
            return RedirectResponse("/sys/?e=4", 303)
        
        return Response(template.render(
            title=f"{self.core_config.server.name} | System", 
            sesh=vars(usr_sesh), 
            cabadd={"id": cab_id, "serial": serial_dash},
        ), media_type="text/html; charset=utf-8")

    async def render_logs(self, request: Request):
        template = self.environment.get_template("core/templates/sys/logs.jinja")
        events = []
        
        usr_sesh = self.validate_session(request)
        if not usr_sesh or not self.test_perm(usr_sesh.permissions, PermissionOffset.SYSADMIN):
            return RedirectResponse("/sys/?e=11", 303)
        
        logs = await self.data.base.get_event_log()
        if not logs:
            logs = []
        
        for log in logs:
            evt = log._asdict()
            if not evt['user']: evt["user"] = "NONE"
            if not evt['arcade']: evt["arcade"] = "NONE"
            if not evt['machine']: evt["machine"] = "NONE"
            if not evt['ip']: evt["ip"] = "NONE"
            if not evt['game']: evt["game"] = "NONE"
            if not evt['version']: evt["version"] = "NONE"
            evt['when_logged'] = evt['when_logged'].strftime("%x %X")
            events.append(evt)
        
        return Response(template.render(
            title=f"{self.core_config.server.name} | Event Logs", 
            sesh=vars(usr_sesh), 
            events=events
        ), media_type="text/html; charset=utf-8")
        
class FE_Arcade(FE_Base):
    async def render_GET(self, request: Request):
        template = self.environment.get_template("core/templates/arcade/index.jinja")
        shop_id = request.path_params.get('shop_id', None)
        
        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            return RedirectResponse("/gate/", 303)
 
        if not shop_id:
            return Response('Not Found', status_code=404)

        is_acmod = self.test_perm(usr_sesh.permissions, PermissionOffset.ACMOD)
        if not is_acmod:
            usr_shop_perm = await self.data.arcade.get_manager_permissions(usr_sesh.user_id, shop_id)
            if usr_shop_perm is None or usr_shop_perm == 0:
                self.logger.warning(f"User {usr_sesh.user_id} does not have permission to view shop {shop_id}!")
                return RedirectResponse("/", 303)
        else:
            usr_shop_perm = 15 # view, bookeep, edit
        
        sinfo = await self.data.arcade.get_arcade(shop_id)
        if not sinfo:
            return Response(template.render(
                title=f"{self.core_config.server.name} | Arcade", 
                sesh=vars(usr_sesh),
            ), media_type="text/html; charset=utf-8")
        
        cabs = await self.data.arcade.get_arcade_machines(shop_id)
        cablst = []
        if cabs:
            for x in cabs:
                cablst.append({
                    "id": x['id'],
                    "serial": x['serial'],
                    "game": x['game'],
                })
        
        managers = []
        if (usr_shop_perm & 1 << ShopPermissionOffset.OWNER.value) or is_acmod:
            mgrs = await self.data.arcade.get_arcade_owners(sinfo['id'])
            if mgrs:
                for mgr in mgrs:
                    usr = await self.data.user.get_user(mgr['user'])
                    managers.append({
                        'user': mgr['user'],
                        'name': usr['username'] if usr['username'] else 'No Name Set',
                        'is_view': bool(mgr['permissions'] & 1 << ShopPermissionOffset.VIEW.value),
                        'is_bookkeep': bool(mgr['permissions'] & 1 << ShopPermissionOffset.BOOKKEEP.value),
                        'is_edit': bool(mgr['permissions'] & 1 << ShopPermissionOffset.EDITOR.value),
                        'is_owner': bool(mgr['permissions'] & 1 << ShopPermissionOffset.OWNER.value),
                    })

        if request.query_params.get("e", None):
            err = int(request.query_params.get("e"))
        else:
            err = 0

        if request.query_params.get("s", None):
            suc = int(request.query_params.get("s"))
        else:
            suc = 0

        return Response(template.render(
            title=f"{self.core_config.server.name} | Arcade", 
            sesh=vars(usr_sesh),
            cablst=cablst,
            arcade=sinfo._asdict(),
            can_bookkeep=bool(usr_shop_perm & 1 << ShopPermissionOffset.BOOKKEEP.value) or is_acmod,
            can_edit=bool(usr_shop_perm & 1 << ShopPermissionOffset.EDITOR.value) or is_acmod,
            is_owner=usr_shop_perm & 1 << ShopPermissionOffset.OWNER.value,
            is_acmod=is_acmod,
            managers=managers,
            error=err,
            success=suc
        ), media_type="text/html; charset=utf-8")

    async def update_shop(self, request: Request):
        shop_id = request.path_params.get('shop_id', None)
        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            return RedirectResponse("/gate/", 303)

        sinfo = await self.data.arcade.get_arcade(shop_id)
        
        if not shop_id or not sinfo:
            return RedirectResponse("/", 303)

        if not self.test_perm(usr_sesh.permissions, PermissionOffset.ACMOD):
            usr_shop_perm = await self.data.arcade.get_manager_permissions(usr_sesh.user_id, sinfo['id'])
            if usr_shop_perm is None or usr_shop_perm == 0:
                self.logger.warning(f"User {usr_sesh.user_id} does not have permission to view shop {sinfo['id']}!")
                return RedirectResponse("/", 303)
        
        frm = await request.form()
        new_name = frm.get('name', None)
        new_nickname = frm.get('nickname', None)
        new_country = frm.get('country', None)
        new_region1 = frm.get('region1', None)
        new_region2 = frm.get('region2', None)
        new_tz = frm.get('tz', None)
        new_ip = frm.get('ip', None)

        try:
            AllnetCountryCode(new_country)
        except ValueError:
            new_country = 'JPN'

        did_name = await self.data.arcade.set_arcade_name_nickname(sinfo['id'], new_name if new_name else f'Arcade{sinfo["id"]}', new_nickname if new_nickname else None)
        did_region = await self.data.arcade.set_arcade_region_info(sinfo['id'], new_country, new_region1 if new_region1 else None, new_region2 if new_region2 else None, None, None)
        did_timezone = await self.data.arcade.set_arcade_timezone(sinfo['id'], new_tz if new_tz else None)
        did_vpn = await self.data.arcade.set_arcade_vpn_ip(sinfo['id'], new_ip if new_ip else None)

        if not did_name or not did_region or not did_timezone or not did_vpn:
            self.logger.error(f"Failed to update some shop into: Name: {did_name} Region: {did_region} TZ: {did_timezone} VPN: {did_vpn}")
            return RedirectResponse(f"/shop/{shop_id}?e=15", 303)
        
        return RedirectResponse(f"/shop/{shop_id}?s=1", 303)

class FE_Machine(FE_Base):
    async def render_GET(self, request: Request):
        template = self.environment.get_template("core/templates/machine/index.jinja")
        cab_id = request.path_params.get('machine_id', None)
        
        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            return RedirectResponse("/gate/", 303)

        cab = await self.data.arcade.get_machine(id=cab_id)
        
        if not cab_id or not cab:
            return Response('Not Found', status_code=404)
        
        shop = await self.data.arcade.get_arcade(cab['arcade'])
        
        is_acmod = self.test_perm(usr_sesh.permissions, PermissionOffset.ACMOD)
        if not is_acmod:
            usr_shop_perm = await self.data.arcade.get_manager_permissions(usr_sesh.user_id, shop['id'])
            if usr_shop_perm is None or usr_shop_perm == 0:
                self.logger.warning(f"User {usr_sesh.user_id} does not have permission to view shop {shop['id']}!")
                return RedirectResponse("/", 303)
        else:
            usr_shop_perm = 15 # view, bookeep, edit
        
        if request.query_params.get("e", None):
            err = int(request.query_params.get("e"))
        else:
            err = 0

        if request.query_params.get("s", None):
            suc = int(request.query_params.get("s"))
        else:
            suc = 0

        return Response(template.render(
            title=f"{self.core_config.server.name} | Machine", 
            sesh=vars(usr_sesh),
            arcade=shop._asdict(),
            machine=cab._asdict(),
            can_bookkeep=bool(usr_shop_perm & 1 << ShopPermissionOffset.BOOKKEEP.value) or is_acmod,
            can_edit=bool(usr_shop_perm & 1 << ShopPermissionOffset.EDITOR.value) or is_acmod,
            is_owner=usr_shop_perm & 1 << ShopPermissionOffset.OWNER.value,
            is_acmod=is_acmod,
            error=err,
            success=suc
        ), media_type="text/html; charset=utf-8")
    
    async def update_cab(self, request: Request):
        cab_id = request.path_params.get('machine_id', None)
        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            return RedirectResponse("/gate/", 303)

        cab = await self.data.arcade.get_machine(id=cab_id)
        
        if not cab_id or not cab:
            return RedirectResponse("/", 303)

        if not self.test_perm(usr_sesh.permissions, PermissionOffset.ACMOD):
            usr_shop_perm = await self.data.arcade.get_manager_permissions(usr_sesh.user_id, cab['arcade'])
            if usr_shop_perm is None or usr_shop_perm == 0:
                self.logger.warning(f"User {usr_sesh.user_id} does not have permission to view shop {cab['arcade']}!")
                return RedirectResponse("/", 303)

        frm = await request.form()
        new_game = frm.get('game', None)
        new_country = frm.get('country', None)
        new_tz = frm.get('tz', None)
        new_is_cab = frm.get('is_cab', False) == 'on'
        new_is_ota = frm.get('is_ota', False) == 'on'
        new_memo = frm.get('memo', None)

        try:
            AllnetCountryCode(new_country)
        except ValueError:
            new_country = None
        
        did_game = await self.data.arcade.set_machine_game(cab['id'], new_game if new_game else None)
        did_country = await self.data.arcade.set_machine_country(cab['id'], new_country if new_country else None)
        did_timezone = await self.data.arcade.set_machine_timezone(cab['id'], new_tz if new_tz else None)
        did_real_cab = await self.data.arcade.set_machine_real_cabinet(cab['id'], new_is_cab)
        did_ota = await self.data.arcade.set_machine_can_ota(cab['id'], new_is_ota)
        did_memo = await self.data.arcade.set_machine_memo(cab['id'], new_memo if new_memo else None)

        if not did_game or not did_country or not did_timezone or not did_real_cab or not did_ota or not did_memo:
            self.logger.error(f"Failed to update some shop into: Game: {did_game} Country: {did_country} TZ: {did_timezone} Real: {did_real_cab} OTA: {did_ota} Memo: {did_memo}")
            return RedirectResponse(f"/cab/{cab['id']}?e=15", 303)

        return RedirectResponse(f"/cab/{cab_id}?s=1", 303)

    async def reassign_cab(self, request: Request):
        cab_id = request.path_params.get('machine_id', None)
        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            return RedirectResponse("/gate/", 303)

        cab = await self.data.arcade.get_machine(id=cab_id)
        
        if not cab_id or not cab:
            return RedirectResponse("/", 303)
        
        frm = await request.form()
        new_shop = frm.get('new_arcade', None)

        if not self.test_perm(usr_sesh.permissions, PermissionOffset.ACMOD):
            self.logger.warning(f"User {usr_sesh.user_id} does not have permission to reassign cab {cab['id']} to arcade !")
            return RedirectResponse(f"/cab/{cab_id}?e=11", 303)
        
        new_sinfo = await self.data.arcade.get_arcade(new_shop)
        if not new_sinfo:
            return RedirectResponse(f"/cab/{cab_id}?e=14", 303)
        
        if not await self.data.arcade.set_machine_arcade(cab['id'], new_sinfo['id']):
            return RedirectResponse(f"/cab/{cab_id}?e=99", 303)
        
        return RedirectResponse(f"/cab/{cab_id}?s=2", 303)

cfg_dir = environ.get("ARTEMIS_CFG_DIR", "config")
cfg: CoreConfig = CoreConfig()
if path.exists(f"{cfg_dir}/core.yaml"):
    cfg.update(yaml.safe_load(open(f"{cfg_dir}/core.yaml")))

if not path.exists(cfg.server.log_dir):
    mkdir(cfg.server.log_dir)

if not access(cfg.server.log_dir, W_OK):
    print(
        f"Log directory {cfg.server.log_dir} NOT writable, please check permissions"
    )
    exit(1)

fe = FrontendServlet(cfg, cfg_dir)
app = Starlette(cfg.server.is_develop, fe.get_routes(), on_startup=[fe.startup])
