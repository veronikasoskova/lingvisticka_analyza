# ==========================================================
# IQ1. KONŠTANTY
# ==========================================================

INTENTION_VALUES = {
    "warning",
    "commanding",
    "promising",
    "persuading",
    "declaring",
    "justifying",
    "questioning",
    "condemning",
    "praising",
    "mobilizing",
    "legitimation",
    "ideological_contestation",
    "intervention",
    "record",
    "narrative",
}

ILLOCUTIONARY_FORCE_VALUES = {
    "assertive",
    "directive",
    "commissive",
    "expressive",
    "declarative",
}

ILLOCUTIONARY_FORCE_MAP = {
    "declaring":                "assertive",
    "justifying":               "assertive",
    "persuading":               "assertive",
    "commanding":               "directive",
    "warning":                  "directive",
    "mobilizing":               "directive",
    "questioning":              "directive",
    "promising":                "commissive",
    "praising":                 "expressive",
    "condemning":               "expressive",
    "legitimation":             "declarative",
    "ideological_contestation": "declarative",
    "intervention":             "declarative",
    "record":                   "assertive",
    "narrative":                "assertive",
}

RHETORICAL_STRATEGY_VALUES = {
    "appeal_to_authority",
    "appeal_to_scripture",
    "appeal_to_tradition",
    "direct_address",
    "rhetorical_question",
    "conditional_threat",
    "promise_of_reward",
    "contrast",
    "repetition",
    "narrative_example",
}


# ==========================================================
# IQ2. LEXIKÓNY
# ==========================================================

WARNING_CONDITION_LEMMAS = {
    "jestliže",
    "pakliť",    # Stanza lemma od "Pakli" (BKR forma) — potvrdené v DB; pakliže sa v BKR nevyskytuje
    "kdož",
    "kdožkoli",
    "kdo",       # "Kdo nepřijme / Kdo neposlechne" — relativizačná podmienková štruktúra
    "li",        # kondicionálna enklitika — "nebudeš-li", "budeš-li" → tokenizér: "li"
    # "nebudeš", "nebudete" odstránené — Stanza lemmatizuje na "být" (AUX), nikdy nie nebudeš/nebudete
    # English (ewt)
    "if", "unless", "lest", "except", "whosoever", "whoever",
}

WARNING_OUTCOME_LEMMAS = {
    "zahynout",
    "zahynét",       # tvar produkovaný lemmatizérom z "zahynete/zahyneš"
    # "zahubiti" odstránené — archaický inf., Stanza → zahubit (nižšie)
    "zahubit",
    "odsoudit",
    "odsouzený",
    "zatratit",
    "zatracený",     # pasívne particípium — lemmatizér vracia ADJ formu
    # "uvrhnouti" odstránené — archaický inf., Stanza → uvrhnout (nižšie)
    "uvrhnout",
    "potrestat",
    "potrestaný",
    # English (ewt)
    "perish", "die", "fall", "condemn", "punish", "destroy", "lose", "fail",
}

WARNING_JUDGMENT_LEMMAS = {
    "soud",
    "odsouzení",
    "trest",
    "pomsta",
    "hněv",
    "prokletí",
    # "záhuba" nahradené — Stanza: záhubce → záhubka (potvrdené v DB)
    "záhubka",
    "peklo",
    # "gehenna" odstránené — NOT FOUND v celej BKR; nahradené peklo+oheň (oba ✓)
    "oheň",
    # "sekyra" nahradené — Stanza: sekeru/sekery → sekera (potvrdené 2× v dep CSV)
    "sekera",     # "sekyra přiložena ke kořeni" — Stanza: sekera
}

WARNING_PREVENTIVE_LEMMAS = {
    "varovat",
    "varuj",    # skutočná Stanza lemma od "Varuj" (imp. sg.) — nie "varovat"
    "střežit",
    "střez",    # imperativ od střežit — lemmatizér vracia "střez" (nie "střežit")
    "bdít",
    "hledět",
    "dbát",
    # English (ewt)
    "beware", "heed", "watch", "guard", "take care", "warn",
}

BĚDA_LEMMAS = {
    "běda",
}

CONDEMNING_PROPHETIC_LEMMAS = {
    "běda",
}

CONDEMNING_ACCUSATION_LEMMAS = {
    "ďábel",
    "hřích",
    "bezbožný",
    "bezbožnost",    # lemmatizér z "bezbožnosti" → bezbožnost (NOUN)
    "ničema",
    "falešný",
    "zlý",
    "zlost",         # lemmatizér z "zlosti" → zlost (NOUN)
    "nepravý",
    "svůdce",
}

CONDEMNING_VIOLATION_LEMMAS = {
    "přestoupit",
    "porušit",
    "nedbat",
    "neposlechnut",
    "odpadnout",
    "zhřešit",
}

CONDEMNING_JUDGMENT_LEMMAS = {
    "odsoudit",
    "proklít",
    "proklet",       # lemmatizér z "prokleje" → proklet (alternatívny tvar)
    "proklat",       # Stanza lemma potvrdené v DB ✓
    "proklatý",      # Stanza ADJ forma potvrdené v DB ✓ ("proklatý člověk")
    "prokletí",      # Stanza NOUN forma — "toto prokletí" ✓
    "zavrhnout",
    "zavržet",       # lemmatizér z "zavrže" → zavržet (alternatívny infinitív)
    "potrestat",
    "soud",
}

