from enum import Enum


class MainboardPlatformCodes(Enum):
    RINGEDGE = "AAL"
    RINGEDGE2 = "AAS"
    RINGWIDE = "AAM"
    NU = "AAV"
    NUSX = "AAW"
    ALLS = "ACA"
    #ALLS_UX = "ACAE"
    #ALLS_HX = "ACAX"


class MainboardRevisions(Enum):
    RINGEDGE = 1
    RINGEDGE2 = 2

    RINGWIDE = 1

    NU1 = 1
    NU11 = 11
    NU2 = 12

    NUSX = 1
    NUSX11 = 11

    ALLS_UX = 1
    ALLS_HX = 11
    ALLS_UX2 = 2
    ALLS_HX2 = 12


class KeychipPlatformsCodes(Enum):
    RING = "72"
    NU = ("60", "61", "69")
    ALLS = "63"


class AllnetCountryCode(Enum):
    JAPAN = "JPN"
    UNITED_STATES = "USA"
    HONG_KONG = "HKG"
    SINGAPORE = "SGP"
    SOUTH_KOREA = "KOR"
    TAIWAN = "TWN"
    CHINA = "CHN"
    AUSTRALIA = "AUS"
    INDONESIA = "IDN"
    MYANMAR = "MMR"
    MALAYSIA = "MYS"
    NEW_ZEALAND = "NZL"
    PHILIPPINES = "PHL"
    THAILAND = "THA"
    VIETNAM = "VNM"


class AllnetJapanRegionId(Enum):
    NONE = 0
    AICHI = 1
    AOMORI = 2
    AKITA = 3
    ISHIKAWA = 4
    IBARAKI = 5
    IWATE = 6
    EHIME = 7
    OITA = 8
    OSAKA = 9
    OKAYAMA = 10
    OKINAWA = 11
    KAGAWA = 12
    KAGOSHIMA = 13
    KANAGAWA = 14
    GIFU = 15
    KYOTO = 16
    KUMAMOTO = 17
    GUNMA = 18
    KOCHI = 19
    SAITAMA = 20
    SAGA = 21
    SHIGA = 22
    SHIZUOKA = 23
    SHIMANE = 24
    CHIBA = 25
    TOKYO = 26
    TOKUSHIMA = 27
    TOCHIGI = 28
    TOTTORI = 29
    TOYAMA = 30
    NAGASAKI = 31
    NAGANO = 32
    NARA = 33
    NIIGATA = 34
    HYOGO = 35
    HIROSHIMA = 36
    FUKUI = 37
    FUKUOKA = 38
    FUKUSHIMA = 39
    HOKKAIDO = 40
    MIE = 41
    MIYAGI = 42
    MIYAZAKI = 43
    YAMAGATA = 44
    YAMAGUCHI = 45
    YAMANASHI = 46
    WAKAYAMA = 47
