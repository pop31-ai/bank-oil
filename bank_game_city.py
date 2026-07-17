#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
БАНКЪ & НЕФТЬ: ГОРОДСКАЯ АРХИТЕКТУРА
Карточная игра о банках, нефти и городских владениях
Python CLI-версия для 2-4 игроков (горячий стул)
"""

import random, sys
from dataclasses import dataclass, field
from enum import Enum

# -------------------------------------------------------------------
# ЦВЕТА
# -------------------------------------------------------------------
class C:
    GREEN='\033[92m'; RED='\033[91m'; BLUE='\033[94m'
    YELLOW='\033[93m'; CYAN='\033[96m'; MAGENTA='\033[95m'
    BLACK='\033[90m'; BOLD='\033[1m'; END='\033[0m'; WHITE='\033[97m'

# -------------------------------------------------------------------
# РАЙОНЫ ГОРОДА (9 основных + 1 секретный)
# -------------------------------------------------------------------
DISTRICTS_DATA = {
    "fin":  {"name": "Финансовый квартал", "x":1,"y":1,"cost":0,
             "bonus":"Хранилище. Все операции быстрее.",
             "desc":"Дом банков. Неоклассика. Колонны. В подвале хранилище.",
             "adj":["birzha","gostiny","merya","vokzal"]},
    "birzha":{"name":"Биржевая площадь","x":0,"y":0,"cost":200,
              "bonus":"Акции без комиссии. +2 эмиссии за ход.",
              "desc":"Огромное табло. Колоннада. Бронзовые бык и медведь.",
              "adj":["fin","merya","gostiny"]},
    "gostiny":{"name":"Гостиный двор","x":0,"y":1,"cost":200,
               "bonus":"Векселя +5% дохода. Обмен бесплатно.",
               "desc":"Купеческие арки. Лавки. Пахнет табаком и кожей.",
               "adj":["fin","birzha","prom","vokzal"]},
    "merya": {"name":"Мэрия","x":1,"y":0,"cost":200,
              "bonus":"Одно событие за ход можно отменить.",
              "desc":"Часы на башне. Герб города. Чиновники.",
              "adj":["fin","birzha","port"]},
    "port":  {"name":"Порт","x":2,"y":0,"cost":250,
              "bonus":"Международные контрагенты -10%.",
              "desc":"Морской вокзал. Соль. Нефть. Таможня.",
              "adj":["merya","fin","vokzal"]},
    "vokzal":{"name":"Вокзал","x":2,"y":1,"cost":200,
              "bonus":"+10K/раунд. Депозиты на 3% дешевле.",
              "desc":"Купол. Ресторан. Очереди. Деньги приезжих.",
              "adj":["fin","gostiny","port","torg"]},
    "prom":  {"name":"Промышленная зона","x":0,"y":2,"cost":250,
              "bonus":"Нефть +20% дохода. 2 проекта за ход.",
              "desc":"Заводы. Трубы. Резервуары. Пахнет нефтью.",
              "adj":["gostiny","fin","bankr"]},
    "bankr": {"name":"Банк России","x":1,"y":2,"cost":300,
              "bonus":"Рефинанс под 3%. Резервы 5%.",
              "desc":"Без вывески. Охрана. Золото в подвалах.",
              "adj":["prom","fin","torg"]},
    "torg":  {"name":"Торговый центр","x":2,"y":2,"cost":200,
              "bonus":"Депозиты +10%. Расходы -5K/раунд.",
              "desc":"Стекло. Фонтаны. Эскалаторы. Деньги рекой.",
              "adj":["vokzal","fin","bankr"]},
    "osobnyak":{"name":"Особняк купца","x":-1,"y":-1,"cost":500,
                "bonus":"+1 действие за ход. Секретный район.",
                "desc":"Старинный особняк. Тайные комнаты. Камин.",
                "adj":["fin"]},
}

@dataclass
class District:
    key: str; name: str; x: int; y: int; cost: int
    bonus: str; desc: str; adj: list
    owner: object = None
    branch: bool = False

@dataclass
class Card:
    name: str; ctype: str; district: str = ""  # район
    desc: str = ""

@dataclass
class Contract:
    name: str; ctype: str; summa: int; rate: float
    srok_total: int; srok_left: int; district: str = ""
    income: int = 0; expense: int = 0

# -------------------------------------------------------------------
# ИГРОК
# -------------------------------------------------------------------
@dataclass
class Player:
    name: str
    cash: int = 0; vault: bool = True; korchet: int = 0
    share_capital: int = 0; shares_issued: int = 0
    districts: list = field(default_factory=list)   # ключи районов
    contracts: list = field(default_factory=list)
    hand: list = field(default_factory=list)
    reputation: int = 100; bankrupt: bool = False
    profit: int = 0; total_profit: int = 0

    @property
    def total_assets(self):
        a = self.cash + self.korchet + (50 if self.vault else 0)
        for c in self.contracts:
            if c.ctype in ('credit','veksel_asset','neft'): a += c.summa
        for d in self.districts:
            dist = DISTRICTS_DATA.get(d)
            if dist: a += dist["cost"]
        return a

    @property
    def total_liabilities(self):
        l = 0
        for c in self.contracts:
            if c.ctype in ('deposit','veksel_liability'): l += c.summa
        return l

    @property
    def capital(self): return self.total_assets - self.total_liabilities

    def has_district(self, key): return key in self.districts

# -------------------------------------------------------------------
# ГАЗЕТЫ (15 шт с привязкой к районам)
# -------------------------------------------------------------------
NEWS = [
    (C.YELLOW,"Золотые часы кассира",
     "В ФИНАНСОВОМ КВАРТАЛЕ кассир Сомов получил золотые часы "
     "за спасение хранилища. 35 лет в банке. Пахнет табаком и верностью."),
    (C.BLUE,"Табачный король стал банкиром",
     "В ГОСТИНОМ ДВОРЕ купец Гольдман открыл банк. Вместо лавки - "
     "кредитный отдел. Табак сменил на векселя. Часы золотые носит."),
    (C.CYAN,"Вещи, которые научили считать",
     "Директор Ковалёва: каждая вещь в моем кабинете - урок. "
     "Бюро из МЭРИИ. Часы с БИРЖЕВОЙ. Ковер из ПОРТА. Бухгалтерия - это вещи."),
    (C.RED,"Предупрежден - значит вооружен",
     "Риск-менеджер Лосев из ФИНАНСОВОГО КВАРТАЛА: носите простые часы. "
     "Золото - риск. Табак - вред. Знание предмета - спасение."),
    (C.MAGENTA,"От ларька до биржи",
     "Цой торговал у ВОКЗАЛА сигаретами. Теперь на БИРЖЕВОЙ ПЛОЩАДИ "
     "продает акции. Вместо папирос - облигации. Звон тот же."),
    (C.YELLOW,"Часы как залог стабильности",
     "Вершинин из БАНКА РОССИИ: золотые часы - актив, но в кризис "
     "их меняют на хлеб. Держите ликвидность. Учите историю."),
    (C.GREEN,"Вексельный садовник",
     "Дятлов из ГОСТИНОГО ДВОРА: вексель - живой организм. Растет в арках "
     "Гостиного. Удобряется доверием. Созревает в срок."),
    (C.BLUE,"Золотые руки операционистки",
     "Зимина с ВОКЗАЛА: 35 лет считает чужие деньги. Золотые часы - "
     "от сберкассы. Табак не курит - предупреждает."),
    (C.CYAN,"Как я учил банковское дело в Китае",
     "Крымов из ПОРТА: в Китае банки пахнут чаем, а не табаком. "
     "Золотые часы подарил партнер из Шанхая. Звенят по-китайски."),
    (C.RED,"История одного дефолта",
     "Трофимов потерял банк в ПРОМЫШЛЕННОЙ ЗОНЕ. Не изучил предмет - "
     "кредитнул пустую скважину. Продал часы. Теперь учит студентов."),
    (C.MAGENTA,"Табак, чай и гарантия",
     "Чхеидзе из ПОРТА: изучал табачные плантации полгода. "
     "Теперь выдает гарантии. Часы от клиента - табакерка в подарок."),
    (C.YELLOW,"Инвентаризация спасла банк",
     "Фролова из ТОРГОВОГО ЦЕНТРА нашла недостачу на 200KK. "
     "Новая система учета. Часы с гравировкой: За порядок в активах."),
    (C.GREEN,"Межбанковский кредит",
     "Четыре банкира в ФИНАНСОВОМ КВАРТАЛЕ спасли коллегу. "
     "Дали МБК под честное слово. Золотые часы каждому - символ."),
    (C.BLUE,"Депозит под табак",
     "Кузнецов из ПРОМЫШЛЕННОЙ ЗОНЫ: деньги в городе звенят в кошельке. "
     "В деревне - в колосе. Научись слышать разницу."),
    (C.CYAN,"Дивиденды успеха",
     "Султанов с БИРЖЕВОЙ ПЛОЩАДИ купил часы на первую прибыль. "
     "Теперь коллекция - 15 штук. Из каждого района."),
]

# -------------------------------------------------------------------
# КАРТЫ
# -------------------------------------------------------------------
def make_deck():
    cards = []
    # акции (Биржевая площадь)
    for i in range(20):
        cards.append(Card(f"Акция {i+1}", "akciya", "birzha"))
    # векселя (Гостиный двор)
    for i in range(20):
        cards.append(Card(f"Вексель {i+1}", "veksel", "gostiny"))
    # события (Мэрия)
    ev = ["Ставка ЦБ+5%","Ставка ЦБ-5%","Инфляция","Девальвация",
          "Рост экономики","Рецессия","Санкции","Инвестиции",
          "Кризис","Стабилизация","Нефть взлетела",
          "Дефолт","Дефолт нефти","Отзыв лицензии","Отток вкладчиков",
          "Кража","Пожар","Авария","Проблема с векселем","Невозврат МБК",
          "Репутация","Предупреждение ЦБ","Сделка с векселем","Продажа активов",
          "Возврат долга","Снижение резервов","IPO","Слияние",
          "Дивиденды от дочек","Господдержка","Тендер","Месторождение","Премия",
          "Корпоративный клиент","Просрочка","Досрочное погашение","Новый акционер",
          "Сбой в ЦБ","Обмен валюты","Иск клиента","Финтех","Аудит ЦБ",
          "Лицензия","Филиал"]
    for e in ev:
        cards.append(Card(e, "sobytie", "merya"))
    # контрагенты (Гостиный двор / Торговый центр)
    dep = ["Физлицо","Физлицо","Пенсионный фонд","Страховая","Нефтяная корп.",
           "Муниципалитет","Инвестфонд","До востребования","VIP","Бюджет"]
    for d in dep:
        cards.append(Card(f"Депозит {d}", "deposit", "torg"))
    cred = ["ИП Петров","ООО Бурнефть","АО Нефтепром","Ипотека","АЗС",
            "Крупный корп.","Потребкредит","Автокредит","МБК","Кред.линия"]
    for c in cred:
        cards.append(Card(f"Кредит {c}", "credit", "gostiny"))
    # межбанк
    for m in ["Банк-партнер","Рефинанс ЦБ","Депозит в банке","Овердрафт","Синдикат"]:
        cards.append(Card(f"Межбанк {m}", "mejbank", "bankr"))
    # прочее
    for o in ["Платежная система","Аренда офиса","Инкассация","Обслуж. хранилища","Банкоматы"]:
        cards.append(Card(o, "other", "fin"))
    # нефтяные проекты (Промзона)
    neft = ["Скважина Сибирь","Нефтепровод","АЗС-сеть","Танкер","НПЗ",
            "Геологоразведка","Вышка","Бензохранилище","Терминал","Лаборатория"]
    for n in neft:
        cards.append(Card(f"Нефть {n}", "neft", "prom"))
    return cards

# -------------------------------------------------------------------
# ИГРА
# -------------------------------------------------------------------
class Game:
    def __init__(self):
        self.players = []
        self.round = 0; self.max_rounds = 10
        self.all_cards = make_deck()
        self.event_deck = [c for c in self.all_cards if c.ctype=="sobytie"]
        self.action_deck = [c for c in self.all_cards if c.ctype!="sobytie"]
        random.shuffle(self.event_deck); random.shuffle(self.action_deck)
        self.districts = {k: District(k, v["name"], v["x"], v["y"], v["cost"],
                           v["bonus"], v["desc"], v["adj"]) for k,v in DISTRICTS_DATA.items()}

    def setup(self):
        print(C.BOLD+C.WHITE+"\n"+ "#"*60+C.END)
        print(C.BOLD+C.GREEN+"   БАНКЪ & НЕФТЬ: ГОРОДСКАЯ АРХИТЕКТУРА"+C.END)
        print(C.WHITE+"#"*60+C.END)
        n = 0
        while not (2 <= n <= 4):
            try: n = int(input(C.CYAN+"Сколько игроков? (2-4): "+C.END))
            except: pass
        for i in range(n):
            name = input(f"Имя игрока {i+1}: ").strip() or f"Игрок {i+1}"
            p = Player(name=name)
            shares = 0
            while not (1 <= shares <= 5):
                try: shares = int(input(f"  {p.name}, сколько акций? (1-5 по 100K): "))
                except: pass
            p.share_capital = shares * 100
            p.shares_issued = shares
            p.korchet = int(p.share_capital * 0.1)
            p.cash = p.share_capital - 50 - p.korchet
            p.districts.append("fin")  # старт в Финансовом квартале
            self.districts["fin"].owner = p
            self.players.append(p)
            print(f"  {C.GREEN}Хранилище собрано! Касса: {p.cash}K, Капитал: {p.capital}K{C.END}")
        # стартовые карты
        for p in self.players:
            for _ in range(3):
                if self.action_deck: p.hand.append(self.action_deck.pop())
        self.show_city()
        input(C.BLACK+"Нажмите Enter для начала..."+C.END)

    def show_city(self):
        print(C.BOLD+C.YELLOW+"\n======= КАРТА ГОРОДА ======="+C.END)
        grid = [["" for _ in range(3)] for _ in range(3)]
        owners = {}
        for d in self.districts.values():
            if d.x >= 0 and d.y >= 0:
                grid[d.y][d.x] = d
                if d.owner:
                    owners[d.key] = d.owner.name[:6]
        for y in range(3):
            line = ""
            for x in range(3):
                d = grid[y][x]
                if d:
                    o = owners.get(d.key, "")[:6]
                    nm = d.name[:12]
                    line += f"| {nm:12s} {o:6s} "
            print("+" + "-"*20 + "+" + "-"*20 + "+" + "-"*20 + "+")
            print("|" + line + "|")
        print("+" + "-"*20 + "+" + "-"*20 + "+" + "-"*20 + "+")
        print(f"  {C.GREEN}Ваш район: + Финансовый квартал{C.END}")
        print(f"  {C.BLUE}Смежные: Биржа, Гостиный, Мэрия, Вокзал{C.END}")

    def show_districts(self, p):
        print(f"\n{C.BOLD}{C.YELLOW}Ваши районы:{C.END}")
        for k in p.districts:
            d = self.districts[k]
            own = "+" if d.owner == p else " "
            br = " Ф" if d.branch else ""
            print(f"  {own} {d.name}{br} ({d.bonus[:30]})")

    def player_turn(self, p):
        if p.bankrupt: return
        print(C.BOLD+C.WHITE+f"\n{'='*60}"+C.END)
        print(C.BOLD+C.GREEN+f"  ХОД: {p.name}  | Раунд {self.round}/{self.max_rounds}"+C.END)
        self.show_balance(p)
        # событие
        input(C.BLACK+"Enter - тянуть событие из Мэрии..."+C.END)
        if self.event_deck:
            ev = self.event_deck.pop()
            print(f"{C.RED}СОБЫТИЕ (Мэрия): {ev.name}{C.END}")
            self.apply_event(p, ev)
        # действия
        extra = 1 if p.has_district("osobnyak") else 0
        acts = 3 + extra
        while acts > 0:
            print(f"\n{C.CYAN}Действий: {acts}{C.END}  |  Касса: {p.cash}K  |  Районов: {len(p.districts)}")
            print("1. Сыграть карту из руки")
            print("2. Купить район (200K, смежный с вашим)")
            print("3. Открыть филиал в районе (100K)")
            print("4. Выпустить акции (Биржа)")
            print("5. Выпустить вексель (Гостиный двор)")
            print("6. Выпуск акций + карта города")
            print("7. Газета")
            print("8. Закончить ход")
            ch = input("Выбор: ").strip()
            if ch == "1":
                if not p.hand:
                    print("  Рука пуста.")
                    continue
                for i,c in enumerate(p.hand):
                    dname = self.districts[c.district].name if c.district in self.districts else "?"
                    print(f"  {i+1}. {c.name} [{c.ctype}] -> {dname}")
                try:
                    ci = int(input("  Номер: "))-1
                    if 0 <= ci < len(p.hand):
                        card = p.hand.pop(ci)
                        self.play_card(p, card)
                        acts -= 1
                except: pass
            elif ch == "2":
                self.buy_district(p)
                acts -= 1
            elif ch == "3":
                self.open_branch(p)
                acts -= 1
            elif ch == "4":
                p.share_capital += 200; p.shares_issued += 2
                p.cash += 200
                print(f"  {C.GREEN}+2 акции, +200K капитала (Биржевая площадь){C.END}")
                acts -= 1
            elif ch == "5":
                nom = 100; sv = input("  Номинал (100-300K): ") or "100"
                try: nom = int(sv)
                except: pass
                p.cash += nom
                p.contracts.append(Contract(f"Вексель на {nom}K","veksel_liability",nom,10,3,3,"gostiny"))
                print(f"  {C.BLUE}Вексель выпущен в Гостином дворе. +{nom}K{C.END}")
                acts -= 1
            elif ch == "6":
                self.show_city()
            elif ch == "7":
                self.show_news(p)
            elif ch == "8":
                break
        # расчёты
        self.do_accounts(p)
        if p.capital < 0:
            print(C.RED+f"\n  БАНКРОТСТВО! {p.name} выбывает (капитал {p.capital}K)."+C.END)
            p.bankrupt = True
        elif p.capital < p.share_capital // 2:
            print(f"  {C.RED}Капитал ниже 50% ({p.capital}K). Срочно нужна прибыль!{C.END}")
        input(C.BLACK+"Enter - передать ход..."+C.END)

    def buy_district(self, p):
        # показать доступные (смежные с владениями игрока)
        available = []
        for dk, d in self.districts.items():
            if d.owner or d.cost == 0: continue
            # смежный хотя бы с одним районом игрока
            for myd in p.districts:
                if dk in self.districts[myd].adj:
                    available.append(dk)
                    break
        if not available:
            print("  {C.RED}Нет доступных районов.{C.END}")
            return
        print(f"{C.BOLD}Доступные районы:{C.END}")
        for i, dk in enumerate(available):
            d = self.districts[dk]
            print(f"  {i+1}. {d.name} - {d.cost}K ({d.bonus[:25]})")
        try:
            ci = int(input("  Какой покупаете? (0 - отмена): "))-1
            if 0 <= ci < len(available):
                dk = available[ci]; d = self.districts[dk]
                if p.cash >= d.cost:
                    p.cash -= d.cost
                    p.districts.append(dk)
                    d.owner = p
                    print(f"  {C.GREEN}Куплен район: {d.name}!{C.END}")
                    print(f"  Архитектура: {d.desc}")
                    print(f"  Бонус: {d.bonus}")
                else:
                    print(f"  {C.RED}Не хватает денег. Нужно {d.cost}K.{C.END}")
        except: pass

    def open_branch(self, p):
        print("Ваши районы для филиала:")
        for dk in p.districts:
            d = self.districts[dk]
            st = "есть" if d.branch else "нет"
            print(f"  {d.name} (филиал: {st})")
        dk = input("  В каком районе открыть? (ключ: fin/birzha/...): ").strip()
        if dk in p.districts and dk in self.districts:
            d = self.districts[dk]
            if d.branch:
                print("  Филиал уже есть.")
            elif p.cash >= 100:
                p.cash -= 100; d.branch = True
                print(f"  {C.GREEN}Филиал открыт в {d.name}!{C.END}")
            else:
                print(f"  {C.RED}Нужно 100K.{C.END}")
        else:
            print("  Нет такого района.")

    def show_balance(self, p):
        assets = p.cash + p.korchet + (50 if p.vault else 0)
        for c in p.contracts:
            if c.ctype in ('credit','neft','veksel_asset'): assets += c.summa
        liab = self.liab_sum(p)
        print(f"\n{C.CYAN}--- Баланс {p.name} ---{C.END}")
        print(f"  {C.GREEN}Активы:{C.END} касса {p.cash}K, корсчет {p.korchet}K, районы {len(p.districts)}")
        for c in p.contracts:
            if c.ctype in ('credit','neft','veksel_asset'):
                print(f"    {c.name} +{c.summa}K")
        print(f"  {C.RED}Пассивы:{C.END} обязат. {liab}K")
        print(f"  Акционерный капитал: {p.share_capital}K")
        col = C.GREEN if p.capital >= p.share_capital else C.YELLOW
        print(f"  {col}ИТОГО КАПИТАЛ (с прибылью): {p.capital}K{C.END}")

    def liab_sum(self, p):
        return sum(c.summa for c in p.contracts if c.ctype in ('deposit','veksel_liability'))

    def apply_event(self, p, ev):
        n = ev.name
        if n=="Кризис": p.cash = int(p.cash*0.8)
        elif n=="Инфляция": p.cash = int(p.cash*0.95)
        elif n=="Кража": p.cash = max(0,p.cash-50)
        elif n=="Пожар": p.cash = max(0,p.cash-30)
        elif n=="Дефолт": p.cash = max(0,p.cash-50)
        elif n=="Дефолт нефти": p.cash = max(0,p.cash-200)
        elif n=="Отток вкладчиков": p.cash = int(p.cash*0.85)
        elif n=="Рецессия": p.cash = max(0,p.cash-30)
        elif n=="Невозврат МБК": p.cash = max(0,p.cash-100)
        elif n=="Рост экономики": p.cash += 50
        elif n=="Инвестиции": p.cash += 100
        elif n=="IPO": p.cash += 100
        elif n=="Слияние": p.cash += 80
        elif n=="Тендер": p.cash += 30
        elif n=="Премия": p.cash += 20; p.reputation = min(100,p.reputation+10)
        elif n=="Нефть взлетела":
            for c in p.contracts:
                if c.ctype=="neft": c.income += 20
        elif n=="Господдержка": p.cash += 100
        elif n=="Месторождение":
            if len([c for c in p.contracts if c.ctype=="neft"])<3:
                p.contracts.append(Contract("Новое месторождение","neft",200,0,999,999,"prom",income=60))
                print(f"  {C.MAGENTA}+1 нефтяной проект!{C.END}")
        elif n=="Предупреждение ЦБ":
            if p.korchet < int(p.share_capital*0.1):
                p.cash = max(0,p.cash-150)
        elif n=="Аудит ЦБ":
            if p.korchet < int(p.share_capital*0.1):
                p.cash = max(0,p.cash-100)
        elif n=="Просрочка":
            for c in p.contracts:
                if c.ctype=="credit": c.income = 0; break
        elif n=="Иск клиента": p.cash = max(0,p.cash-30)
        elif n=="Досрочное погашение": p.cash += 50
        elif n=="Продажа активов": p.cash += 60
        elif n=="Возврат долга": p.cash += 80
        elif n=="Снижение резервов":
            r = int(p.korchet*0.5); p.cash += r; p.korchet -= r
        elif n=="Филиал": p.cash -= 50
        elif n=="Обмен валюты": p.cash += 15
        elif n=="Дивиденды от дочек": p.cash += 50
        elif n=="Санкции": p.korchet = int(p.korchet*0.5)

    def play_card(self, p, card):
        # проверка района
        if card.district and card.district not in p.districts:
            # можно сыграть если есть филиал или это Финансовый квартал
            if not p.has_district("fin"):
                print(f"  {C.RED}Нужен район {self.districts[card.district].name}!{C.END}")
                p.hand.append(card)
                return
            else:
                print(f"  {C.BLACK}Используем через Финансовый квартал (без бонуса){C.END}")
        # эффект
        if card.ctype == "credit":
            s = 100
            p.cash -= s
            p.contracts.append(Contract(card.name,"credit",s,12,4,4,card.district,income=int(s*12/100)))
            print(f"  {C.GREEN}Кредит выдан в {self.districts[card.district].name}: -{s}K{C.END}")
        elif card.ctype == "deposit":
            s = 100
            p.cash += s
            p.contracts.append(Contract(card.name,"deposit",s,5,4,4,card.district,expense=int(s*5/100)))
            print(f"  {C.YELLOW}Депозит в {self.districts[card.district].name}: +{s}K{C.END}")
        elif card.ctype == "neft":
            if p.cash >= 200:
                p.cash -= 200
                p.contracts.append(Contract(card.name,"neft",200,0,999,999,card.district,income=50))
                print(f"  {C.MAGENTA}Нефть в Промзоне: -200K, доход 50K/раунд{C.END}")
            else:
                print(f"  {C.RED}Не хватает денег.{C.END}")
                p.hand.append(card)
        elif card.ctype == "mejbank":
            p.cash += 150
            p.contracts.append(Contract(card.name,"credit",150,6,3,3,card.district,income=9))
            print(f"  {C.CYAN}Межбанк в Банке России: +150K{C.END}")
        elif card.ctype in ("akciya","veksel"):
            print(f"  {C.GREEN}{card.name} в {self.districts[card.district].name}{C.END}")
        elif card.ctype == "other":
            print(f"  {C.BLACK}{card.name}: в силе{C.END}")

    def do_accounts(self, p):
        profit = 0
        for c in p.contracts[:]:
            if c.ctype == "credit":
                profit += c.income
                c.srok_left -= 1
                if c.srok_left <= 0:
                    p.cash += c.summa + c.income
                    p.contracts.remove(c)
                    print(f"  {C.GREEN}Кредит погашен: +{c.summa+c.income}K{C.END}")
            elif c.ctype == "deposit":
                profit -= c.expense
                p.cash -= c.expense
                c.srok_left -= 1
                if c.srok_left <= 0:
                    p.cash -= c.summa
                    p.contracts.remove(c)
                    print(f"  {C.RED}Депозит выплачен: -{c.summa+c.expense}K{C.END}")
            elif c.ctype == "neft":
                bonus = 1
                if p.has_district("prom"): bonus = 1.2
                inc = int(c.income * bonus)
                profit += inc; p.cash += inc
                print(f"  {C.MAGENTA}{c.name}: +{inc}K{C.END}")
            elif c.ctype == "veksel_liability":
                p.cash -= c.expense; profit -= c.expense
                c.srok_left -= 1
                if c.srok_left <= 0:
                    p.cash -= c.summa + c.expense
                    p.contracts.remove(c)
                    print(f"  {C.RED}Вексель оплачен: -{c.summa+c.expense}K{C.END}")
            elif c.ctype == "veksel_asset":
                profit += c.income; c.srok_left -= 1
                if c.srok_left <= 0:
                    p.cash += c.summa + c.income
                    p.contracts.remove(c)
        # бонусы районов
        for dk in p.districts:
            d = self.districts[dk]
            if d.branch: p.cash += 5; profit += 5
        # Финансовый квартал дает +5K за раунд
        if p.has_district("fin"): p.cash += 5; profit += 5
        # Вокзал
        if p.has_district("vokzal"): p.cash += 10; profit += 10
        if p.vault and self.round > 1: p.cash = max(0,p.cash-3); profit -= 3
        p.profit = profit; p.total_profit += profit

    def show_news(self, p):
        print(f"\n{C.BOLD}{C.YELLOW}========== ГАЗЕТА =========={C.END}")
        for i,(col,tit,txt) in enumerate(NEWS):
            print(f"  {i+1}. {col}{tit}{C.END}")
        try:
            ci = int(input("  Номер статьи (0-назад): "))-1
            if 0 <= ci < len(NEWS):
                col,tit,txt = NEWS[ci]
                print(f"\n{col}{C.BOLD}--- {tit} ---{C.END}")
                print(f"{col}{txt}{C.END}")
                input(C.BLACK+"Enter..."+C.END)
        except: pass

    def dividends(self):
        print(C.BOLD+C.YELLOW+f"\nДИВИДЕНДЫ (раунд {self.round})"+C.END)
        for p in self.players:
            if p.bankrupt: continue
            if p.total_profit > 0:
                d = int(p.total_profit*0.1)
                p.cash -= d
                print(f"  {p.name}: дивиденды {d}K")
            else:
                print(f"  {p.name}: прибыли нет")

    def meeting(self):
        print(C.BOLD+C.MAGENTA+f"\nСОБРАНИЕ АКЦИОНЕРОВ (раунд {self.round})"+C.END)
        for p in self.players:
            if p.bankrupt: continue
            print(f"  {p.name}: {p.shares_issued} акций, {len(p.districts)} районов")

    def play(self):
        self.setup()
        for self.round in range(1, self.max_rounds+1):
            print(C.BOLD+C.WHITE+f"\n{'#'*60}"+C.END)
            print(C.BOLD+C.GREEN+f"  РАУНД {self.round}/{self.max_rounds}"+C.END)
            print(C.WHITE+f"{'#'*60}"+C.END)
            if self.round % 3 == 0: self.dividends()
            if self.round % 5 == 0: self.meeting()
            for p in self.players:
                self.player_turn(p)
                if p.bankrupt: continue
            alive = [p for p in self.players if not p.bankrupt]
            if len(alive) <= 1: break
        self.final()

    def final(self):
        print(C.BOLD+C.WHITE+f"\n{'#'*60}"+C.END)
        print(C.BOLD+C.GREEN+"  ИГРА ОКОНЧЕНА!"+C.END)
        print(C.WHITE+f"{'#'*60}"+C.END)
        res = sorted(self.players, key=lambda p: p.capital, reverse=True)
        for i,p in enumerate(res):
            st = C.GREEN if not p.bankrupt else C.RED
            print(f"\n  {i+1}. {st}{p.name}{C.END}")
            print(f"     Капитал: {p.capital}K  |  Районов: {len(p.districts)}")
            print(f"     Акций: {p.shares_issued}  |  Репутация: {p.reputation}%")
            if p.bankrupt: print(f"     {C.RED}БАНКРОТ{C.END}")
            for dk in p.districts:
                d = self.districts[dk]
                print(f"       {d.name} {'Ф' if d.branch else ''}")
        w = res[0]
        print(C.BOLD+C.YELLOW+f"\nПОБЕДИТЕЛЬ: {w.name}! Капитал {w.capital}K, {len(w.districts)} районов"+C.END)
        print(C.YELLOW+"  Деньги звенят в каждом районе по-своему."+C.END)
        print(C.WHITE+f"{'#'*60}\n"+C.END)

# -------------------------------------------------------------------
# ЗАПУСК
# -------------------------------------------------------------------
def main():
    try:
        Game().play()
    except KeyboardInterrupt:
        print(f"\n{C.RED}Игра прервана.{C.END}")
        sys.exit(0)

if __name__ == "__main__":
    main()