CONDEMNING_LABEL_LEMMAS = {
    "pokrytec",
    "pokrytství",    # Stanza lemma pre pokrytci/pokrytce, potvrdené v DB ✓
    "hříšník",
    "zákoník",
    "písař",         # BKR forma pre zákoník: písaři/písařů → Stanza: písař ✓
    "farizeus",
    "farizejský",    # Stanza ADJ forma: farizejští/farizejské → farizejský ✓
}

PRAISING_DIRECT_LEMMAS = {
    "chválit",
    "velebit",
    "oslavit",
    "požehnaný",
    "blahoslavený",
    "slavný",
    "svatý",
    # English (ewt)
    "praise", "glorify", "bless", "blessed", "holy", "sacred", "exalt",
    "worthy", "great", "glorious", "divine", "worship",
}

PRAISING_DOXOLOGY_LEMMAS = {
    "sláva",
    "čest",
    "moc",
    "velebnost",
    "věk",
    "amen",
}

PRAISING_ATTRIBUTE_LEMMAS = {
    "mocný",
    "věrný",
    "spravedlivý",
    "milosrdný",
    "dobrotivý",
    "milostivý",
    "chvalitebný",
}

PRAISING_HYMNIC_LEMMAS = {
    "zpívat",
    "haleluja",
    "oslavovat",
    "děkovat",
}

PRAISING_CONFESSION_LEMMAS = {
    "láska",
    "milosrdenství",
    "věrnost",
    "trvat",
}

MOBILIZING_MOVEMENT_LEMMAS = {
    "jít",
    "pojít",
    "vstát",
    "přijít",
    "běžet",
    "nést",
    "šířit",
}

MOBILIZING_MISSIONARY_LEMMAS = {
    "kázat",
    "kažit",     # Stanza lemma od "kažte" (imp. pl. kázat) — potvrdené v dep CSV ✓
    "učit",
    "křtit",     # Stanza: křtil → křtit (bez prízvuku) — potvrdené v dep CSV ✓
    # "křtít" nahradené → křtit; "křít" odstránené — nepotvrdené, Stanza → křtit
    "zvěstovat",
    "hlásat",
    "svědčit",
    # "svědčít" odstránené — Stanza → svědčit (bez prízvuku, ✓ v DB)
}

MOBILIZING_COLLECTIVE_LEMMAS = {
    "my",
    "bojovat",
    # "vytrvat" vynechané — "kdo vytrvají" → FP pri declaring/promising kontextoch
    "pracovat",
}

MOBILIZING_URGENCY_LEMMAS = {
    "přibližovat",
    "blízko",
    "brzy",
    "hle",
}

MOBILIZING_COMMISSION_LEMMAS = {
    "poslat",
    "posílat",   # imperfektívny variant — lemmatizér z "posílá" → posílat
    "poslaný",   # ADJ pasívne particípium — lemmatizér z "poslaný" → poslaný
    "pověřit",
}

COMMANDING_LEMMAS = {
    "činit",
    "jít",
    "pojít",
    "vzít",
    "nést",
    "zachovávat",
    "plnit",
    "poslouchat",
    # English (ewt)
    "shall", "must", "obey", "keep", "do", "go", "take", "bring",
    "follow", "seek", "come", "give", "make", "let",
}

COMMANDING_PROHIBITION_LEMMAS = {
    "zabít",
    "krást",
    "cizoložit",
    "neposlouchat",
}

COMMANDING_NORMATIVE_LEMMAS = {
    "přikázání",
    "zákon",
    "nařízení",
    "ustanovení",
    "povinnost",
}

COMMANDING_DEONTIC_LEMMAS = {
    "muset",
    "mít",
    "dlužen",
    "povinen",
    # English (ewt)
    "must", "shall", "ought", "need", "have",
}

QUESTIONING_MARKER_LEMMAS = {
    "což",
    "zdali",
    "zdaliž",
    "kterak",
    "jak",
    "proč",
    "kdo",
    "co",
    "kde",
    "kdy",
    "přivázat",
    "povolat",
    "svobodný",
    "služebník",
    # English (ewt)
    "what", "who", "how", "why", "where", "when", "which", "doth",
    "hath", "can", "could", "whether",
}

QUESTIONING_POSSIBILITY_LEMMAS = {
    "moci",
    "obstát",
    "možný",
}

QUESTIONING_IRONIC_LEMMAS = {
    "zdaž",
    "zdaliž",
    "zdalit",   # Stanza mislemmatizuje "Zdaliž" ako perfektívne sloveso
    "není",
    "liž",
}

QUESTIONING_EPISTEMIC_LEMMAS = {
    "vědět",
    "snad",
    "pochybovat",
}

QUESTIONING_CHALLENGE_LEMMAS = {
    "myslet",
    "říci",
    "soudit",
    "odpovědět",
    "povědět",
}

PERSUADING_CONNECTOR_LEMMAS = {
    "neboť",
    "proto",
    "tedy",
    "poněvadž",
    "jelikož",
    "nebo",
    "protož",
    "zajisté",
    # English (ewt)
    "for", "therefore", "thus", "hence", "because", "since", "so",
    "wherefore", "accordingly", "consequently",
}

PERSUADING_QUESTION_LEMMAS = {
    "což",
    "zdali",
    "kterak",
    "obstát",
    "moci",
}

