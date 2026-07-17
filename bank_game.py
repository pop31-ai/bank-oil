#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
БАНК & НЕФТЬ -- карточная игра о банках, нефти и большой прибыли
Python CLI-версия для 2-4 игроков (горячий стул)

Основана на документации: bank_and_oil_game.txt
Автор: pop31-ai
"""

import random
import sys
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

# -----------------------------------------------------------------
# ЦВЕТА ДЛЯ ТЕРМИНАЛА
# -----------------------------------------------------------------

class C:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BLACK = '\033[90m'
    BOLD = '\033[1m'
    END = '\033[0m'
    WHITE = '\033[97m'

# -----------------------------------------------------------------
# ТИПЫ КАРТ
# -----------------------------------------------------------------

class CardType(Enum):
    AKCIYA = "Акция"
    VEKSEL = "Вексель"
    SOBYTIE = "Событие"
    KONTAGENT = "Контрагент"
    NEFT = "Нефтяной проект"

class EventCategory(Enum):
    MACRO = "Макроэкономика"
    RISK = "Риски"
    POSITIVE = "Позитив"
    OPER = "Операционка"

class KontragentType(Enum):
    DEPOSIT = "Депозит"
    CREDIT = "Кредит"
    MEJBANK = "Межбанк"
    OTHER = "Прочее"

# -----------------------------------------------------------------
# БАЗОВЫЙ КЛАСС КАРТЫ
# -----------------------------------------------------------------

@dataclass
class Card:
    name: str
    card_type: CardType
    description: str = ""

@dataclass
class AkciyaCard(Card):
    nominal: int = 100
    special: str = ""

@dataclass
class VekselCard(Card):
    nominal: int = 100
    srok: int = 3
    dohodnost: int = 10

@dataclass
class SbytieCard(Card):
    category: EventCategory = EventCategory.MACRO
    effect_text: str = ""

@dataclass
class KontragentCard(Card):
    kt_type: KontragentType = KontragentType.DEPOSIT
    summa: int = 100
    srok: int = 3
    stavka: float = 5.0
    obespechenie: str = ""

@dataclass
class NeftCard(Card):
    cost: int = 300
    dohod: int = 80
    risk_text: str = ""
    risk_loss: int = 200

# -----------------------------------------------------------------
# ПАКИ КАРТ (все 124 карты)
# -----------------------------------------------------------------

def create_deck() -> list:
    cards = []

    # АКЦИИ (20)
    akcii_data = [
        ("Обыкновенная акция", 100, "1 голос на собрании"),
        ("Обыкновенная акция", 100, ""),
        ("Обыкновенная акция", 100, ""),
        ("Привилегированная акция", 100, "Дивиденд 10% фикс"),
        ("Привилегированная акция", 100, "Дивиденд 10% фикс"),
        ("Акция с отсрочкой", 100, "Дивиденд 15% через 3 раунда"),
        ("Конвертируемая акция", 100, "Можно обменять на вексель"),
        ("Акция трудового коллектива", 80, "Стабильность +5%"),
        ("Акция стратег. партнёра", 150, "Блок на 4 раунда"),
        ("Золотая акция", 200, "Вето на собрании"),
        ("Акция с правом доп. эмиссии", 120, "+1 эмиссия в раунд"),
        ("Акция с гарантией выкупа", 110, "Банк обязан выкупить за 120K"),
        ("Кумулятивная акция", 100, "Накопление дивидендов"),
        ("Акция для VIP", 200, "Владелец -- клиент банка"),
        ("Акция «Нефтяная»", 150, "Бонус к нефтяным проектам"),
        ("Акция «Золотая молодёжь»", 50, "Без голоса"),
        ("Акция с правом требования", 100, "Можно потребовать выкуп"),
        ("Акция безноминальная", 1, "1000 шт = 1KK капитала"),
        ("Акция с плавающим дивидендом", 100, "Дивиденд = % от прибыли"),
        ("Акция «Казначейская»", 100, "Принадлежит самому банку"),
    ]
    for name, nom, spec in akcii_data:
        cards.append(AkciyaCard(name=name, card_type=CardType.AKCIYA, nominal=nom, special=spec))
        # каждая акция в трёх экземплярах -- нет, по одной, всего 20

    # ВЕКСЕЛЯ (20)
    veksel_data = [
        ("Простой вексель", 50, 3, 10),
        ("Простой вексель", 100, 2, 8),
        ("Переводной (тратта)", 100, 4, 15),
        ("Казначейский", 200, 6, 12),
        ("Дружеский", 50, 2, 5),
        ("Бронзовый (фиктивный)", 100, 1, 20),
        ("С авалем", 150, 4, 10),
        ("Коммерческий", 80, 2, 12),
        ("Банковский акцепт", 200, 3, 8),
        ("С дисконтом", 100, 1, 15),
        ("Вексель нефтяной компании", 300, 5, 18),
        ("Вексель с отсрочкой", 150, 6, 14),
        ("Соло-вексель", 70, 2, 7),
        ("Вексель с залогом нефти", 250, 4, 20),
        ("Вексель с поручительством", 120, 3, 11),
        ("Вексель до востребования", 50, 1, 3),
        ("Вексель с индоссаментом", 100, 3, 13),
        ("Вексель «Экспортный»", 200, 5, 16),
        ("Вексель с пролонгацией", 80, 4, 9),
        ("Вексель «Золотой»", 500, 8, 25),
    ]
    for name, nom, srok, doh in veksel_data:
        cards.append(VekselCard(name=name, card_type=CardType.VEKSEL, nominal=nom, srok=srok, dohodnost=doh))

    # СОБЫТИЯ (44)
    event_data = [
        # Макроэкономика (11)
        (EventCategory.MACRO, "Ставка ЦБ +5%", "Все кредиты дорожают на 5%, депозиты выгоднее"),
        (EventCategory.MACRO, "Ставка ЦБ -5%", "Кредиты дешевле на 5%, депозиты менее выгодны"),
        (EventCategory.MACRO, "Инфляция 5%", "Касса теряет 5% реальной стоимости"),
        (EventCategory.MACRO, "Девальвация рубля -10%", "Если есть валюта -- +10% к рублёвому эквиваленту"),
        (EventCategory.MACRO, "Экономический рост", "+20K дохода по всем выданным кредитам"),
        (EventCategory.MACRO, "Рецессия", "-10K дохода по всем кредитам"),
        (EventCategory.MACRO, "Санкции против банков", "Корсчёт заморожен на 1 раунд"),
        (EventCategory.MACRO, "Иностранные инвестиции", "Можно привлечь депозит 300K под 3% на 4 раунда"),
        (EventCategory.MACRO, "Банковский кризис", "Все игроки теряют 20% кассы"),
        (EventCategory.MACRO, "Финансовая стабилизация", "Резервы можно снизить до 5%"),
        (EventCategory.MACRO, "Цена нефти взлетела!", "Все нефтяные проекты +50% дохода в этот раунд"),
        # Риски (11)
        (EventCategory.RISK, "Дефолт заёмщика", "Спишите 50K выданного кредита в убыток"),
        (EventCategory.RISK, "Дефолт нефтяной компании", "Спишите 200K -- нефтяной проект прогорел"),
        (EventCategory.RISK, "Отзыв лицензии у банка-партнёра", "Потеря 50K на корсчете"),
        (EventCategory.RISK, "Отток вкладчиков", "-15% депозитов"),
        (EventCategory.RISK, "Кража в банке", "-50K из кассы"),
        (EventCategory.RISK, "Пожар в хранилище", "-30K ущерб, ремонт 20K"),
        (EventCategory.RISK, "Авария на нефтяной вышке", "Один нефтяной проект не приносит доход"),
        (EventCategory.RISK, "Проблема с векселем", "Ваш выпущенный вексель предъявили досрочно"),
        (EventCategory.RISK, "Невозврат МБК", "-100K"),
        (EventCategory.RISK, "Репутационный кризис", "Нельзя привлекать депозиты 1 раунд"),
        (EventCategory.RISK, "Предупреждение ЦБ!", "Если резервы < 10% -- штраф 150K"),
        # Позитив (11)
        (EventCategory.POSITIVE, "Удачная сделка с векселем", "+40K дохода от дисконта"),
        (EventCategory.POSITIVE, "Продажа непрофильных активов", "+60K в кассу"),
        (EventCategory.POSITIVE, "Возврат просроченного кредита", "+80K (считали безнадёжным)"),
        (EventCategory.POSITIVE, "Снижение резервных требований", "Высвобождается 5% с корсчета"),
        (EventCategory.POSITIVE, "IPO успешное", "Акции дорожают на 20%"),
        (EventCategory.POSITIVE, "Слияние с мелким банком", "+100K активов, +30K обязательств"),
        (EventCategory.POSITIVE, "Дивиденды от дочек", "+50K в доход"),
        (EventCategory.POSITIVE, "Господдержка", "+100K субординированный кредит под 2%"),
        (EventCategory.POSITIVE, "Выигрыш тендера", "+30K комиссии за раунд (3 раунда)"),
        (EventCategory.POSITIVE, "Новое нефтяное месторождение", "Можно купить нефтяной проект со скидкой 30%"),
        (EventCategory.POSITIVE, "Премия «Лучший банк»", "+20K грант, репутация +10%"),
        # Операционка (11)
        (EventCategory.OPER, "Крупный корпоративный клиент", "+200K на расчётном счёте (депозит до востреб.)"),
        (EventCategory.OPER, "Просрочка по кредиту", "Один кредит не приносит доход в этом раунде"),
        (EventCategory.OPER, "Досрочное погашение", "+100K сейчас, но теряете будущие проценты"),
        (EventCategory.OPER, "Новый акционер", "Можно выпустить +2 акции вне очереди"),
        (EventCategory.OPER, "Технический сбой в ЦБ", "Платежи задерживаются на 1 ход"),
        (EventCategory.OPER, "Выгодный обмен валюты", "+15K от курсовой разницы"),
        (EventCategory.OPER, "Судебный иск от клиента", "-30K компенсации"),
        (EventCategory.OPER, "Партнёрство с финтехом", "Операционные расходы -10K/раунд на 3 раунда"),
        (EventCategory.OPER, "Аудит ЦБ", "Если резервы < 10% -- штраф 100K"),
        (EventCategory.OPER, "Лицензия на новые операции", "Векселя без ограничений на 2 раунда"),
        (EventCategory.OPER, "Филиал в нефтяном регионе", "-50K единоразово, +15K дохода/раунд"),
    ]
    for cat, name, effect in event_data:
        cards.append(SbytieCard(name=name, card_type=CardType.SOBYTIE, category=cat, effect_text=effect))

    # КОНТРАГЕНТЫ (30)
    dep_data = [
        ("Физлицо-вкладчик", 50, 3, 5.0),
        ("Физлицо-вкладчик", 100, 6, 7.0),
        ("Пенсионный фонд", 300, 8, 8.0),
        ("Страховая компания", 200, 4, 6.0),
        ("Нефтяная корпорация", 500, 2, 4.0),
        ("Муниципальное предприятие", 150, 5, 6.5),
        ("Инвестиционный фонд", 250, 3, 5.5),
        ("Депозит до востребования", 100, 0, 1.0),
        ("VIP-вкладчик", 400, 6, 9.0),
        ("Бюджетная организация", 180, 4, 5.0),
    ]
    for name, summa, srok, stavka in dep_data:
        cards.append(KontragentCard(name=name, card_type=CardType.KONTAGENT, kt_type=KontragentType.DEPOSIT, summa=summa, srok=srok, stavka=stavka))

    cred_data = [
        ("ИП Петров (нефтевозы)", 50, 2, 15.0, "Поручитель"),
        ("ООО «Бурнефть»", 100, 4, 12.0, "Залог оборудования"),
        ("АО «Нефтепром»", 300, 6, 10.0, "Скважины"),
        ("Физлицо ипотека", 200, 10, 9.0, "Квартира"),
        ("Малый бизнес (АЗС)", 80, 3, 14.0, "Оборудование"),
        ("Крупный корпоративный", 500, 8, 8.0, "Активы компании"),
        ("Потребительский", 30, 2, 18.0, "Без обеспечения"),
        ("Автокредит", 150, 5, 11.0, "Автомобиль"),
        ("МБК (межбанк)", 200, 1, 6.0, "Без обеспечения"),
        ("Кредитная линия", 400, 4, 9.0, "Оборотные средства"),
    ]
    for name, summa, srok, stavka, obesp in cred_data:
        cards.append(KontragentCard(name=name, card_type=CardType.KONTAGENT, kt_type=KontragentType.CREDIT, summa=summa, srok=srok, stavka=stavka, obespechenie=obesp))

    mej_data = [
        ("Кредит от банка-партнёра", 150, 2, 5.0),
        ("Рефинансирование ЦБ", 300, 3, 7.0),
        ("Депозит в другом банке", 100, 3, 4.0),
        ("Овердрафт по корсчету", 80, 1, 10.0),
        ("Синдицированный кредит", 500, 5, 6.0),
    ]
    for name, summa, srok, stavka in mej_data:
        cards.append(KontragentCard(name=name, card_type=CardType.KONTAGENT, kt_type=KontragentType.MEJBANK, summa=summa, srok=srok, stavka=stavka))

    other_data = [
        ("Платёжная система", KontragentType.OTHER, "Комиссионный доход 5K/раунд"),
        ("Аренда офиса", KontragentType.OTHER, "Расход 10K/раунд"),
        ("Инкассация", KontragentType.OTHER, "Расход 5K/раунд"),
        ("Обслуживание хранилища", KontragentType.OTHER, "Расход 3K/раунд"),
        ("Покупка банкоматов", KontragentType.OTHER, "-20K единоразово, +2K/раунд дохода"),
    ]
    for name, kt, desc in other_data:
        cards.append(KontragentCard(name=name, card_type=CardType.KONTAGENT, kt_type=kt, description=desc, summa=0, srok=0, stavka=0.0))

    # НЕФТЯНЫЕ ПРОЕКТЫ (10)
    neft_data = [
        ("Скважина «Сибирь-1»", 300, 80, "При аварии -200K", 200),
        ("Нефтепровод «Дружба-2»", 500, 120, "При санкциях -300K", 300),
        ("АЗС-сеть «Луна»", 200, 40, "При кризисе -100K", 100),
        ("Танкер «Чёрный бриллиант»", 400, 100, "При шторме -350K", 350),
        ("НПЗ «Восток»", 600, 150, "При аварии -400K", 400),
        ("Геологоразведка", 150, 30, "50% что пустая порода", 150),
        ("Нефтяная вышка «Окей»", 250, 60, "При пожаре -250K", 250),
        ("Бензохранилище", 180, 35, "При краже -90K", 90),
        ("Нефтяной терминал", 700, 180, "При кризисе -500K", 500),
        ("Лаборатория «Битум»", 120, 25, "При дефолте -60K", 60),
    ]
    for name, cost, dohod, risk_t, risk_l in neft_data:
        cards.append(NeftCard(name=name, card_type=CardType.NEFT, cost=cost, dohod=dohod, risk_text=risk_t, risk_loss=risk_l))

    return cards


# -----------------------------------------------------------------
# ГАЗЕТНЫЕ СТАТЬИ (15 шт -- краткий текст)
# -----------------------------------------------------------------

NEWSPAPER_ARTICLES = [
    ("Золотые часы кассира",
     "Пётр Ильич Сомов начинал инкассатором -- возил мешки с мелочью, "
     "пропахшие табаком. Но каждую ночь изучал банковское дело. "
     "Сегодня у него золотые часы от директора и 12 человек в подчинении. "
     "«Деньги любят счёт. И тишину».", C.YELLOW),
    ("Табачный король стал банкиром",
     "Семён Маркович Гольдман прошёл путь от лотка на рынке до кресла "
     "председателя банка. Секрет: «Знай свой товар, знай клиента, "
     "всегда имей запасную зажигалку». Его кабинет пропах табаком "
     "и деньгами.", C.BLUE),
    ("Вещи, которые научили его считать",
     "Финансовый директор Елена Ковалёва коллекционирует вещи. "
     "Каждая -- урок: «Бухгалтерия -- это не цифры. Это вещи, "
     "записанные цифрами». Золотые часы купила на первый "
     "международный аудит.", C.CYAN),
    ("Предупреждён -- значит вооружён",
     "Риск-менеджер Дмитрий Лосев не носит золотых часов. "
     "«Избыточная уверенность -- главный риск банка». Его отдел "
     "спас банк в кризис 1998 года.", C.RED),
    ("От табачного ларька до биржи",
     "Виктор Цой торговал сигаретами у метро. Сегодня -- директор "
     "департамента ценных бумаг. «Вместо папирос -- облигации, "
     "вместо сигарет -- акции. А звон монет тот же».", C.MAGENTA),
    ("Золотые часы -- залог стабильности",
     "Председатель банка Вершинин: «Когда клиент видит золотые часы, "
     "он понимает: банк надёжен». В кризис 1998 года его банк "
     "выжил, потому что Вершинин знал историю денег.", C.YELLOW),
    ("Вексельное обращение -- садовник денег",
     "Начальник вексельного отдела Дятлов: «Вексель -- живой организм. "
     "За ним надо ухаживать». Однажды чуть не потерял должность "
     "из-за ошибки в бланке. Теперь учит других.", C.GREEN),
    ("Операционистка с золотыми руками",
     "Валентина Зимина работает в банке 35 лет. Начинала на почте. "
     "«Компьютер сломается -- а ты должен знать предмет руками». "
     "Золотые часы -- подарок банка за верность.", C.BLUE),
    ("Как я учил банковское дело в Китае",
     "Павел Крымов изучал китайскую банковскую систему ночами. "
     "«У каждого народа -- свой подход к деньгам. Китайцы доверяют "
     "вещам: золото, табак, чай -- вот их валюта».", C.CYAN),
    ("История одного дефолта",
     "Александр Трофимов потерял банк из-за самонадеянности. "
     "«Я думал, что всё знаю. А знал только верхушку». "
     "Теперь преподаёт и предупреждает студентов о граблях.", C.RED),
    ("Табак, чай и банковская гарантия",
     "Глава отдела гарантий Чхеидзе изучал табачное дело полгода: "
     "ездил на плантации, смотрел, как сушат листья. "
     "«Знание бизнеса клиента -- 80% успеха».", C.MAGENTA),
    ("Как инвентаризация спасла банк",
     "Главбух Фролова обнаружила недостачу на 200KK. Внедрила "
     "новую систему учёта -- и банк прошёл аудит без замечаний. "
     "Золотые часы: «За порядок в активах».", C.YELLOW),
    ("Межбанковский кредит: история взаимовыручки",
     "Четыре банкира спасли коллегу межбанковским кредитом. "
     "«Мы дали деньги, потому что видели: человек знает дело». "
     "В благодарность -- золотые часы каждому.", C.GREEN),
    ("Депозит под табак",
     "Иван Кузнецов вырос в деревне. Сегодня -- председатель "
     "банка «Земельный». «Деньги в городе звенят в кошельке, "
     "а в деревне -- в налитом колосе».", C.BLUE),
    ("Дивиденды успеха",
     "Рашид Султанов на первую прибыль купил золотые часы. "
     "«Не понты -- первый актив, заработанный знанием». "
     "Коллекционирует часы: 15 штук, каждые -- история.", C.CYAN),
]

# -----------------------------------------------------------------
# ИГРОК
# -----------------------------------------------------------------

@dataclass
class Contract:
    """Активный договор (кредит/депозит/вексель/проект)"""
    name: str
    ctype: str  # 'credit', 'deposit', 'veksel_asset', 'veksel_liability', 'neft'
    summa: int
    rate: float
    srok_total: int
    srok_left: int
    income_per_round: int = 0  # для кредитов
    expense_per_round: int = 0  # для депозитов

@dataclass
class Player:
    name: str
    cash: int = 0  # касса
    vault: bool = False  # есть хранилище
    vault_cost: int = 50  # стоимость хранилища
    korchet: int = 0  # корсчёт в ЦБ
    share_capital: int = 0  # акционерный капитал
    shares_issued: int = 0  # выпущено акций
    contracts: list = field(default_factory=list)
    neft_projects: list = field(default_factory=list)  # имена проектов
    hand: list = field(default_factory=list)
    reputation: int = 100
    bankrupt: bool = False
    profit: int = 0  # прибыль за последний расчёт
    total_profit: int = 0  # накопленная прибыль
    dividends_paid: int = 0

    @property
    def total_assets(self) -> int:
        assets = self.cash + self.korchet
        if self.vault:
            assets += self.vault_cost
        for c in self.contracts:
            if c.ctype in ('credit', 'veksel_asset', 'neft'):
                assets += c.summa
        return assets

    @property
    def total_liabilities(self) -> int:
        liab = 0
        for c in self.contracts:
            if c.ctype in ('deposit', 'veksel_liability'):
                liab += c.summa
        return liab + self.share_capital

    @property
    def capital(self) -> int:
        return self.total_assets - self.total_liabilities

# -----------------------------------------------------------------
# ИГРА
# -----------------------------------------------------------------

class Game:
    def __init__(self):
        self.players: list[Player] = []
        self.round = 0
        self.max_rounds = 10
        self.deck: list[Card] = []
        self.discard: list[Card] = []
        self.event_deck: list[SbytieCard] = []
        self.event_discard: list[SbytieCard] = []
        self.contract_deck: list[KontragentCard] = []
        self.neft_deck: list[NeftCard] = []
        self.current_player_idx = 0
        self.game_over = False

    def setup(self):
        print(C.BOLD + C.WHITE + "\n" + "#" * 60 + C.END)
        print(C.BOLD + C.GREEN + "   БАНКЪ & НЕФТЬ" + C.END)
        print(C.BOLD + C.WHITE + "   Карточная игра о банках, нефти и большой прибыли" + C.END)
        print(C.WHITE + "#" * 60 + C.END)

        # Сколько игроков
        while True:
            try:
                n = int(input(C.CYAN + "\nСколько игроков? (2-4): " + C.END))
                if 2 <= n <= 4:
                    break
                print("От 2 до 4.")
            except:
                print("Введите число.")

        # Создание игроков
        for i in range(n):
            name = input(f"Имя игрока {i+1}: ").strip()
            if not name:
                name = f"Игрок {i+1}"
            p = Player(name=name)
            self.players.append(p)

        # Сборка хранилищ и капитализация
        print(C.YELLOW + "\n--- СБОРКА ХРАНИЛИЩ И КАПИТАЛИЗАЦИЯ ---" + C.END)
        for p in self.players:
            print(f"\n{C.BOLD}{p.name}{C.END}, ваш банк создаётся.")
            while True:
                try:
                    shares = int(input(f"  Сколько акций покупаете? (1-5 по 100K каждая): "))
                    if 1 <= shares <= 5:
                        break
                    print("От 1 до 5.")
                except:
                    print("Введите число.")

            p.share_capital = shares * 100
            p.shares_issued = shares
            p.vault = True
            p.cash = p.share_capital - p.vault_cost
            p.korchet = int(p.share_capital * 0.1)
            p.cash -= p.korchet

            print(f"  {C.GREEN}Хранилище собрано!{C.END}")
            print(f"  Акционерный капитал: {C.BOLD}{p.share_capital}K{C.END}")
            print(f"  Хранилище: -50K")
            print(f"  Резерв ЦБ: -{p.korchet}K")
            print(f"  Касса (в хранилище): {C.BOLD}{p.cash}K{C.END}")

        # Создание колод
        all_cards = create_deck()
        random.shuffle(all_cards)
        self.deck = all_cards

        # Разделяем на колоды
        self.event_deck = [c for c in all_cards if c.card_type == CardType.SOBYTIE]
        self.contract_deck = [c for c in all_cards if c.card_type == CardType.KONTAGENT]
        self.neft_deck = [c for c in all_cards if c.card_type == CardType.NEFT]
        # Акции и векселя остаются в общей колоде

        random.shuffle(self.event_deck)
        random.shuffle(self.contract_deck)
        random.shuffle(self.neft_deck)

        # Стартовые карты в руку
        for p in self.players:
            if self.event_deck:
                p.hand.append(self.event_deck.pop())
            if self.contract_deck:
                p.hand.append(self.contract_deck.pop())

        print(C.YELLOW + "\n--- ИГРА НАЧИНАЕТСЯ! ---" + C.END)
        input(C.BLACK + "\nНажмите Enter..." + C.END)

    def show_balance(self, p: Player):
        print(f"\n{C.BOLD}{C.CYAN}-- Баланс банка «{p.name}» --{C.END}")
        print(f"  {C.GREEN}АКТИВЫ:{C.END}")
        print(f"    Касса:                        {p.cash:>6}K")
        print(f"    Хранилище:                    {p.vault_cost if p.vault else 0:>6}K")
        print(f"    Корсчёт в ЦБ:                 {p.korchet:>6}K")
        creds = sum(c.summa for c in p.contracts if c.ctype == 'credit')
        v_asset = sum(c.summa for c in p.contracts if c.ctype == 'veksel_asset')
        neft = sum(c.summa for c in p.contracts if c.ctype == 'neft')
        if creds: print(f"    Выданные кредиты:             {creds:>6}K")
        if v_asset: print(f"    Приобретённые векселя:        {v_asset:>6}K")
        if neft: print(f"    Нефтяные проекты:             {neft:>6}K")
        print(f"    {C.BOLD}ИТОГО АКТИВЫ:                 {p.total_assets:>6}K{C.END}")

        print(f"  {C.RED}ПАССИВЫ:{C.END}")
        print(f"    Акционерный капитал:           {p.share_capital:>6}K")
        deps = sum(c.summa for c in p.contracts if c.ctype == 'deposit')
        v_liab = sum(c.summa for c in p.contracts if c.ctype == 'veksel_liability')
        if deps: print(f"    Привлечённые депозиты:        {deps:>6}K")
        if v_liab: print(f"    Выпущенные векселя:           {v_liab:>6}K")
        print(f"    {C.BOLD}ИТОГО ПАССИВЫ:                {p.total_liabilities:>6}K{C.END}")
        print(f"  {C.YELLOW}------------------------------{C.END}")
        cap_color = C.GREEN if p.capital >= 0 else C.RED
        print(f"  {cap_color}СОБСТВЕННЫЙ КАПИТАЛ:           {p.capital:>6}K{C.END}")
        print(f"  Репутация: {p.reputation}% | Прибыль за раунд: {p.profit:+d}K")

    def show_hand(self, p: Player):
        print(f"\n{C.BOLD}Рука {p.name}:{C.END}")
        if not p.hand:
            print("  (пусто)")
            return
        for i, card in enumerate(p.hand):
            ct = card.card_type.value
            col = C.GREEN if card.card_type == CardType.AKCIYA else \
                  C.BLUE if card.card_type == CardType.VEKSEL else \
                  C.RED if card.card_type == CardType.SOBYTIE else \
                  C.YELLOW if card.card_type == CardType.KONTAGENT else C.MAGENTA
            print(f"  {i+1}. {col}{card.name}{C.END} [{ct}]")

    def draw_event(self, p: Player) -> Optional[SbytieCard]:
        if not self.event_deck:
            self.event_deck, self.event_discard = self.event_discard, []
            random.shuffle(self.event_deck)
            if not self.event_deck:
                return None
        card = self.event_deck.pop()
        print(f"\n{C.RED}=== СОБЫТИЕ: {card.name} ==={C.END}")
        print(f"  {card.effect_text}")
        self.event_discard.append(card)
        return card

    def apply_event(self, p: Player, event: SbytieCard):
        name = event.name
        # Макро
        if name == "Ставка ЦБ +5%":
            for c in p.contracts:
                if c.ctype in ('credit', 'deposit'):
                    c.rate += 5
        elif name == "Ставка ЦБ -5%":
            for c in p.contracts:
                if c.ctype in ('credit', 'deposit'):
                    c.rate = max(0, c.rate - 5)
        elif name == "Инфляция 5%":
            p.cash = int(p.cash * 0.95)
        elif name == "Девальвация рубля -10%":
            # упрощённо: +5% к капиталу
            p.cash = int(p.cash * 1.05)
        elif name == "Экономический рост":
            for c in p.contracts:
                if c.ctype == 'credit':
                    c.income_per_round += 20
        elif name == "Рецессия":
            for c in p.contracts:
                if c.ctype == 'credit':
                    c.income_per_round = max(0, c.income_per_round - 10)
        elif name == "Санкции против банков":
            p.korchet = 0
        elif name == "Иностранные инвестиции":
            p.cash += 300
            p.contracts.append(Contract("Иностранный депозит", "deposit", 300, 3.0, 4, 4, expense_per_round=9))
        elif name == "Банковский кризис":
            p.cash = int(p.cash * 0.8)
        elif name == "Финансовая стабилизация":
            pass  # бонус игроку на выбор (упрощённо)
        elif name == "Цена нефти взлетела!":
            for c in p.contracts:
                if c.ctype == 'neft':
                    c.income_per_round = int(c.income_per_round * 1.5)
        # Риски
        elif name == "Дефолт заёмщика":
            for c in p.contracts:
                if c.ctype == 'credit' and c.summa <= 50:
                    p.contracts.remove(c)
                    p.cash -= 50
                    break
        elif name == "Дефолт нефтяной компании":
            for c in p.contracts:
                if c.ctype == 'neft':
                    p.contracts.remove(c)
                    p.cash -= 200
                    break
        elif name == "Отзыв лицензии у банка-партнёра":
            p.cash -= 50
        elif name == "Отток вкладчиков":
            for c in p.contracts[:]:
                if c.ctype == 'deposit':
                    p.cash -= int(c.summa * 0.15)
                    c.srok_left -= 1
        elif name == "Кража в банке":
            p.cash = max(0, p.cash - 50)
        elif name == "Пожар в хранилище":
            p.cash -= 30
            if p.cash < 0: p.cash = 0
        elif name == "Авария на нефтяной вышке":
            for c in p.contracts:
                if c.ctype == 'neft':
                    c.income_per_round = 0
                    break
        elif name == "Проблема с векселем":
            for c in p.contracts:
                if c.ctype == 'veksel_liability':
                    c.srok_left = 1
                    break
        elif name == "Невозврат МБК":
            p.cash -= 100
        elif name == "Репутационный кризис":
            p.reputation = max(0, p.reputation - 20)
        elif name == "Предупреждение ЦБ!":
            if p.korchet < int(p.share_capital * 0.1):
                p.cash -= 150
        # Позитив
        elif name == "Удачная сделка с векселем":
            p.cash += 40
        elif name == "Продажа непрофильных активов":
            p.cash += 60
        elif name == "Возврат просроченного кредита":
            p.cash += 80
        elif name == "Снижение резервных требований":
            freed = int(p.korchet * 0.05)
            p.cash += freed
            p.korchet -= freed
        elif name == "IPO успешное":
            bonus = int(p.share_capital * 0.2)
            p.share_capital += bonus
            p.cash += bonus
        elif name == "Слияние с мелким банком":
            p.cash += 100
        elif name == "Дивиденды от дочек":
            p.cash += 50
        elif name == "Господдержка":
            p.cash += 100
            p.contracts.append(Contract("Господдержка", "credit", 100, 2.0, 5, 5, income_per_round=2))
        elif name == "Выигрыш тендера":
            p.cash += 30
        elif name == "Новое нефтяное месторождение":
            if self.neft_deck:
                neft_card = self.neft_deck.pop()
                p.hand.append(neft_card)
                print(f"  {C.MAGENTA}Получена карта: {neft_card.name}{C.END}")
        elif name == "Премия «Лучший банк»":
            p.cash += 20
            p.reputation = min(100, p.reputation + 10)
        # Операционка
        elif name == "Крупный корпоративный клиент":
            p.cash += 200
        elif name == "Просрочка по кредиту":
            for c in p.contracts:
                if c.ctype == 'credit':
                    c.income_per_round = 0
                    break
        elif name == "Досрочное погашение":
            p.cash += 100
        elif name == "Новый акционер":
            p.share_capital += 200
            p.shares_issued += 2
        elif name == "Технический сбой в ЦБ":
            pass
        elif name == "Выгодный обмен валюты":
            p.cash += 15
        elif name == "Судебный иск от клиента":
            p.cash -= 30
        elif name == "Партнёрство с финтехом":
            pass
        elif name == "Аудит ЦБ":
            if p.korchet < int(p.share_capital * 0.1):
                p.cash -= 100
        elif name == "Лицензия на новые операции":
            pass
        elif name == "Филиал в нефтяном регионе":
            p.cash -= 50
            # доход в расчётах

        if p.cash < 0:
            p.cash = 0

    def do_calculations(self, p: Player):
        """Расчёты в конце хода"""
        profit = 0
        # Доход по кредитам
        for c in p.contracts[:]:
            if c.ctype == 'credit':
                inc = int(c.summa * c.rate / 100)
                profit += inc
                c.income_per_round = inc
                c.srok_left -= 1
                if c.srok_left <= 0:
                    p.cash += c.summa + inc
                    p.contracts.remove(c)
                    print(f"  {C.GREEN}Кредит «{c.name}» погашен: +{c.summa + inc}K{C.END}")
            elif c.ctype == 'deposit':
                exp = int(c.summa * c.rate / 100)
                profit -= exp
                c.expense_per_round = exp
                p.cash -= exp
                c.srok_left -= 1
                if c.srok_left <= 0:
                    p.cash -= c.summa
                    p.contracts.remove(c)
                    print(f"  {C.RED}Депозит «{c.name}» выплачен: -{c.summa + exp}K{C.END}")
            elif c.ctype == 'veksel_asset':
                inc = int(c.summa * c.rate / 100)
                profit += inc
                c.srok_left -= 1
                if c.srok_left <= 0:
                    p.cash += c.summa + inc
                    p.contracts.remove(c)
                    print(f"  {C.GREEN}Вексель «{c.name}» погашен: +{c.summa + inc}K{C.END}")
            elif c.ctype == 'veksel_liability':
                exp = int(c.summa * c.rate / 100)
                profit -= exp
                c.srok_left -= 1
                if c.srok_left <= 0:
                    p.cash -= c.summa + exp
                    p.contracts.remove(c)
                    print(f"  {C.RED}Ваш вексель «{c.name}» оплачен: -{c.summa + exp}K{C.END}")
            elif c.ctype == 'neft':
                profit += c.income_per_round
                p.cash += c.income_per_round
                print(f"  {C.MAGENTA}Нефтяной проект «{c.name}»: +{c.income_per_round}K{C.END}")

        # Расходы на хранилище
        if p.vault:
            p.cash -= 3
            profit -= 3

        p.profit = profit
        p.total_profit += profit

    def player_turn(self, p: Player):
        print(C.BOLD + C.WHITE + f"\n{'=' * 50}" + C.END)
        print(C.BOLD + C.GREEN + f"  ХОД: {p.name}  |  Раунд {self.round}/{self.max_rounds}" + C.END)
        print(C.WHITE + f"{'=' * 50}" + C.END)

        # Показать баланс
        self.show_balance(p)

        # Фаза 1: Событие
        input(C.BLACK + "  Нажмите Enter, чтобы тянуть Событие..." + C.END)
        event = self.draw_event(p)
        if event:
            self.apply_event(p, event)
            print(f"  Касса после события: {C.BOLD}{p.cash}K{C.END}")

        # Фаза 2: Действия (до 3)
        actions_left = 3
        while actions_left > 0:
            print(f"\n{C.CYAN}Действий осталось: {actions_left}{C.END}")
            print(f"  1. Показать руку и сыграть карту")
            print(f"  2. Выпустить вексель")
            print(f"  3. Выпустить акции")
            print(f"  4. Показать баланс")
            print(f"  5. Читать газету (флаф)")
            print(f"  6. Закончить ход")

            choice = input("  Ваш выбор: ").strip()

            if choice == '1':
                self.show_hand(p)
                if not p.hand:
                    input("  Рука пуста. Enter..." + C.END)
                    continue
                try:
                    ci = int(input("  Номер карты: ")) - 1
                    if 0 <= ci < len(p.hand):
                        card = p.hand.pop(ci)
                        self.play_card(p, card)
                        actions_left -= 1
                    else:
                        print("  Неверный номер.")
                except:
                    print("  Ошибка.")

            elif choice == '2':
                print(f"  {C.BLUE}Выпуск векселя:{C.END}")
                nom = int(input("  Номинал (50-500K): ") or "100")
                rate = int(input("  Доходность %: ") or "10")
                srok = int(input("  Срок (раундов): ") or "3")
                name = input("  Название векселя: ") or f"Вексель #{random.randint(100,999)}"
                p.contracts.append(Contract(name, "veksel_liability", nom, rate, srok, srok))
                p.cash += nom
                print(f"  {C.GREEN}Вексель выпущен! +{nom}K в кассу{C.END}")
                actions_left -= 1

            elif choice == '3':
                print(f"  {C.GREEN}Допэмиссия акций:{C.END}")
                cnt = int(input("  Сколько акций выпустить? (1-5): ") or "1")
                cnt = max(1, min(5, cnt))
                gain = cnt * 100
                p.share_capital += gain
                p.shares_issued += cnt
                p.cash += gain
                print(f"  {C.GREEN}+{cnt} акций, капитал +{gain}K{C.END}")
                actions_left -= 1

            elif choice == '4':
                self.show_balance(p)

            elif choice == '5':
                self.show_newspaper(p)

            elif choice == '6':
                break

        # Фаза 3: Расчёты
        print(f"\n{C.CYAN}-- Расчёты --{C.END}")
        self.do_calculations(p)
        print(f"  {C.BOLD}Баланс после расчётов: касса {p.cash}K, капитал {p.capital}K{C.END}")

        # Проверка банкротства
        if p.capital < 0:
            print(C.RED + f"\n  ⚠ {p.name}: КАПИТАЛ ОТРИЦАТЕЛЬНЫЙ! БАНКРОТСТВО!" + C.END)
            p.bankrupt = True
            self.game_over = True

        input(C.BLACK + "  Enter, чтобы передать ход..." + C.END)

    def play_card(self, p: Player, card: Card):
        if isinstance(card, KontragentCard):
            if card.kt_type == KontragentType.CREDIT:
                p.contracts.append(Contract(card.name, "credit", card.summa, card.stavka, card.srok, card.srok, income_per_round=int(card.summa * card.stavka / 100)))
                p.cash -= card.summa
                print(f"  {C.GREEN}Кредит выдан «{card.name}»: -{card.summa}K{C.END}")
            elif card.kt_type == KontragentType.DEPOSIT:
                p.contracts.append(Contract(card.name, "deposit", card.summa, card.stavka, card.srok if card.srok > 0 else 999, card.srok if card.srok > 0 else 999, expense_per_round=int(card.summa * card.stavka / 100)))
                p.cash += card.summa
                print(f"  {C.YELLOW}Депозит привлечён «{card.name}»: +{card.summa}K{C.END}")
            elif card.kt_type == KontragentType.MEJBANK:
                p.contracts.append(Contract(card.name, "credit", card.summa, card.stavka, card.srok, card.srok, income_per_round=0))
                p.cash += card.summa
                print(f"  {C.CYAN}Межбанковский кредит: +{card.summa}K{C.END}")
            else:
                print(f"  {C.BLACK}Контрагент «{card.name}»: {card.description}{C.END}")

        elif isinstance(card, NeftCard):
            if p.cash >= card.cost:
                p.cash -= card.cost
                p.contracts.append(Contract(card.name, "neft", card.cost, 0, 999, 999, income_per_round=card.dohod))
                print(f"  {C.MAGENTA}Нефтяной проект «{card.name}» куплен! -{card.cost}K, доход +{card.dohod}K/раунд{C.END}")
            else:
                print(f"  {C.RED}Не хватает денег! Нужно {card.cost}K, есть {p.cash}K{C.END}")
                p.hand.append(card)

        elif isinstance(card, AkciyaCard):
            print(f"  {C.GREEN}Акция «{card.name}» -- можно продать или оставить{C.END}")
            p.hand.append(card)

        elif isinstance(card, VekselCard):
            # Купить вексель
            if p.cash >= card.nominal:
                p.cash -= card.nominal
                p.contracts.append(Contract(card.name, "veksel_asset", card.nominal, card.dohodnost, card.srok, card.srok))
                print(f"  {C.BLUE}Вексель куплен «{card.name}»: -{card.nominal}K, доход {card.dohodnost}%{C.END}")
            else:
                print(f"  {C.RED}Не хватает денег!{C.END}")
                p.hand.append(card)

        elif isinstance(card, SbytieCard):
            # Событие можно отложить или применить сейчас
            print(f"  {C.RED}Событие «{card.name}» применено.{C.END}")
            self.apply_event(p, card)

    def show_newspaper(self, p: Player):
        if not NEWSPAPER_ARTICLES:
            print("  Газет нет.")
            return
        print(f"\n{C.BOLD}{C.YELLOW}=== ГАЗЕТА ==={C.END}")
        for i, (title, text, color) in enumerate(NEWSPAPER_ARTICLES):
            print(f"  {i+1}. {color}{title}{C.END}")
        try:
            ci = int(input("  Какую статью читать? (0 -- назад): ")) - 1
            if 0 <= ci < len(NEWSPAPER_ARTICLES):
                title, text, color = NEWSPAPER_ARTICLES[ci]
                print(f"\n{color}{C.BOLD}--- {title} ---{C.END}")
                print(f"{color}{text}{C.END}")
                print(f"{color}--------------{C.END}")
                input(C.BLACK + "  Enter..." + C.END)
        except:
            pass

    def dividend_round(self):
        print(C.BOLD + C.YELLOW + f"\n=== ДИВИДЕНДЫ (раунд {self.round}) ===" + C.END)
        for p in self.players:
            if p.bankrupt: continue
            if p.total_profit > 0:
                div = int(p.total_profit * 0.1)
                p.cash -= div
                p.dividends_paid += div
                p.total_profit -= div
                print(f"  {p.name}: выплачено дивидендов {div}K")
            else:
                print(f"  {p.name}: прибыли нет, дивиденды не платятся")

    def shareholder_meeting(self):
        print(C.BOLD + C.MAGENTA + f"\n=== СОБРАНИЕ АКЦИОНЕРОВ (раунд {self.round}) ===" + C.END)
        for p in self.players:
            if p.bankrupt: continue
            votes = sum(1 for c in p.contracts if c.ctype == 'deposit') + p.shares_issued
            print(f"  {p.name}: {votes} голосов")
        print("  Собрание прошло. Стратегия утверждена.")

    def play(self):
        self.setup()

        for self.round in range(1, self.max_rounds + 1):
            if self.game_over:
                break

            print(C.BOLD + C.WHITE + f"\n{'#' * 60}" + C.END)
            print(C.BOLD + C.GREEN + f"  РАУНД {self.round}/{self.max_rounds}" + C.END)
            print(C.WHITE + f"{'#' * 60}" + C.END)

            # Дивиденды каждые 3 раунда
            if self.round % 3 == 0:
                self.dividend_round()

            # Собрание каждые 5 раундов
            if self.round % 5 == 0:
                self.shareholder_meeting()

            # Ходы игроков
            for p in self.players:
                if p.bankrupt:
                    continue
                self.player_turn(p)
                if self.game_over:
                    break

            # Проверка: если все банкроты
            alive = [p for p in self.players if not p.bankrupt]
            if len(alive) <= 1:
                break

        # ИТОГ
        self.show_final()

    def show_final(self):
        print(C.BOLD + C.WHITE + f"\n{'#' * 60}" + C.END)
        print(C.BOLD + C.GREEN + "  ИГРА ОКОНЧЕНА!" + C.END)
        print(C.WHITE + f"{'#' * 60}" + C.END)

        results = sorted(self.players, key=lambda p: p.capital, reverse=True)
        for i, p in enumerate(results):
            status = C.GREEN if not p.bankrupt else C.RED
            print(f"\n  {i+1}. {status}{C.BOLD}{p.name}{C.END}")
            print(f"     Капитал: {p.capital}K  |  Касса: {p.cash}K")
            print(f"     Акций выпущено: {p.shares_issued}  |  Дивидендов выплачено: {p.dividends_paid}K")
            print(f"     Репутация: {p.reputation}%")
            if p.bankrupt:
                print(f"     {C.RED}БАНКРОТ{C.END}")

        winner = results[0]
        print(C.BOLD + C.YELLOW + f"\n  ПОБЕДИТЕЛЬ: {winner.name} с капиталом {winner.capital}K!" + C.END)
        print(C.YELLOW + "  «Звените деньгами, господа банкиры!»" + C.END)
        print(C.WHITE + f"{'#' * 60}\n" + C.END)


# -----------------------------------------------------------------
# ЗАПУСК
# -----------------------------------------------------------------

def main():
    try:
        game = Game()
        game.play()
    except KeyboardInterrupt:
        print(f"\n{C.RED}Игра прервана.{C.END}")
        sys.exit(0)

if __name__ == "__main__":
    main()
