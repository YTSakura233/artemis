import logging, coloredlogs
from Crypto.Cipher import AES
from typing import Dict, Tuple, Callable, Union, Optional
import asyncio
from logging.handlers import TimedRotatingFileHandler

from core.config import CoreConfig
from core.utils import create_sega_auth_key
from core.data import Data
from .adb_handlers import *

class AimedbServlette():
    request_list: Dict[int, Tuple[Callable[[bytes, int], Union[ADBBaseResponse, bytes]], int, str]] = {}
    def __init__(self, core_cfg: CoreConfig) -> None:        
        self.config = core_cfg        
        self.data = Data(core_cfg)

        self.logger = logging.getLogger("aimedb")
        if not hasattr(self.logger, "initted"):
            log_fmt_str = "[%(asctime)s] Aimedb | %(levelname)s | %(message)s"
            log_fmt = logging.Formatter(log_fmt_str)

            fileHandler = TimedRotatingFileHandler(
                "{0}/{1}.log".format(self.config.server.log_dir, "aimedb"),
                when="d",
                backupCount=10,
            )
            fileHandler.setFormatter(log_fmt)

            consoleHandler = logging.StreamHandler()
            consoleHandler.setFormatter(log_fmt)

            self.logger.addHandler(fileHandler)
            self.logger.addHandler(consoleHandler)

            self.logger.setLevel(self.config.aimedb.loglevel)
            coloredlogs.install(
                level=core_cfg.aimedb.loglevel, logger=self.logger, fmt=log_fmt_str
            )
            self.logger.initted = True

        if not core_cfg.aimedb.key:
            self.logger.error("!!!KEY NOT SET!!!")
            exit(1)

        self.register_handler(0x01, 0x03, self.handle_felica_lookup, 'felica_lookup')
        self.register_handler(0x02, 0x03, self.handle_felica_register, 'felica_register')

        self.register_handler(0x04, 0x06, self.handle_lookup, 'lookup')
        self.register_handler(0x05, 0x06, self.handle_register, 'register')

        self.register_handler(0x07, 0x08, self.handle_status_log, 'status_log')
        self.register_handler(0x09, 0x0A, self.handle_log, 'aime_log')       

        self.register_handler(0x0B, 0x0C, self.handle_campaign, 'campaign')
        self.register_handler(0x0D, 0x0E, self.handle_campaign_clear, 'campaign_clear')

        self.register_handler(0x0F, 0x10, self.handle_lookup_ex, 'lookup_ex')
        self.register_handler(0x11, 0x12, self.handle_felica_lookup_ex, 'felica_lookup_ex')

        self.register_handler(0x13, 0x14, self.handle_log_ex, 'aime_log_ex')
        self.register_handler(0x64, 0x65, self.handle_hello, 'hello')

    def register_handler(self, cmd: int, resp:int, handler: Callable[[bytes, int], Union[ADBBaseResponse, bytes]], name: str) -> None:
        self.request_list[cmd] = (handler, resp, name)
    
    def start(self) -> None:
        self.logger.info(f"Start on port {self.config.aimedb.port}")
        addr = self.config.aimedb.listen_address if self.config.aimedb.listen_address else self.config.server.listen_address
        asyncio.create_task(asyncio.start_server(self.dataReceived, addr, self.config.aimedb.port))
    
    async def dataReceived(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.logger.debug(f"Connection made from {writer.get_extra_info('peername')[0]}")
        while True:
            try:
                data: bytes = await reader.read(4096)
                if len(data) == 0:
                    self.logger.debug("Connection closed")
                    return
                await self.process_data(data, reader, writer)
                await writer.drain()
            except ConnectionResetError as e:
                self.logger.debug("Connection reset, disconnecting")
                return

    async def process_data(self, data: bytes, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> Optional[bytes]:
        addr = writer.get_extra_info('peername')[0]
        cipher = AES.new(self.config.aimedb.key.encode(), AES.MODE_ECB)

        try:
            decrypted = cipher.decrypt(data)
        
        except Exception as e:
            self.logger.error(f"Failed to decrypt {data.hex()} because {e}")
            return

        self.logger.debug(f"{addr} wrote {decrypted.hex()}")

        try:
            head = ADBHeader.from_data(decrypted)
        
        except ADBHeaderException as e:
            self.logger.error(f"Error parsing ADB header: {e}")
            try:    
                encrypted = cipher.encrypt(ADBBaseResponse().make())
                writer.write(encrypted)
                await writer.drain()
                return

            except Exception as e:
                self.logger.error(f"Failed to encrypt default response because {e}")
            
            return

        if head.keychip_id == "ABCD1234567" or head.store_id == 0xfff0:
            self.logger.warning(f"Request from uninitialized AMLib: {vars(head)}")

        if head.cmd == 0x66:
            self.logger.info("Goodbye")
            writer.close()
            return

        handler, resp_code, name = self.request_list.get(head.cmd, (self.handle_default, None, 'default'))

        if resp_code is None:
            self.logger.warning(f"No handler for cmd {hex(head.cmd)}")
        
        elif resp_code > 0:
            self.logger.info(f"{name} from {head.keychip_id} ({head.game_id}) @ {addr}")
        
        resp = await handler(decrypted, resp_code)

        if type(resp) == ADBBaseResponse or issubclass(type(resp), ADBBaseResponse):
            resp_bytes = resp.make()

        elif type(resp) == bytes:
            resp_bytes = resp
        
        elif resp is None: # Nothing to send, probably a goodbye
            self.logger.warning(f"None return by handler for {name}")
            return
        
        else:
            self.logger.error(f"Unsupported type returned by ADB handler for {name}: {type(resp)}")
            raise TypeError(f"Unsupported type returned by ADB handler for {name}: {type(resp)}")

        try:
            encrypted = cipher.encrypt(resp_bytes)
            self.logger.debug(f"Response {resp_bytes.hex()}")
            writer.write(encrypted)

        except Exception as e:
            self.logger.error(f"Failed to encrypt {resp_bytes.hex()} because {e}")
    
    async def handle_default(self, data: bytes, resp_code: int, length: int = 0x20) -> ADBBaseResponse:
        req = ADBHeader.from_data(data)
        return ADBBaseResponse(resp_code, length, 1, req.game_id, req.store_id, req.keychip_id, req.protocol_ver)

    async def handle_hello(self, data: bytes, resp_code: int) -> ADBBaseResponse:
        return await self.handle_default(data, resp_code)

    async def handle_campaign(self, data: bytes, resp_code: int) -> ADBBaseResponse:
        h = ADBHeader.from_data(data)
        if h.protocol_ver >= 0x3030:
            req = h
            resp = ADBCampaignResponse.from_req(req)

        else:
            req = ADBOldCampaignRequest(data)
            
            self.logger.info(f"Legacy campaign request for campaign {req.campaign_id} (protocol version {hex(h.protocol_ver)})")
            resp = ADBOldCampaignResponse.from_req(req.head)
        
        # We don't currently support campaigns
        return resp

    async def handle_lookup(self, data: bytes, resp_code: int) -> ADBBaseResponse:
        req = ADBLookupRequest(data)
        if req.access_code == "00000000000000000000":
            self.logger.warning(f"All-zero access code from {req.head.keychip_id}")
            ret = ADBLookupResponse.from_req(req.head, -1)
            ret.head.status = ADBStatus.BAN_SYS
            return ret
        
        user_id = await self.data.card.get_user_id_from_card(req.access_code)
        is_banned = await self.data.card.get_card_banned(req.access_code)
        is_locked = await self.data.card.get_card_locked(req.access_code)
        
        ret = ADBLookupResponse.from_req(req.head, user_id)
        if is_banned and is_locked:
            ret.head.status = ADBStatus.BAN_SYS_USER
        elif is_banned:
            ret.head.status = ADBStatus.BAN_SYS
        elif is_locked:
            ret.head.status = ADBStatus.LOCK_USER
        
        self.logger.info(
            f"access_code {req.access_code} -> user_id {ret.user_id}"
        )
        
        if user_id and user_id > 0:
            await self.data.card.update_card_last_login(req.access_code)
            if (req.access_code.startswith("010") or req.access_code.startswith("3")) and req.serial_number != 0x04030201: # Default segatools sn
                await self.data.card.set_chip_id_by_access_code(req.access_code, req.serial_number)
                self.logger.info(f"Attempt to set chip id to {req.serial_number:08X} for access code {req.access_code}")
        return ret

    async def handle_lookup_ex(self, data: bytes, resp_code: int) -> ADBBaseResponse:
        req = ADBLookupRequest(data)
        if req.access_code == "00000000000000000000":
            self.logger.warning(f"All-zero access code from {req.head.keychip_id}")
            ret = ADBLookupExResponse.from_req(req.head, -1)
            ret.head.status = ADBStatus.BAN_SYS
            return ret
        
        user_id = await self.data.card.get_user_id_from_card(req.access_code)

        is_banned = await self.data.card.get_card_banned(req.access_code)
        is_locked = await self.data.card.get_card_locked(req.access_code)

        ret = ADBLookupExResponse.from_req(req.head, user_id)
        if is_banned and is_locked:
            ret.head.status = ADBStatus.BAN_SYS_USER
        elif is_banned:
            ret.head.status = ADBStatus.BAN_SYS
        elif is_locked:
            ret.head.status = ADBStatus.LOCK_USER

        self.logger.info(
            f"access_code {req.access_code} -> user_id {ret.user_id}"
        )

        if user_id and user_id > 0 and self.config.aimedb.id_secret:
            auth_key = create_sega_auth_key(user_id, req.head.game_id, req.head.store_id, req.head.keychip_id, self.config.aimedb.id_secret, self.config.aimedb.id_lifetime_seconds)
            if auth_key is not None:
                auth_key_extra_len = 256 - len(auth_key)
                auth_key_full = auth_key.encode() + (b"\0" * auth_key_extra_len)
                self.logger.debug(f"Generated auth token {auth_key}")
                ret.auth_key = auth_key_full

        if user_id and user_id > 0:
            await self.data.card.update_card_last_login(req.access_code)
        return ret

    async def handle_felica_lookup(self, data: bytes, resp_code: int) -> bytes:
        """
        On official, the IDm is used as a key to look up the stored access code in a large
        database. We do not have access to that database so we have to make due with what we got.
        Interestingly, namco games are able to read S_PAD0 and send the server the correct access
        code, but aimedb doesn't. Until somebody either enters the correct code manually, or scans
        on a game that reads it correctly from the card, this will have to do. It's the same conversion
        used on the big boy networks.
        """
        req = ADBFelicaLookupRequest(data)
        idm = req.idm.zfill(16)
        if idm == "0000000000000000":
            self.logger.warning(f"All-zero IDm from {req.head.keychip_id}")
            ret = ADBFelicaLookupResponse.from_req(req.head, "00000000000000000000")
            ret.head.status = ADBStatus.BAN_SYS
            return ret

        card = await self.data.card.get_card_by_idm(idm)
        if not card:
            ac = self.data.card.to_access_code(idm)
            test = await self.data.card.get_card_by_access_code(ac)
            if test:
                await self.data.card.set_idm_by_access_code(ac, idm)
        
        else:
            ac = card['access_code']
        
        self.logger.info(
            f"idm {idm} pmm {req.pmm.zfill(16)} -> access_code {ac}"
        )
        return ADBFelicaLookupResponse.from_req(req.head, ac)

    async def handle_felica_register(self, data: bytes, resp_code: int) -> bytes:
        """
        Used to register felica moble access codes. Will never be used on our network
        because we don't implement felica_lookup properly.
        """
        req = ADBFelicaLookupRequest(data)
        idm = req.idm.zfill(16)
        
        if idm == "0000000000000000":
            self.logger.warning(f"All-zero IDm from {req.head.keychip_id}")
            ret = ADBFelicaLookupResponse.from_req(req.head, "00000000000000000000")
            ret.head.status = ADBStatus.BAN_SYS
            return ret
        
        ac = self.data.card.to_access_code(req.idm)
        
        if self.config.server.allow_user_registration:
            user_id = await self.data.user.create_user()

            if user_id is None:
                self.logger.error("Failed to register user!")
                user_id = -1

            else:
                card_id = await self.data.card.create_card(user_id, ac)

                if card_id is None:
                    self.logger.error("Failed to register card!")
                    user_id = -1

            self.logger.info(
                f"Register access code {ac} (IDm: {req.idm} PMm: {req.pmm}) -> user_id {user_id}"
            )

        else:
            self.logger.info(
                f"Registration blocked!: access code {ac} (IDm: {req.idm} PMm: {req.pmm})"
            )

        if user_id > 0:
            await self.data.card.update_card_last_login(ac)
        return ADBFelicaLookupResponse.from_req(req.head, ac)

    async def handle_felica_lookup_ex(self, data: bytes, resp_code: int) -> bytes:
        req = ADBFelicaLookupExRequest(data)
        user_id = None
        idm = req.idm.zfill(16)
        
        if idm == "0000000000000000":
            self.logger.warning(f"All-zero IDm from {req.head.keychip_id}")
            ret = ADBFelicaLookupExResponse.from_req(req.head, -1, "00000000000000000000")
            ret.head.status = ADBStatus.BAN_SYS
            return ret
        
        card = await self.data.card.get_card_by_idm(idm)
        if not card:
            access_code = self.data.card.to_access_code(idm)
            card = await self.data.card.get_card_by_access_code(access_code)
            if card:
                user_id = card['user']
                await self.data.card.set_idm_by_access_code(access_code, idm)
        
        else:
            user_id = card['user']
            access_code = card['access_code']

        if user_id is None:
            user_id = -1

        self.logger.info(
            f"idm {idm} dfc {req.dfc} -> access_code {access_code} user_id {user_id}"
        )

        resp = ADBFelicaLookupExResponse.from_req(req.head, user_id, access_code)
        
        if user_id > 0:
            if card['is_banned'] and card['is_locked']:
                resp.head.status = ADBStatus.BAN_SYS_USER
            elif card['is_banned']:
                resp.head.status = ADBStatus.BAN_SYS
            elif card['is_locked']:
                resp.head.status = ADBStatus.LOCK_USER

        if user_id and user_id > 0 and self.config.aimedb.id_secret:
            auth_key = create_sega_auth_key(user_id, req.head.game_id, req.head.store_id, req.head.keychip_id, self.config.aimedb.id_secret, self.config.aimedb.id_lifetime_seconds)
            if auth_key is not None:
                auth_key_extra_len = 256 - len(auth_key)
                auth_key_full = auth_key.encode() + (b"\0" * auth_key_extra_len)
                self.logger.debug(f"Generated auth token {auth_key}")
                resp.auth_key = auth_key_full
        
        if user_id and user_id > 0:
            await self.data.card.update_card_last_login(access_code)
        return resp

    async def handle_campaign_clear(self, data: bytes, resp_code: int) -> ADBBaseResponse:
        req = ADBCampaignClearRequest(data)

        resp = ADBCampaignClearResponse.from_req(req.head)

        # We don't support campaign stuff
        return resp

    async def handle_register(self, data: bytes, resp_code: int) -> bytes:
        req = ADBLookupRequest(data)
        user_id = -1
        
        if req.access_code == "00000000000000000000":
            self.logger.warning(f"All-zero access code from {req.head.keychip_id}")
            ret = ADBLookupResponse.from_req(req.head, -1)
            ret.head.status = ADBStatus.BAN_SYS
            return ret

        if self.config.server.allow_user_registration:
            user_id = await self.data.user.create_user()

            if user_id is None:
                self.logger.error("Failed to register user!")
                user_id = -1

            else:
                card_id = await self.data.card.create_card(user_id, req.access_code)

                if card_id is None:
                    self.logger.error("Failed to register card!")
                    user_id = -1

            self.logger.info(
                f"Register access code {req.access_code} -> user_id {user_id}"
            )

        else:
            self.logger.info(
                f"Registration blocked!: access code {req.access_code}"
            )
        
        if user_id > 0:
            if (req.access_code.startswith("010") or req.access_code.startswith("3")) and req.serial_number != 0x04030201: # Default segatools sn:
                await self.data.card.set_chip_id_by_access_code(req.access_code, req.serial_number)
                self.logger.info(f"Attempt to set chip id to {req.serial_number} for access code {req.access_code}")
            
            elif req.access_code.startswith("0008"):
                idm = self.data.card.to_idm(req.access_code)
                await self.data.card.set_idm_by_access_code(req.access_code, idm)
                self.logger.info(f"Attempt to set IDm to {idm} for access code {req.access_code}")

        resp = ADBLookupResponse.from_req(req.head, user_id)
        if resp.user_id <= 0:
            resp.head.status = ADBStatus.BAN_SYS # Closest we can get to a "You cannot register"

        else:
            await self.data.card.update_card_last_login(req.access_code)

        return resp

    # TODO: Save these in some capacity, as deemed relevant
    async def handle_status_log(self, data: bytes, resp_code: int) -> bytes:
        req = ADBStatusLogRequest(data)
        self.logger.info(f"User {req.aime_id} logged {req.status.name} event")
        return ADBBaseResponse(resp_code, 0x20, 1, req.head.game_id, req.head.store_id, req.head.keychip_id, req.head.protocol_ver)

    async def handle_log(self, data: bytes, resp_code: int) -> bytes:
        req = ADBLogRequest(data)
        self.logger.info(f"User {req.aime_id} logged {req.status.name} event, credit_ct: {req.credit_ct} bet_ct: {req.bet_ct} won_ct: {req.won_ct}")
        return ADBBaseResponse(resp_code, 0x20, 1, req.head.game_id, req.head.store_id, req.head.keychip_id, req.head.protocol_ver)

    async def handle_log_ex(self, data: bytes, resp_code: int) -> bytes:
        req = ADBLogExRequest(data)
        strs = []
        self.logger.info(f"Recieved {req.num_logs} or {len(req.logs)} logs")
        
        for x in range(req.num_logs):
            self.logger.debug(f"User {req.logs[x].aime_id} logged {req.logs[x].status.name} event, credit_ct: {req.logs[x].credit_ct} bet_ct: {req.logs[x].bet_ct} won_ct: {req.logs[x].won_ct}")
        return ADBLogExResponse.from_req(req.head)