PERSUADING_APPEAL_LEMMAS = {
    "vidět",
    "pohledět",
    "pohlédit",      # lemmatizér z "pohleďte" → pohlédit
    "pamatovat",
    "uvážit",
    "slyšet",
    "znát",
}

PERSUADING_CONTRAST_LEMMAS = {
    "ale",
    "však",
    "nýbrž",
    "naopak",
}

PERSUADING_ANALOGY_LEMMAS = {
    # "jakož" vynechané — v biblickej češtine je to citačná formula ("jakož psáno jest"),
    # nie analógia; pokrytá SCRIPTURE_CITATION_LEMMAS
    "jako",
    "podle",
}

DECLARING_IDENTITY_LEMMAS = {
    "já",
    "ten",
    "který",
    "toto",
}

DECLARING_UNIVERSAL_LEMMAS = {
    "všichni",
    "všechen",   # lemmatizér z "všichni" → všechen
    "každý",
    "nikdo",
    "vždy",
    "nikdy",
}

DECLARING_PROCLAMATION_LEMMAS = {
    "věru",
    "zajisté",
    "vpravdě",
    "amen",
    "pravit",
}

DECLARING_COPULAR_LEMMAS = {
    "být",
    "znamenat",
    "nazývat",
}

DECLARING_ABSTRACT_LEMMAS = {
    "světlo",
    "pravda",
    "láska",
    "život",
    "cesta",
    "slovo",
    # English (ewt)
    "light", "truth", "love", "life", "way", "word", "spirit", "soul",
    "wisdom", "power", "mystery", "symbol", "key", "arcanum", "secret",
}

JUSTIFYING_CAUSAL_LEMMAS = {
    "neboť",
    "proto",
    "poněvadž",
    "jelikož",
    "nebo",
    "protože",
    "protož",
}

JUSTIFYING_EXPLANATORY_LEMMAS = {
    "totiž",
    "důvod",
    "příčina",
    "za",
}

JUSTIFYING_RETROSPECTIVE_LEMMAS = {
    "stát",
    "učinit",
    "být",
    "říci",
}

JUSTIFYING_THEOLOGICAL_LEMMAS = {
    "vůle",
    "líbit",
    "ustanovit",
    "naplnit",
    "písmo",
}

JUSTIFYING_PASSIVE_LEMMAS = {
    "říci",
    "psát",
    "psaný",     # ADJ passive participle — lemmatizér z "psáno/psána" → psaný
    "napsaný",   # prefix variant
    "ustanovit",
    "zjevit",
    "zjevený",   # ADJ passive participle variant
}

PROMISING_EXPLICIT_LEMMAS = {
    "dát",
    "zaslíbit",
    "slíbit",
    "učinit",
    # English (ewt)
    "receive", "obtain", "attain", "find", "grant", "give", "bestow",
    "gain", "inherit", "possess",
}

PROMISING_CONTRACT_LEMMAS = {
    "smlouva",
    "úmluva",
    "zaslíbení",
    "přísaha",
    "příslib",
    "zavázat",
}

PROMISING_POSITIVE_OUTCOME_LEMMAS = {
    "požehnat",
    "požehnaný",     # ADJ passive participle — lemmatizér vracia z "požehnáni/požehnaný"
    "zachovat",
    "obdržet",
    "zdědit",
    "vejít",
}

PROMISING_OATH_LEMMAS = {
    "přísahat",
    "amen",
    "živý",
}

AUTHORITY_EXPLICIT_LEMMAS = {
    "říci",
    "pravit",
    "přikázat",
    "ustanovit",
    "zjevit",
}

AUTHORITY_DIVINE_LEMMAS = {
    "hospodin",
    "hospodinův",  # posesívne ADJ — "přikázání Hospodinova" → hospodinův
    "bůh",
    "boží",        # posesívne ADJ — "přikázání Boží / Duch Boží" → boží
    "pán",
    "duch",
    "kristus",
    "ježíš",
    # English (ewt)
    "god", "lord", "divine", "spirit", "christ", "jesus", "holy",
    "eternal", "infinite", "supreme", "absolute", "sacred",
}

AUTHORITY_FIRST_PERSON_LEMMAS = {
    "já",
}

AUTHORITY_PROPHETIC_LEMMAS = {
    "prorok",
    "pomazaný",
    "poslaný",
    "slovo",
    "duch",
}

AUTHORITY_APOSTOLIC_LEMMAS = {
    "apoštol",
    "pavel",
    "petr",
    "jakub",
    "jan",
}

SCRIPTURE_CITATION_LEMMAS = {
    "jakož",
    "jakž",
    "napsat",
    "psát",
    "psaný",
    "napsaný",
    "stát",
    # English (ewt)
    "write", "written", "say", "according", "tradition", "ancient",
    "master", "teach", "scripture", "text", "book",
}

SCRIPTURE_FULFILLMENT_LEMMAS = {
    "naplnit",
    "naplňovat",
    "skrze",
    "prorok",
}

SCRIPTURE_REFERENCE_LEMMAS = {
    "zákon",
    "prorok",
    "žalm",
    "kniha",
    "písmo",
    "list",
}

SCRIPTURE_FORMULA_LEMMAS = {
    "pravit",
    "díti",
    "hospodin",
    "slovo",
    "svatý",
}

