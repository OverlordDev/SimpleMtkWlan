#!/usr/bin/env python3
"""Статическая проверка старта AirportMtkWlan (не требует macOS и компилятора).

Проверяет то, что в рабочей Sequoia-сборке (laobamac/itlwm, ветка AIRPORT_WCL, 15.8 / 24H23) обязательно
и что в этом порте раньше отсутствовало; каждое правило привязано к причине. Запуск:

    python3 -I experimental/check_airport_start.py [корень_репозитория]

Код возврата 0 - все правила выполнены, 1 - нет. build_airport.sh вызывает этот скрипт перед компиляцией.
Правило считается работающим только после того, как его намеренно сломали и увидели падение
(см. experimental/check_airport_start_selftest.py).
"""
import os
import re
import sys


def strip_comments(s):
    s = re.sub(r"/\*.*?\*/", " ", s, flags=re.S)
    return re.sub(r"//[^\n]*", " ", s)


def strip_strings(s):
    """Содержимое строковых литералов вырезается: токены в сообщениях XYLog не должны засчитываться как код."""
    return re.sub(r'"(?:\\.|[^"\\\n])*"', '""', s)


def read(root, rel):
    with open(os.path.join(root, rel), encoding="utf-8") as f:
        return f.read()


def func_body(src, header_regex):
    """Тело функции от строки заголовка до парной закрывающей скобки (комментарии уже вырезаны)."""
    m = re.search(header_regex, src)
    if not m:
        return None
    i = src.find("{", m.end())
    if i < 0:
        return None
    depth = 0
    for j in range(i, len(src)):
        if src[j] == "{":
            depth += 1
        elif src[j] == "}":
            depth -= 1
            if depth == 0:
                return src[i:j + 1]
    return None


class Checker:
    def __init__(self):
        self.errors = []
        self.passed = 0

    def ok(self, cond, rule, why):
        if cond:
            self.passed += 1
        else:
            self.errors.append("НАРУШЕНО: %s\n    почему важно: %s" % (rule, why))


def hexval(s):
    return int(s, 16)


