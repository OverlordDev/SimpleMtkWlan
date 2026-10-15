#!/usr/bin/env python3
"""Самопроверка check_airport_start.py: каждое правило обязано упасть на намеренно сломанной копии.

    python3 -I experimental/check_airport_start_selftest.py [корень_репозитория]

Проверка, которая ничего не находит, выглядит так же, как проверка, которая работает. Поэтому для каждого правила
здесь есть мутация исходников, при которой чекер ОБЯЗАН вернуть ненулевой код и назвать нужное правило.
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = [
    "experimental/AirportMtkWlan/AirportMtkWlan.cpp",
    "experimental/AirportMtkWlan/AirportMtkWlan.hpp",
    "experimental/AirportMtkWlan/AirportMtkWlanSkywalkInterface.cpp",
    "experimental/AirportMtkWlan/AirportMtkWlanEthernetInterface.cpp",
    "experimental/include/Sequoia/IOSkywalkInterface.h",
    "experimental/include/Sequoia/IOSkywalkNetworkInterface.h",
    "experimental/include/Sequoia/IOSkywalkEthernetInterface.h",
    "experimental/include/Sequoia/CCStream.h",
]
CTL, HPP, SW, ETH = FILES[0], FILES[1], FILES[2], FILES[3]
NETH, ETHH, CCH = FILES[5], FILES[6], FILES[7]

# (имя, файл, что заменить, на что, подстрока, которая должна появиться в выводе чекера)
MUTATIONS = [
    ("attachInterface(..., true)", CTL,
     "(IONetworkInterface **)&bsdInterface, false)", "(IONetworkInterface **)&bsdInterface, true)", "doRegister=false"),
    ("нет startPipe у log-pipe", CTL,
     "driverLogPipeStarted = driverLogPipe->CCPipe::startPipe();", "driverLogPipeStarted = true;", "startPipe"),
    ("нет заполнения ExpansionData (сеть)", CTL,
     "expNet->fRegistrationInfo = (", "expNet->fRegistrationInfoX = (", "expNet->fRegistrationInfo ="),
    ("нет обёртки IO80211FaultReporter", CTL,
     "IO80211FaultReporter::allocWithParams(driverCoreFaultReporter)", "(IO80211FaultReporter *)driverCoreFaultReporter",
     "IO80211FaultReporter"),
    ("нет проверки CommonFaultReporter", CTL,
     "OSDynamicCast(CommonFaultReporter, driverFaultReporter)", "driverFaultReporter", "CommonFaultReporter"),
    ("start интерфейса раньше ExpansionData", CTL,
     "memset(&registInfo, 0, sizeof(registInfo));", "fNetIf->start(this); memset(&registInfo, 0, sizeof(registInfo));",
     "нигде не вызывается раньше"),
    ("нет второй init интерфейса", SW,
     "if (!IO80211SkywalkInterface::init(provider,", "if (!IO80211SkywalkInterface::initX(provider,", "IO80211SkywalkInterface::init"),
    ("нет getWorkLoop override", HPP,
     "virtual IOWorkLoop *getWorkLoop() const override;", "virtual IOWorkLoop *getWorkLoopX() const;", "getWorkLoop"),
    ("нет setInterfaceSubType(3)", ETH,
     "if (!setInterfaceSubType(3))", "if (!setInterfaceSubType(2))", "setInterfaceSubType"),
    ("prepareBSDInterface не под gate", ETH,
     "!queue->inGate() ||", "false ||", "inGate"),
    ("неверное смещение mExpansionData", NETH,
     "uint8_t _layout0[0x8];", "uint8_t _layout0[0x10];", "mExpansionData по 0xb8"),
    ("неверное смещение mExpansionData2", ETHH,
     "uint8_t _layout0[0x38];", "uint8_t _layout0[0x30];", "mExpansionData2 по 0x108"),
    ("нет объявления IO80211FaultReporter", CCH,
     "class IO80211FaultReporter", "class IO80211FaultReporterX", "IO80211FaultReporter"),
]


def run_checker(root):
    r = subprocess.run([sys.executable, "-I", os.path.join(HERE, "check_airport_start.py"), root],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout + r.stderr


def main(argv):
    src_root = argv[1] if len(argv) > 1 else os.path.dirname(HERE)
    fails = 0
    tmp_root = tempfile.mkdtemp(prefix="airport_selftest_")
    try:
        def fresh():
            d = tempfile.mkdtemp(dir=tmp_root)
            for rel in FILES:
                dst = os.path.join(d, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copyfile(os.path.join(src_root, rel), dst)
            return d

        d = fresh()
        code, out = run_checker(d)
        if code != 0:
            print("ПРОВАЛ: на неизменённых исходниках чекер падает:\n" + out)
            return 1
        print("ok    исходники без изменений проходят")

        for name, rel, old, new, expect in MUTATIONS:
            d = fresh()
            p = os.path.join(d, rel)
            with open(p, encoding="utf-8") as f:
                text = f.read()
            if old not in text:
                print("ПРОВАЛ %-42s в %s нет фрагмента для мутации: %r" % (name, rel, old))
                fails += 1
                continue
            with open(p, "w", encoding="utf-8") as f:
                f.write(text.replace(old, new, 1))
            code, out = run_checker(d)
            if code == 0:
                print("ПРОВАЛ %-42s чекер НЕ заметил поломку" % name)
                fails += 1
            elif expect not in out:
                print("ПРОВАЛ %-42s чекер упал, но не на том правиле (ждали %r)" % (name, expect))
                fails += 1
            else:
                print("ok    %-42s пойман" % name)
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)
    print("мутаций: %d, непойманных: %d" % (len(MUTATIONS), fails))
    return 1 if fails else 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.exit(main(sys.argv))