SCRIPTURE_TYPOLOGY_LEMMAS = {
    "jako",
    "mojžíš",
    "jonáš",
    # "vzor" odstránené — NOT FOUND v celej BKR; BKR používa příklad
    "příklad",   # Stanza: příkladu/příkladem → příklad, potvrdené v DB ✓
    # "dnů" nahradené — Stanza: dnů/dní/dne → den (potvrdené 3× v dep CSV)
    "den",
}

TRADITION_PRECEDENT_LEMMAS = {
    "pradávno",
    "počátek",
    "věk",
    "jakož",
    "být",
    "činit",
}

TRADITION_ANCESTORS_LEMMAS = {
    "otec",
    "předek",
    "praotec",
    "abraham",
    "izák",
    "jakub",
    "mojžíš",
}

TRADITION_COVENANT_LEMMAS = {
    "smlouva",
    "zaslíbení",
    "úmluva",
    "učinit",
}

TRADITION_RITUAL_LEMMAS = {
    "zvyk",
    "ustanovení",
    "každoročně",
    "vždy",
    "pokolení",
}

TRADITION_CONTINUITY_LEMMAS = {
    "víra",
    "tradice",
    "podání",
    "zachovávat",
    "držet",
    "plnit",
}

THREAT_CONDITION_LEMMAS = {
    "jestliže",
    "pakliže",
    # DEAD: Stanza lemmatizuje na být (AUX), nikdy nebudeš/nebudete (viď komentár pri WARNING_CONDITION_LEMMAS)
    # "nebudeš",
    # "nebudete",
    "kdož",
    "kdo",
    "nepřijmout",
    "neposlechnut",
    "li",   # kondicionálna enklitika — "nebudeš-li" → "li" (Stanza tokenizuje zvlášť)
}

THREAT_OUTCOME_LEMMAS = {
    "odsoudit",
    "odsouzený",   # ADJ pasívne particípium — "budeš odsouzen" → odsouzený
    "potrestat",
    "zahynout",
    "zahynét",     # Stanza lemma od "zahynete/zahyneš" — kontextový variant
    "padnout",
    "vyťat",       # "bude vyťat" — pasívne particípium, metafora rozsudku
    "neprojít",
    "neujít",
    "zůstat",
}

THREAT_URGENCY_LEMMAS = {
    "již",
    "brzy",
    "přicházet",
    "sekera",    # Stanza: sekeru/sekery → sekera (potvrdené v dep CSV ✓)
    "kořen",
    "přiložit",
}

THREAT_EXEMPLAR_LEMMAS = {
    "jako",
    "oni",
    "tak",
    "padnout",
    "stát",
}

THREAT_DIVINE_WRATH_LEMMAS = {
    "hněv",
    "boží",
    "zůstávat",
    "nepominout",
    "neujít",
}

REWARD_DIRECT_LEMMAS = {
    "dostat",
    "obdržet",
    "přijmout",
    "dát",
    "nalézt",
    "naleznout",  # Stanza lemma od "naleznete" — alternativní infinitiv k "nalézt"
}

REWARD_BEATITUDE_LEMMAS = {
    "blahoslavený",
    "blahoslavení",
}

REWARD_CONDITION_LEMMAS = {
    "budete",
    "jestliže",
    "kdo",
    "kdož",
    "hledat",
    "vytrvat",
}

REWARD_ESCHATOLOGICAL_LEMMAS = {
    "věčný",
    "království",
    "nebeský",
    "ráj",
    "sláva",
    "věnec",
    "spasit",
    "spasení",       # NOUN variant — "obdržet spasení / přijmout spasení"
    "milosrdenství", # "Blahoslavení milosrdní, neboť oni milosrdenství dojdou"
}

REWARD_RECIPROCAL_LEMMAS = {
    "hledat",
    "nalézat",
    "naleznout",  # Stanza lemma od "naleznete" — záloha za "nalézat"
    "prosit",
    "tloucí",
    "tlucit",     # Stanza lemma od "tlucte" (imper. pl.) — skutočný tvar
    "otevřít",
    "otevřený",   # ADJ pasívne particípium — "bude vám otevřeno" → otevřený
}

CONTRAST_CONNECTOR_LEMMAS = {
    "ale",
    "však",
    "nýbrž",
    "naopak",
    "oproti",
    "zatímco",
    "kdežto",
    # English (ewt)
    "but", "yet", "however", "whereas", "although", "though",
    "nevertheless", "while", "rather", "instead",
}

CONTRAST_LIGHT_DARK_LEMMAS = {
    "světlo",
    "tma",
    "temnota",
    "den",
    "noc",
}

CONTRAST_LIFE_DEATH_LEMMAS = {
    "život",
    "smrt",
    "zahynout",
    "žít",
    "věčný",
}

CONTRAST_GOOD_EVIL_LEMMAS = {
    "dobrý",
    "zlý",
    "spravedlivý",
    "bezbožný",
    "pravda",
    "lež",
    "láska",
    "nenávist",
}

CONTRAST_OLD_NEW_LEMMAS = {
    "starý",
    "nový",
    "dříve",
    "nyní",
    "slyšet",
    "pravit",
}

REPETITION_FORMULA_LEMMAS = {
    "amen",      # "Amen, amen pravím vám" — formulaické zdvojenie, liturgický marker
    "haleluja",  # chvalozpěvná formula
    "hosanna",   # liturgická aklamácia
    "věk",       # "na věky věků" — temporální amplifikátor v liturgických formulách
}