def check(root):
    c = Checker()
    ctl_rel = "experimental/AirportMtkWlan/AirportMtkWlan.cpp"
    hpp_rel = "experimental/AirportMtkWlan/AirportMtkWlan.hpp"
    sw_rel = "experimental/AirportMtkWlan/AirportMtkWlanSkywalkInterface.cpp"
    eth_rel = "experimental/AirportMtkWlan/AirportMtkWlanEthernetInterface.cpp"
    inc = "experimental/include/Sequoia/"

    ctl_s = strip_comments(read(root, ctl_rel))     # со строками: нужен ключ "MtkDelaySec"
    ctl = strip_strings(ctl_s)
    hpp = strip_strings(strip_comments(read(root, hpp_rel)))
    sw = strip_strings(strip_comments(read(root, sw_rel)))
    eth = strip_strings(strip_comments(read(root, eth_rel)))

    # ---- 1. порядок start() ------------------------------------------------------------------
    start = func_body(ctl, r"bool\s+AirportMtkWlan::start\s*\(\s*IOService\s*\*\s*provider\s*\)")
    c.ok(start is not None, "AirportMtkWlan::start найден", "без тела start() остальные проверки бессмысленны")
    if start is not None:
        order = [
            ("initCCLogs()", "CC-логгеры и fault reporter нужны Family до IO80211Controller::start() (иначе паника)"),
            ("super::start(provider)", "базовый start контроллера"),
            ("fHalService->attach(pciNub)", "MAC и прошивка должны быть известны до инициализации интерфейса"),
            ("fNetIf->initWithController(this)", "двойная инициализация интерфейса (см. SkywalkInterface.cpp)"),
            ("fNetIf->attach(this)", "attach интерфейса к контроллеру"),
            ("attachInterface(fNetIf, this)", "регистрация Skywalk-интерфейса в Family"),
            ("IONetworkController::attachInterface(", "создание BSD-интерфейса"),
            ("fNetIf->initRegistrationInfo(", "заполнение локальной RegistrationInfo"),
            ("expNet->fRegistrationInfo =", "ExpansionData сети: start() Family читает это поле"),
            ("expEth->fRegistrationInfo =", "ExpansionData Ethernet: start() Family читает это поле"),
            ("fNetIf->deferBSDAttach(true)", "отложенная регистрация BSD, как в рабочей сборке"),
            ("fNetIf->start(this)", "запуск интерфейса Family строго после заполнения ExpansionData"),
        ]
        pos = -1
        for token, why in order:
            p = start.find(token, pos + 1)
            c.ok(p >= 0, "в start() есть и стоит по порядку: %s" % token, why)
            if p >= 0:
                pos = p
            else:
                break
        d = start.find("fNetIf->deferBSDAttach(true)")
        early = [m.start() for m in re.finditer(re.escape("fNetIf->start(this)"), start) if d < 0 or m.start() < d]
        c.ok(not early, "fNetIf->start(this) нигде не вызывается раньше заполнения ExpansionData",
             "ранний вызов даёт то же разыменование NULL внутри Family")
        c.ok(re.search(r"IONetworkController::attachInterface\(\s*\(IONetworkInterface\s*\*\*\)\s*&bsdInterface\s*,\s*false\s*\)", start) is not None,
             "BSD-интерфейс присоединяется с doRegister=false",
             "рабочая сборка регистрирует BSD-интерфейс отдельно, после старта Skywalk-интерфейса (finishStart)")
        c.ok("mtkLooksLikeKernelPtr(expNet)" in start and "mtkLooksLikeKernelPtr(expEth)" in start,
             "указатели ExpansionData проверяются перед записью",
             "при несовпадении смещения ABI запись по чужому адресу даёт панику без диагностики")
        start_s = func_body(ctl_s, r"bool\s+AirportMtkWlan::start\s*\(\s*IOService\s*\*\s*provider\s*\)") or ""
        c.ok("MtkDelaySec" in start_s and re.search(r"delaySec\s*==\s*0", start) is not None,
             "есть синхронный путь старта интерфейса (MtkDelaySec == 0)",
             "именно он соответствует рабочей сборке; отложенный режим - только отладочный")

    # ---- 2. initCCLogs() ---------------------------------------------------------------------
    cc = func_body(ctl, r"bool\s+AirportMtkWlan::\s*initCCLogs\s*\(\s*\)")
    c.ok(cc is not None, "AirportMtkWlan::initCCLogs найден", "без него нет логгера/репортёра")
    if cc is not None:
        c.ok(len(re.findall(r"->\s*CCPipe::startPipe\s*\(\s*\)", cc)) == 3,
             "ровно три квалифицированных вызова CCPipe::startPipe()",
             "фабрика pipe-а только инициализирует объект; event source-ы создаёт startPipe()")
        c.ok("IO80211FaultReporter::allocWithParams(driverCoreFaultReporter)" in cc,
             "fault reporter оборачивается в IO80211FaultReporter",
             "getFaultReporterFromDriver() обязан вернуть CommonFaultReporter, а не сырой CCFaultReporter")
        c.ok("OSDynamicCast(CommonFaultReporter" in cc,
             "обёртка проверяется как CommonFaultReporter", "иначе Family получит объект чужого типа")
        c.ok("CCFaultReporter::withStreamWorkloop(dataStream, _fWorkloop)" in cc,
             "core fault reporter создаётся на workloop wrapper-а", "порядок шагов как в рабочей сборке")
    c.ok(re.search(r"void\s+\*\s*AirportMtkWlan::getFaultReporterFromDriver\s*\(\s*\)\s*\{\s*return\s+driverFaultReporter\s*;", ctl) is not None,
         "getFaultReporterFromDriver() возвращает driverFaultReporter (обёртку)", "см. выше")
    c.ok(re.search(r"IOWorkLoop\s*\*\s*AirportMtkWlan::getWorkLoop\s*\(\s*\)\s*const\s*\{\s*return\s+_fWorkloop\s*;", ctl) is not None,
         "getWorkLoop() переопределён и возвращает очередь wrapper-а",
         "иначе Family использует свой workloop, а command gate висит на очереди wrapper-а")
    c.ok(re.search(r"virtual\s+IOWorkLoop\s*\*\s*getWorkLoop\s*\(\s*\)\s*const\s+override", hpp) is not None,
         "getWorkLoop объявлен как override в AirportMtkWlan.hpp", "иначе определение не станет переопределением слота 209")
    c.ok("driverCoreFaultReporter" in hpp and "IO80211FaultReporter *driverFaultReporter" in hpp,
         "поля репортёра в AirportMtkWlan.hpp", "тип поля - обёртка, core хранится отдельно для release")

    # ---- 3. интерфейс: двойная init ----------------------------------------------------------
    iw = func_body(sw, r"bool\s+AirportMtkWlanSkywalkInterface::\s*initWithController\s*\(\s*IOService\s*\*\s*provider\s*\)")
    c.ok(iw is not None, "initWithController найден", "см. ниже")
    if iw is not None:
        a = iw.find("IO80211InfraInterface::init()")
        b = iw.find("IO80211SkywalkInterface::init(provider")
        c.ok(a >= 0 and b > a,
             "после IO80211InfraInterface::init() вызывается IO80211SkywalkInterface::init(provider, mac)",
             "рабочая сборка делает обе инициализации; вторая задаёт провайдера и MAC интерфейса Family")
        c.ok("getHardwareAddress(&address)" in iw, "MAC читается у контроллера и передаётся во вторую init",
             "вторая init принимает ether_addr*")

    # ---- 4. Ethernet-интерфейс ---------------------------------------------------------------
    c.ok("setInterfaceSubType(3)" in eth, "setInterfaceSubType(3) в attachToDataLinkLayer",
         "обязательно перед super::attachToDataLinkLayer на Sequoia")
    i1 = eth.find("setInterfaceSubType(3)")
    i2 = eth.find("super::attachToDataLinkLayer(options, parameter)")
    c.ok(i1 >= 0 and i2 > i1, "setInterfaceSubType вызывается до super::attachToDataLinkLayer", "порядок как в рабочей сборке")
    c.ok(re.search(r"queue->inGate\(\)", eth) is not None and "prepareBSDInterface(self->getIfnet(), 0)" in eth,
         "prepareBSDInterface выполняется под проверкой inGate()", "вызов вне gate очереди IO80211 запрещён")
    c.ok("_fCommandGate->runAction(prepareBSDGated" in eth, "prepareBSDInterface вызывается через command gate", "см. выше")

    # ---- 5. заголовки ABI --------------------------------------------------------------------
    def asserts(rel):
        t = read(root, inc + rel)
        return t, strip_comments(t)

    ski_raw, ski = asserts("IOSkywalkInterface.h")
    net_raw, net = asserts("IOSkywalkNetworkInterface.h")
    eth_raw, ethh = asserts("IOSkywalkEthernetInterface.h")

    m = re.search(r"sizeof\(IOSkywalkInterface\)\s*==\s*(0x[0-9a-fA-F]+)", ski)
    base_ski = hexval(m.group(1)) if m else None
    c.ok(base_ski == 0xB0, "IOSkywalkInterface == 0xb0", "основа расчёта смещений")

    def layout(h, cls, base):
        """Раскладка: _layout0[X], <ExpansionData*>, _layout1[Y]; возвращает (смещение указателя, итоговый размер)."""
        m0 = re.search(r"_layout0\[(0x[0-9a-fA-F]+)\]", h)
        m1 = re.search(r"_layout1\[(0x[0-9a-fA-F]+)\]", h)
        if not m0 or base is None:
            return None, None
        off = base + hexval(m0.group(1))
        end = off + 8
        if m1:
            end += hexval(m1.group(1))
        return off, end

    off_net, size_net = layout(net, "IOSkywalkNetworkInterface", base_ski)
    c.ok(off_net == 0xB8 and size_net == 0xD0,
         "раскладка IOSkywalkNetworkInterface: mExpansionData по 0xb8, размер 0xd0",
         "значения из рабочей сборки; считаются из полей, а не из static_assert (который сам мог бы быть неверным)")
    c.ok(re.search(r"ExpansionData\s*\*\s*mExpansionData\s*;", net) is not None, "поле mExpansionData объявлено", "без него нечего заполнять")
    off_eth, size_eth = layout(ethh, "IOSkywalkEthernetInterface", size_net)
    c.ok(off_eth == 0x108 and size_eth == 0x110,
         "раскладка IOSkywalkEthernetInterface: mExpansionData2 по 0x108, размер 0x110",
         "значения из рабочей сборки")
    c.ok(re.search(r"ExpansionData\s*\*\s*mExpansionData2\s*;", ethh) is not None, "поле mExpansionData2 объявлено", "см. выше")
    c.ok("__offsetof(IOSkywalkNetworkInterface, mExpansionData) == 0xb8" in net, "static_assert смещения mExpansionData", "ловит дрейф раскладки на компиляции")
    c.ok("__offsetof(IOSkywalkEthernetInterface, mExpansionData2) == 0x108" in ethh, "static_assert смещения mExpansionData2", "см. выше")
    c.ok(len(re.findall(r"sizeof\(IOSkywalk(Network|Ethernet)Interface::RegistrationInfo\)\s*==\s*0x130", net + ethh)) == 2,
         "static_assert размера RegistrationInfo == 0x130 (оба класса)", "memcpy копирует ровно эту структуру")
    c.ok("fRegistrationInfo" in net and "fRegistrationInfo" in ethh, "поле fRegistrationInfo в обеих ExpansionData", "см. выше")

    # ---- 6. объявления для fault reporter ----------------------------------------------------
    ccs = strip_comments(read(root, inc + "CCStream.h"))
    c.ok(re.search(r"class\s+CommonFaultReporter\b", ccs) is not None
         and re.search(r"class\s+IO80211FaultReporter\b", ccs) is not None
         and "allocWithParams(CCFaultReporter *)" in ccs,
         "объявлены CommonFaultReporter / IO80211FaultReporter::allocWithParams", "иначе initCCLogs не соберётся")
    return c


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    root = argv[1] if len(argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    c = check(root)
    for e in c.errors:
        print(e)
    print("правил выполнено: %d, нарушено: %d" % (c.passed, len(c.errors)))
    return 1 if c.errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
