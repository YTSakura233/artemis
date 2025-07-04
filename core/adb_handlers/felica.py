from construct import Struct, Int32sl, Padding, Int8ub, Int16sl
from typing import Union
from .base import *

class ADBFelicaLookupRequest(ADBBaseRequest):
    def __init__(self, data: bytes) -> None:
        super().__init__(data)
        idm, pmm = struct.unpack_from(">QQ", data, 0x20)
        self.idm = hex(idm)[2:].upper()
        self.pmm = hex(pmm)[2:].upper()

class ADBFelicaLookupResponse(ADBBaseResponse):
    def __init__(self, access_code: str = None, idx: int = 0, game_id: str = "SXXX", store_id: int = 1, keychip_id: str = "A69E01A8888", code: int = 0x03, length: int = 0x30, status: int = 1) -> None:
        super().__init__(code, length, status, game_id, store_id, keychip_id)
        self.access_code = access_code if access_code is not None else "00000000000000000000"
        self.idx = idx
    
    @classmethod
    def from_req(cls, req: ADBHeader, access_code: str = None, idx: int = 0) -> "ADBFelicaLookupResponse":
        c = cls(access_code, idx, req.game_id, req.store_id, req.keychip_id)
        c.head.protocol_ver = req.protocol_ver
        return c
    
    def make(self) -> bytes:        
        resp_struct = Struct(
            "felica_idx" / Int32ul,
            "access_code" / Int8ub[10],
            Padding(2)
        ).build(dict(
            felica_idx = self.idx,
            access_code = bytes.fromhex(self.access_code)
        ))

        self.head.length = HEADER_SIZE + len(resp_struct)

        return self.head.make() + resp_struct

class ADBFelicaLookupExRequest(ADBBaseRequest):
    def __init__(self, data: bytes) -> None:
        super().__init__(data)
        self.random = struct.unpack_from("<16s", data, 0x20)[0]
        idm, dfc, self.arbitrary = struct.unpack_from(">QH6s", data, 0x30)
        self.card_key_ver, self.write_ct, self.maca, company, fw_ver, self.dfc = struct.unpack_from("<16s16sQccH", data, 0x40)
        self.idm = hex(idm)[2:].upper()
        self.dfc = hex(dfc)[2:].upper()
        self.company = CompanyCodes(int.from_bytes(company, 'little'))
        self.fw_ver = ReaderFwVer.from_byte(fw_ver)

class ADBFelicaLookupExResponse(ADBBaseResponse):
    def __init__(self, user_id: Union[int, None] = None, access_code: Union[str, None] = None, game_id: str = "SXXX", store_id: int = 1, keychip_id: str = "A69E01A8888", code: int = 0x12, length: int = 0x130, status: int = 1) -> None:
        super().__init__(code, length, status, game_id, store_id, keychip_id)
        self.user_id = user_id if user_id is not None else -1
        self.access_code = access_code if access_code is not None else "00000000000000000000"
        self.company = CompanyCodes.SEGA
        self.portal_status = PortalRegStatus.NO_REG
        self.auth_key = [0] * 256

    @classmethod
    def from_req(cls, req: ADBHeader, user_id: Union[int, None] = None, access_code: Union[str, None] = None) -> "ADBFelicaLookupExResponse":
        c = cls(user_id, access_code, req.game_id, req.store_id, req.keychip_id)
        c.head.protocol_ver = req.protocol_ver
        return c

    def make(self) -> bytes:        
        resp_struct = Struct(
            "user_id" / Int32sl,
            "relation1" / Int32sl,
            "relation2" / Int32sl,
            "access_code" / Int8ub[10],
            "portal_status" / Int8ub,
            "company_code" / Int8ub,
            Padding(8),
            "auth_key" / Int8ub[256],
        ).build(dict(
            user_id = self.user_id,
            relation1 = -1, # Unsupported
            relation2 = -1, # Unsupported
            access_code = bytes.fromhex(self.access_code),
            portal_status = self.portal_status.value,
            company_code = self.company.value,
            auth_key = self.auth_key
        ))

        self.head.length = HEADER_SIZE + len(resp_struct)

        return self.head.make() + resp_struct