REPETITION_EMPHATIC_LEMMAS = {
    "věru",     # "věru, věru pravím" — Johannine emfatická formula
    "zajisté",  # emfatický zdůrazňovač v proklamačnom kontexte
}

REPETITION_ANAPHORIC_LEMMAS = {
    "blahoslavený",  # anafora beatitúd — "Blahoslavení... blahoslavení..."
    "blahoslavení",
    "běda",          # prorocká anafora — "Běda vám! Běda vám!"
}

REPETITION_PARALLELISM_LEMMAS = {
    "hledat",  # trojčlenný paralelizmus: "Proste... Hledejte... Tlucte..."
    "prosit",
    "tloucí",
    "tlucit",
    "jako",    # komparatívny paralelizmus "jako... tak..."
    "tak",
}

REPETITION_REFRAIN_LEMMAS = {
    "milosrdenství",  # žalmový refrén: "neboť jeho milosrdenství trvá na věky"
    "trvat",
    "chválit",
    "zpívat",
    "oslavovat",
}

NARRATIVE_EXAMPLE_COMPARATIVE_LEMMAS = {
    "jako",
    "tak",
    "podobně",
    "přirovnat",
}

NARRATIVE_EXAMPLE_PARABLE_LEMMAS = {
    "podobný",
    "království",    # "Království nebeské je podobné..." — parabolická formula
    "podobenství",
    "přirovnat",
}

NARRATIVE_EXAMPLE_HISTORICAL_LEMMAS = {
    "den",
    "doba",
    "když",
    "stát",
    "být",
    "noé",           # "jako za dnů Noé" — typologická historická alúzia
    "lot",
}

NARRATIVE_EXAMPLE_FIGURE_LEMMAS = {
    "abraham",
    "mojžíš",
    "david",
    "jonáš",
    "lot",
    "šalamoun",
}

NARRATIVE_EXAMPLE_MORAL_LEMMAS = {
    "tak",
    "také",
    "podobně",
    "činit",
    "jít",
}

DIRECT_ADDRESS_PRONOUN_LEMMAS = {
    "vy",
    "ty",
    "vám",
    "tebe",
    "tobě",
}

DIRECT_ADDRESS_VOCATIVE_LEMMAS = {
    # "hospodin" a "pán" vynechané — ich lemma sa zhoduje s nominatívom
    # (podmetové vety) aj datívom ("Zpívejte Hospodinu") → príliš veľa FP
    "lid",
    "izrael",
    "jeruzalém",
    "bratr",      # lemma od "bratři" (vokativ pl.) → Stanza: bratr
    # "syn" vynechané — "Syna" (gen.) → "syn" — FP v "ve jménu ... Syna"
}

DIRECT_ADDRESS_INCLUSIVE_LEMMAS = {
    "my",
    "nás",
    "náš",
}

DIRECT_ADDRESS_IMPERATIVE_LEMMAS = {
    "slyšet",
    "slyšt",    # skutočná Stanza lemma od "slyšte" (imperativ pl.) — nie "slyšet"
    "vědět",
    "vězte",    # imperativ pl. od vědět — záloha ak lemmatizér nevráti "vědět"
    "oznámit",
}

DIRECT_ADDRESS_EPISTOLAR_LEMMAS = {
    "psát",
    "oznamovat",
    "prosit",
    "vězte",
}

RHETORICAL_NEGATIVE_LEMMAS = {
    "což",
    "zdali",
    "není",
    "liž",
    "vědět",
    "znát",
}

RHETORICAL_CONSEQUENCE_LEMMAS = {
    "uniknout",
    "obstát",
    "prospět",
    "nač",
}

RHETORICAL_ARGUMENTATIVE_LEMMAS = {
    "myslet",
    "myslit",   # alternatívna Stanza lemma od "myslíte" — variant "myslit"
    "říci",
    "který",
    "přikázání",
}

RHETORICAL_IRONIC_LEMMAS = {
    "zdaž",
    "zdali",
    "což",
    "sbírat",
    "trní",
}

RHETORICAL_CHALLENGE_LEMMAS = {
    "ucho",
    "oko",
    "pochopit",
    "porozumět",
    "slyšet",
}

# ==========================================================
# LEGITIMATION LEXIKÓNY
# ==========================================================

LEGITIMATION_DIVINE_MANDATE_LEMMAS = {
    "vůle",
    "ustanovit",
    "pomazat",
    "poslat",
    "bůh",
    "hospodin",
    # English (ewt)
    "will", "ordain", "appoint", "send", "god", "lord", "command",
    "authority", "power", "decree", "divine",
}

LEGITIMATION_ROYAL_LEMMAS = {
    "král",
    "trůn",
    "království",
    "vláda",
    "pomazaný",
    "vyvolený",
    "ustanovený",
}

LEGITIMATION_PRIESTLY_LEMMAS = {
    "kněz",
    "prorok",
    "starší",
    "velekněz",
    "úřad",
    "služba",
    "povolání",
    "povolat",
}

LEGITIMATION_COVENANT_LEMMAS = {
    "smlouva",
    "zaslíbení",
    "dědictví",
    "národ",
    "lid",
}

LEGITIMATION_DIVINE_VOICE_LEMMAS = {
    "já",
    "hospodin",
    "král",
    "sláva",
    "mocný",
}

# ==========================================================
# IDEOLOGICAL CONTESTATION LEXIKÓNY
# ==========================================================

IDEOLOGICAL_CONTESTATION_REDEF_LEMMAS = {
    "znamenat",
    "rozumět",
    "pravit",
    "říci",
}

IDEOLOGICAL_CONTESTATION_POLEMIC_LEMMAS = {
    "naopak",
    "nýbrž",
    "ale",
    "však",
}

IDEOLOGICAL_CONTESTATION_CONCEPT_LEMMAS = {
    "spravedlnost",
    "pravda",
    "zákon",
    "svoboda",
    "pravý",
    "skutečný",
    "opravdový",
}

IDEOLOGICAL_CONTESTATION_CRITIQUE_LEMMAS = {
    "mýlit",
    "nerozumět",
    "nepochopit",
    "znát",
    "písmo",
}

IDEOLOGICAL_CONTESTATION_NEW_AUTH_LEMMAS = {
    "říci",
    "pravit",
    "předek",
    "slyšet",
    "duch",
}

# ==========================================================
# INTERVENTION LEXIKÓNY
# ==========================================================

INTERVENTION_RESPONSE_LEMMAS = {
    "odpovědět",
    "říci",
    "pravit",
}

INTERVENTION_POLEMIC_LEMMAS = {
    "vy",
    "váš",
    "říkat",
    "tvrdit",
    "myslet",
}

INTERVENTION_DISPUTE_LEMMAS = {
    "otázat",
    "pokoušet",
    "přijít",
    "farizeus",
    "zákoník",
    "velekněz",
    "saduceus",
    "saducejský",   # Stanza ADJ forma: saducejského/saducejské → saducejský ✓
    "písař",        # BKR substitút za zákoník: písaři/písařů → písař ✓
}

INTERVENTION_CORRECTIVE_LEMMAS = {
    "nikoliv",
    "nikoli",
    "ne",
    "nýbrž",
}

INTERVENTION_META_LEMMAS = {
    "otázka",
    "spor",
    "věc",
    "záležitost",
}

POLITICAL_VOCABULARY_LEMMAS: frozenset = frozenset({
    "král", "království", "vláda", "trůn", "lid", "národ",
    "kněz", "velekněz", "smlouva", "zákon", "přikázání",
    "spravedlnost", "soud", "spása", "vyvolený", "pomazaný",
    "dědic", "nepřítel", "satan", "farizeus", "zákoník",
})


# ==========================================================
# MULTILANG LEXICON ACCESS  (absorbed from t_lexicons_multilang)
# ==========================================================

import json as _json
from pathlib import Path as _Path

# Adresárová štruktúra lexikónov
_LEXICONS_DIR  = _Path(__file__).parent / "lexicons"
_EN_AUTO_FILE  = _LEXICONS_DIR / "en" / "lexicons_en_auto.json"    # generované prekladom
_EN_MANUAL_FILE = _LEXICONS_DIR / "en" / "lexicons_en_manual.json" # ručne kurátorované
# Legacy fallback — output/lexicons_en.json (staré umiestnenie)
_EN_LEGACY_FILE = _Path(__file__).parent / "output" / "lexicons_en.json"

_cs_cache: dict | None = None
_en_cache: dict | None = None


def _load_cs() -> dict:
    global _cs_cache
    if _cs_cache is None:
        _cs_cache = {
            name: val
            for name, val in globals().items()
            if name.endswith("_LEMMAS")
            and isinstance(val, (set, frozenset))
        }
    return _cs_cache


def _load_en() -> dict:
    """
    Dvojvrstvové načítanie anglických lexikónov:
      1. Základ:  lexicons_en_auto.json  (generovaný Claude API prekladom z CS)
      2. Override: lexicons_en_manual.json (ručne kurátorované — archaická angličtina,
                   KJV formy, ezoterika; manual vždy prepisuje auto pre daný lexikón)
      3. Fallback: output/lexicons_en.json (legacy)

    Pre každý kľúč sa EN výsledok = auto[kľúč] ∪ manual[kľúč],
    pričom manual má prednosť (union je bezpečný — lemmy sú additivne).
    """
    global _en_cache
    if _en_cache is not None:
        return _en_cache

    merged: dict[str, set] = {}

    # Vrstva 1: auto-preložený súbor (nemusí existovať)
    for candidate in (_EN_AUTO_FILE, _EN_LEGACY_FILE):
        if candidate.exists():
            raw = _json.loads(candidate.read_text(encoding="utf-8"))
            for name, lemmas in raw.items():
                if name.startswith("_"):   # preskoč _meta a iné meta-kľúče
                    continue
                merged.setdefault(name, set()).update(lemmas)
            break  # použij prvý nájdený

    # Vrstva 2: manuálny súbor (vždy sa aplikuje ak existuje)
    if _EN_MANUAL_FILE.exists():
        raw_manual = _json.loads(_EN_MANUAL_FILE.read_text(encoding="utf-8"))
        for name, lemmas in raw_manual.items():
            if name.startswith("_"):
                continue
            merged.setdefault(name, set()).update(lemmas)

    if not merged:
        raise FileNotFoundError(
            f"Žiadny anglický lexikón nenájdený.\n"
            f"  auto:   {_EN_AUTO_FILE}\n"
            f"  manual: {_EN_MANUAL_FILE}\n"
            "Spusti: python scripts/translate_lexicons_to_en.py"
        )

    _en_cache = {name: frozenset(lemmas) for name, lemmas in merged.items()}
    return _en_cache


def get_lexicons(lang: str) -> dict:
    if lang == "cs":
        return _load_cs()
    if lang == "en":
        return _load_en()
    raise ValueError(f"Unsupported lang: {lang!r}. Use 'cs' or 'en'.")


def lexicon_coverage_report(lang: str = "cs") -> list[dict]:
    """
    For each lexicon, compute what fraction of its lemmas appear
    in the refined_descriptions DB (lemmas column).

    Returns a list of dicts sorted by coverage descending:
        lexicon_name, lexicon_size, db_hits, coverage_pct

    Prints a summary table to stdout.
    """
    from n_db import load_rows as _load_db, TABLE_REFINED

    db_rows = _load_db(TABLE_REFINED)
    if not db_rows:
        print("lexicon_coverage_report: refined_descriptions table is empty.")
        return []

    # Collect all unique lemmas seen in the DB
    db_lemmas: set = set()
    for row in db_rows:
        db_lemmas.update(row.get("lemmas", "").split())

    lexicons = get_lexicons(lang)
    results  = []

    for name, lemma_set in sorted(lexicons.items()):
        size = len(lemma_set)
        hits = len(lemma_set & db_lemmas)
        pct  = round(100 * hits / size, 1) if size else 0.0
        results.append({
            "lexicon_name":  name,
            "lexicon_size":  size,
            "db_hits":       hits,
            "coverage_pct":  pct,
        })

    results.sort(key=lambda r: r["coverage_pct"], reverse=True)

    # Print summary table
    W = 48
    print(f"\n{'LEXICON COVERAGE REPORT':─<{W}}")
    print(f"  DB unique lemmas : {len(db_lemmas)}")
    print(f"  Lang             : {lang}")
    print(f"  {'Lexicon':<42} {'size':>5}  {'hits':>5}  {'cov%':>6}")
    print(f"  {'-'*42} {'-----':>5}  {'-----':>5}  {'------':>6}")
    for r in results:
        bar = "█" * int(r["coverage_pct"] // 10)
        print(
            f"  {r['lexicon_name']:<42} {r['lexicon_size']:>5}"
            f"  {r['db_hits']:>5}  {r['coverage_pct']:>5.1f}%  {bar}"
        )
    print("─" * W)

    return results


# ==========================================================
# IQ3f. PERLOKATÍVNY EFEKT — emotívny slovník a adresácia čitateľa
# ==========================================================

# Evokácia strachu, báze, naliehavosti  [CS only — EN: lexicons/en/lexicons_en_manual.json]
EMOTIVE_FEAR_LEMMAS: frozenset = frozenset({
    "strach", "bázeň", "hrůza", "třást", "třes",
    "děsit", "děs", "bát", "bojácný", "zachvět",
    "zhrozit", "zastrašit", "chvět",
})

# Evokácia nádeje, útechy, uistenia  [CS only — EN: lexicons/en/lexicons_en_manual.json]
EMOTIVE_HOPE_LEMMAS: frozenset = frozenset({
    "naděje", "útěcha", "doufat", "potěšit", "utěšit",
    "upokojiť", "uklidnit", "posilnit", "povzbudit",
    "ujistit", "ujištění", "čekat", "očekávat",
})

# Evokácia úžasu, obdivu, posvätnej hrôzy  [CS only — EN: lexicons/en/lexicons_en_manual.json]
EMOTIVE_WONDER_LEMMAS: frozenset = frozenset({
    "úžas", "obdiv", "div", "zázrak", "obdivovat",
    "žasnout", "užasnout", "podivný", "podivuhodný",
    "slavný", "vznešený", "nevýslovný", "nepochopitelný",
})

# Evokácia viny, hanby, ľútosti, pokánia  [CS only — EN: lexicons/en/lexicons_en_manual.json]
EMOTIVE_GUILT_LEMMAS: frozenset = frozenset({
    "stud", "vina", "pokání", "hřích", "provinění",
    "kajícnost", "litovat", "obrátit", "kajícný",
    "pokořit", "ponížit", "zpytovat",
})

# Priame oslovenie čitateľa ako čitateľa / žiaka / hľadajúceho
# CS základ; EN rozšírenie (Waite-štýl) → lexicons/en/lexicons_en_manual.json
READER_ADDRESS_LEMMAS: frozenset = frozenset({
    "čtenář", "žák", "učedník", "hledající", "zasvěcenec", "čitatel",
})


# ==========================================================
# IQ4. FREKVENČNÁ VÁHA LEMIEM  (lemma IDF)
# ==========================================================
#
# Motivácia:
#   Aktuálna klasifikácia vychádza z binárnej prítomnosti lemmy v lexikóne.
#   "blahoslavený" (unikátne pre 2–3 lexikóny) a "být" (vo všetkých) majú
#   rovnakú váhu 1.  Frekvenčná váha znižuje váhu generických lemiem a
#   zosilňuje váhu špecifických — presne ako TF-IDF v IR.
#
# Dva zdroje váh:
#   LEMMA_IDF_CROSS — cross-lexikón IDF, vypočítané pri importe z lexikónov
#                     samotných (bez DB).  Vždy dostupné.
#   compute_corpus_idf(rows) — korpusový IDF z DB riadkov.  Presnejší, ale
#                              vyžaduje načítanú DB.

import math as _math


def _collect_lexicon_df() -> dict[str, int]:
    """Return {lemma: count_of_distinct_lexicons_containing_it}."""
    df: dict[str, int] = {}
    for name, val in globals().items():
        if name.endswith("_LEMMAS") and isinstance(val, (set, frozenset)):
            for lemma in val:
                df[lemma] = df.get(lemma, 0) + 1
    return df


def _build_cross_lexicon_idf(df: dict[str, int], n_lexicons: int) -> dict[str, float]:
    """
    IDF = log(N / df)  where N = total number of *_LEMMAS sets.

    Lemma in 1 lexicon  → log(N/1) ≈ high weight (specific signal)
    Lemma in N lexicons → log(N/N) = 0        (ubiquitous, uninformative)
    """
    return {lemma: _math.log(n_lexicons / count) for lemma, count in df.items()}


def _init_cross_lexicon_idf() -> dict[str, float]:
    df         = _collect_lexicon_df()
    n_lexicons = sum(
        1 for name, val in globals().items()
        if name.endswith("_LEMMAS") and isinstance(val, (set, frozenset))
    )
    return _build_cross_lexicon_idf(df, n_lexicons)


# Precomputed at import time — no DB required.
LEMMA_IDF_CROSS: dict[str, float] = _init_cross_lexicon_idf()

# Maximum possible IDF = log(N / 1) = log(N), for lemmas unique to 1 lexicon.
# Used to normalise the boost curve so the rarest lemma always reaches 1.0.
_LEMMA_IDF_MAX: float = max(LEMMA_IDF_CROSS.values()) if LEMMA_IDF_CROSS else 1.0


def compute_corpus_idf(rows: list[dict]) -> dict[str, float]:
    """
    Compute lemma IDF from a list of DB rows (each row must have "lemmas" key,
    a space-separated string of lemmatised tokens).

    IDF = log((N_sentences + 1) / (df_sentences + 1))   [Laplace smoothing]

    Higher IDF → lemma is rare → stronger discriminative signal.
    Returns a dict usable directly in weighted_lemma_score().
    """
    n = len(rows)
    if n == 0:
        return {}
    df: dict[str, int] = {}
    for row in rows:
        seen = set(row.get("lemmas", "").split())
        for lemma in seen:
            df[lemma] = df.get(lemma, 0) + 1
    return {
        lemma: _math.log((n + 1) / (count + 1))
        for lemma, count in df.items()
    }


def weighted_lemma_score(
    sentence_lemmas: set,
    lexicon: set,
    idf: dict[str, float],
    default_weight: float = 1.0,
) -> float:
    """
    Return the sum of IDF weights for sentence lemmas that are in *lexicon*.

    Parameters
    ----------
    sentence_lemmas : set of lemmas present in the sentence
    lexicon         : one of the *_LEMMAS sets from this module
    idf             : {lemma: weight} — use LEMMA_IDF_CROSS or compute_corpus_idf()
    default_weight  : weight assigned to a lemma not in *idf*
                      (default 1.0 — neutral, equivalent to binary presence)

    Returns 0.0 if no lexicon lemma is present in the sentence.
    """
    return sum(
        idf.get(lemma, default_weight)
        for lemma in sentence_lemmas & lexicon
    )


def confidence_boost(
    base_conf: float,
    sentence_lemmas: set,
    lexicons: list[set],
    idf: dict[str, float],
    max_boost: float = 0.12,
) -> float:
    """
    Adjust *base_conf* upward when high-IDF (rare, specific) lexicon lemmas
    match, and leave it unchanged when only low-IDF (generic) lemmas match.

    The boost is proportional to the mean IDF of all matched lemmas across
    all *lexicons*, normalised to [0, max_boost].

    Parameters
    ----------
    base_conf       : starting confidence value (e.g. 0.65)
    sentence_lemmas : set of sentence lemmas
    lexicons        : list of *_LEMMAS sets involved in the firing pattern
    idf             : {lemma: weight} — typically LEMMA_IDF_CROSS
    max_boost       : maximum additive boost (default 0.12, i.e. up to 77 % → 89 %)

    Returns the adjusted confidence, clamped to [base_conf, 0.95].

    Example
    -------
    # "blahoslavený" is specific (high IDF) → confidence 0.70 → ~0.79
    # "být" is generic (IDF ≈ 0) → confidence 0.70 stays at 0.70
    base = 0.70
    c = confidence_boost(base, {"blahoslavený"}, [PRAISING_DIRECT_LEMMAS], LEMMA_IDF_CROSS)
    """
    if not idf:
        return base_conf

    # Collect IDF scores for all lexicon hits
    hit_weights: list[float] = []
    for lex in lexicons:
        for lemma in sentence_lemmas & lex:
            hit_weights.append(idf.get(lemma, 0.0))

    if not hit_weights:
        return base_conf

    mean_idf   = sum(hit_weights) / len(hit_weights)
    # Normalise by the true maximum IDF (log N, lemma in exactly 1 lexicon) so
    # the rarest lemma maps to 1.0 and the most common lemma maps to a value
    # proportional to its actual cross-lexicon frequency.
    normalised = min(mean_idf / _LEMMA_IDF_MAX, 1.0)
    boost      = normalised * max_boost
    return min(base_conf + boost, 0.95)
