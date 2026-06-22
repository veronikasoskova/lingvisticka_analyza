"""
Skinner Pipeline — Streamlit Interface
Czech biblical text analysis: illocutionary force · intention · rhetorical strategy
"""

import io
import sys
from pathlib import Path

SRC = Path(__file__).parent
sys.path.insert(0, str(SRC))
OUTPUT = SRC / "output"

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ──────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Skinner Pipeline",
    page_icon="📖",
    layout="wide",
)

# ──────────────────────────────────────────────────────────────────────────────
# TRANSLATIONS
# ──────────────────────────────────────────────────────────────────────────────

TRANSLATIONS = {
    "cs": {
        "app_title": "📖 Skinner Pipeline",
        "app_subtitle": "Analýza českého biblického textu — komunikační síla · záměr · rétorická strategie",
        "tab_analyze": "📝 Analyzovat text",
        "tab_bible": "📚 Biblický korpus",
        "export_pdf": "📄  Exportovat report jako PDF",
        "pdf_generating": "Generuje se PDF…",
        "pdf_ready": "Report připraven ke stažení.",
        "pdf_error": "Chyba při generování PDF",
        "pdf_filename": "skinner_report.pdf",
        "lang_label": "Jazyk",
        # Tab 1
        "upload_header": "Nahrajte nebo vložte text",
        "upload_label": "Nahrát .txt nebo .pdf",
        "paste_label": "…nebo vložit text sem",
        "run_button": "▶  Spustit analýzu",
        "reading_file": "Čtení souboru…",
        "running_pipeline": "Probíhá analýza…",
        "no_text_warning": "Nahrajte soubor nebo vložte text.",
        "metric_sentences": "Vět celkem",
        "metric_classified": "Klasifikováno",
        "metric_confidence": "Průměrná jistota",
        "metric_intentions": "Různé záměry",
        "intent_pie_title": "Záměry",
        "intent_pie_desc": "Záměry mluvčího v analyzovaném textu — dominantní záměry ukazují rétoricko-komunikační profil textu.",
        "strategy_bar_title": "Rétorické strategie",
        "strategy_bar_desc": "Nejčastěji použité rétoricke techniky pro prosazování záměrů.",
        "force_pie_title": "Typ řečového aktu",
        "force_pie_desc": "Základní typ řečového aktu: direktivy · asertiva · komisiva · expresiva · deklarativa.",
        "conf_hist_title": "Jistota klasifikace per záměr",
        "conf_hist_desc": "Spolehlivost klasifikace per záměr — nízká jistota signalizuje rétorickou ambivalenci výroku.",
        "conf_table_desc": "Průměrná jistota per záměr.",
        "secondary_intent_title": "Sekundární záměry",
        "secondary_intent_desc": "Věty s dvojitým záměrem — sekundární záměr odhaluje argumentativní podtext.",
        "section_sentence_table": "Výsledky po větách",
        "filter_intention": "Filtrovat záměr",
        "filter_strategy": "Filtrovat strategii",
        "download_csv": "⬇  Stáhnout jako CSV",
        "col_id": "#",
        "col_sentence": "Věta",
        "col_intention": "Záměr",
        "col_2nd_intention": "2. záměr",
        "col_force": "Typ řeč. aktu",
        "col_strategy": "Strategie",
        "col_confidence": "Jistota",
        "col_reason": "Zdůvodnění",
        "col_locution": "Lokuce",
        "col_convention": "Konvence",
        "col_pol_vocab": "Polit. slovník",
        # Tab 2
        "bible_header": "Analýza biblického korpusu",
        "bible_caption": "Předpočítáno z české Bible (Kralická, BKR) — spusťte `k_apply_all_to_bible.py` pro aktualizaci.",
        "metric_total": "Vět celkem",
        "metric_books": "Biblické knihy",
        "metric_coverage": "Klasifikováno",
        "metric_mean_conf": "Průměrná jistota",
        "no_db": "Databáze `output/bible_analysis.db` nenalezena. Nejprve spusťte pipeline.",
        # Section 1
        "sec_intention": "📊 Analýza záměrů",
        "all_intentions_title": "Záměry — všechny knihy",
        "all_intentions_desc": "Distribuce záměrů v celém korpusu — dominantní záměry charakterizují rétoricképole textu.",
        "force_all_title": "Typy řečových aktů",
        "force_all_desc": "Distribuce typů řečových aktů v celém korpusu.",
        "intent_book_heatmap_title": "Záměry podle knih",
        "intent_book_heatmap_desc": "Rétoricképrofily jednotlivých knih — tmavší = záměr dominuje v dané knize.",
        # Section 2
        "sec_strategy": "🎯 Analýza strategií",
        "all_strategies_title": "Rétorické strategie — všechny knihy",
        "all_strategies_desc": "Rétoricketechniky v celém korpusu — srovnání ukazuje argumentativní strategie textu.",
        "pvoc_title": "Nejčastější politická slovní zásoba",
        "pvoc_desc": "Slova spjatá s mocí, autoritou a zákonem — ukazatel politického diskurzu textu.",
        "strat_book_heatmap_title": "Strategie podle knih",
        "strat_book_heatmap_desc": "Rétoricképrofily knih — tmavší = strategie dominuje v dané knize.",
        # Section 3
        "sec_ratios": "⚖️ Klíčové poměry podle knih",
        "directive_assertive_title": "Direktivní vs. asertivní věty",
        "directive_assertive_desc": "Příkazové (červená) vs. výrokové (modrá) věty — klíčový ukazatel autoritativnosti a žánru textu.",
        "legit_ratio_title": "Legitimace · Zpochybnění · Intervence",
        "legit_ratio_desc": "Skinnerovy analytické kategorie mocenského diskurzu: legitimace autority, zpochybnění protivníka, výzva k akci.",
        "no_ratios": "Spusťte `l_taxonomy_analytics.py` pro výpočet poměrů.",
        # Section 4
        "sec_religious": "✝️ Náboženské prvky",
        "element_coverage_title": "Výskyt náboženských prvků",
        "element_coverage_desc": "Počet vět s danými náboženskými prvky — ukazuje tematické zaměření korpusu.",
        "philosophy_title": "Filozofické tradice",
        "philosophy_desc": "Přítomnost filozofických a teologických tradic v textu.",
        "rel_elements": {
            "covenant_law":      "Smlouva a zákon",
            "prophetic_speech":  "Prorocká řeč",
            "divine_hierarchy":  "Božská hierarchie",
            "legal":             "Právní prvky",
            "life_death":        "Život a smrt",
            "wisdom":            "Moudrost",
            "ritual_sacrifice":  "Rituální oběť",
            "moral":             "Morální prvky",
            "war_conflict":      "Válka a konflikt",
            "eschatology":       "Eschatologie",
            "royal_power":       "Královská moc",
            "monotheism":        "Monoteismus",
            "genealogy_lineage": "Genealogie",
            "divine":            "Božské prvky",
            "kinship":           "Příbuzenství",
        },
        "rel_philosophy": {
            "platonic":      "Platonismus",
            "neoplatonic":   "Neoplatonismus",
            "stoic":         "Stoicismus",
            "gnostic":       "Gnóze",
            "aristotelian":  "Aristotelismus",
            "pythagorean":   "Pythagorismus",
            "epicurean":     "Epikureismus",
            "hermetic":      "Hermetismus",
            "sufi":          "Súfismus",
            "kabbalistic":   "Kabala",
            "theosophical":  "Teosofie",
            "jungian":       "Jungianismus",
            "new_age":       "New Age",
            "shamanic":      "Šamanismus",
            "tantric":       "Tantrismus",
        },
        "density_heatmap_title": "Hustota náboženských prvků podle knih",
        "density_heatmap_desc": "Podíl vět s danými náboženskými prvky per kniha (0–1) — tmavší = prvek dominuje v dané knize.",
        # Section 5
        "sec_clusters": "🔗 Konceptové shluky a sémantické opozice",
        "cluster_bubble_title": "Konceptové shluky",
        "cluster_bubble_desc": "Sémantické shluky slov — větší bublina = více propojených dvojic, poloha vpravo = silnější vzájemná přitažlivost slov.",
        "opposition_title": "Nejsilnější sémantické opozice",
        "opposition_desc": "Nejčastěji doložené protikladné páry slov v kontextu ±3 vět.",
        # Section 6
        "sec_centrality": "🌐 Sémantická centralita slov",
        "top_n_slider": "Počet zobrazených slov",
        "centrality_bar_title": "Nejdůležitější slova podle sémantické centrality",
        "centrality_bar_desc": "Sémanticky nejdůležitější slova — centrální uzly sítě významů textu.",
        "no_centrality": "Spusťte `r_word_network.py` a `s_word_relations_analytics.py`.",
        # Section 7
        "sec_style": "✍️ Styl a autorství",
        "style_table_desc": "Stylové shluky biblických knih — knihy v jednom shluku sdílejí podobný slovník a rétorický profil.",
        "cluster_terms_title": "Nejcharakterističtější slova shluku",
        "cluster_terms_desc": "Slova nejcharakterističtější pro daný stylový shluk — odlišují ho od ostatních.",
        "select_cluster": "Shluk",
        "no_style": "Spusťte `x_style_authorship.py`.",
        # Section 8
        "sec_dependency": "🏗️ Syntaktická struktura",
        "dep_bar_title": "Nejčastější syntaktické vztahy",
        "dep_bar_desc": "Typy syntaktických závislostí v korpusu — základ pro analýzu větné složitosti a stylu.",
        "dep_heatmap_title": "Syntaktické vztahy podle knih",
        "dep_heatmap_desc": "Distribuce syntaktických závislostí per kniha — tmavší = vztah dominuje v dané knize.",
        # Section 9
        "sec_verbal": "💬 Slovesné vztahy",
        "verbal_types_title": "Typy slovesných vztahů",
        "verbal_types_desc": "Typy slovesných vztahů — přímá řeč, proroctví, genealogie, modlitba, popis atd.",
        "verbal_conf_title": "Jistota klasifikace slovesných vztahů",
        "verbal_conf_desc": "Spolehlivost klasifikace per typ slovesného vztahu.",
        "verbal_book_heatmap_title": "Slovesné vztahy podle knih",
        "verbal_book_heatmap_desc": "Slovesné vztahy per kniha — tmavší = typ dominuje v dané knize.",
        # Section 10
        "sec_taxonomy": "🏷️ Skinnerova behaviorální taxonomie",
        "tax_class_title": "Skinnerovy funkční třídy",
        "tax_class_desc": "Klasifikace vět podle **Skinnerovy behaviorální taxonomie** jazyka: `tact` = popis/pojmenování světa · `mand` = příkaz nebo žádost · `echoic` = citace nebo opakování · `intraverbal` = odpověď na verbální podnět · `autoclitic` = komentář k vlastní řeči. `none` = věty bez přiřazené třídy.",
        "tax_dialogue_title": "Hustota dialogu podle knih",
        "tax_dialogue_desc": "**Podíl vět, které jsou součástí dialogu** (přímé řeči) v každé biblické knize. Vyšší hodnota = kniha obsahuje více dialogů a přímých promluv.",
        "tax_control_title": "Role kontroly",
        "tax_control_desc": "Klasifikace vět z hlediska **vztahu kontroly** mezi mluvčím a posluchačem: `stimulus` = mluvčí kontroluje posluchače, `response` = mluvčí reaguje na podnět, `record` = neutrální záznam bez jasné kontroly.",
        # Section 11
        "sec_word_rel": "🔤 Sémantické asociace slov",
        "top_pmi_title": "Nejsilnější sémantické asociace",
        "top_pmi_desc": "Dvojice slov s **nejvyšším skóre PMI** (Pointwise Mutual Information) — míra toho, jak silně se dvě slova v textu vzájemně přitahují. Vysoké PMI = tato dvě slova se v textu vyskytují spolu mnohem častěji, než by odpovídalo náhodě.",
        "top_pmi_word1": "Slovo 1",
        "top_pmi_word2": "Slovo 2",
        "top_pmi_count": "Počet výskytů",
        "top_pmi_pmi": "PMI skóre",
        "most_connected_title": "Nejvíce propojená slova",
        "most_connected_desc": "Slova s **nejvyšším počtem sémantických vazeb** — tj. slova, která se v textu silně asociují s největším počtem jiných slov. Jsou to sémantická centra textu.",
        "no_word_rel": "Spusťte `s_word_relations_analytics.py`.",
        # Section 12
        "sec_corpus_density": "📐 Hustota tematických kategorií",
        "corpus_density_title": "Hustota kategorií podle knih (věty)",
        "corpus_density_desc": "Podíl vět v každé knize, které obsahují prvky dané **tematické kategorie** (smlouva/zákon, božskost, eschatologie, genealogie, příbuzenství, morálka, proroctví, rituál a další — celkem 16 kategorií). Hodnota 0,30 znamená, že 30 % vět v dané knize patří do dané kategorie.",
        # Axis / column labels
        "x_intention": "Záměr",
        "x_force": "Typ řeč. aktu",
        "x_strategy": "Strategie",
        "x_count": "Počet",
        "x_score": "Skóre",
        "x_book": "Kniha",
        "x_word": "Slovo",
        "x_confidence": "Jistota",
        "x_avg_pmi": "Průměrné PMI",
        "x_edges": "Vazby",
        "x_ratio": "Podíl",
        "x_element": "Prvek",
        "x_relation": "Typ vztahu",
        "x_class": "Třída",
        "x_density": "Hustota",
        "x_tfidf": "TF-IDF",
        "x_pmi": "PMI",
        "x_connections": "Počet vazeb",
        "x_weighted": "Vážené skóre",
        # Section 13 — Text Patterns
        "sec_patterns": "🔠 Textové vzory",
        "wordcloud_title": "Oblak slov — nejčastější slova v korpusu",
        "wordcloud_desc": "Nejčastější lemmatizovaná slova v celém korpusu — větší = četnější.",
        "bigrams_title": "Nejčastější slovní dvojice",
        "bigrams_desc": "Nejčastější slovní dvojice — ustálené fráze a kolokace textu.",
        "trigrams_title": "Nejčastější slovní trojice",
        "trigrams_desc": "Nejčastější slovní trojice — formulaické výrazy a opakující se struktury.",
        "tfidf_heatmap_title": "Charakteristická slova podle knih",
        "tfidf_heatmap_desc": "Slova typická pro danou knihu a ne pro ostatní — odhaluje specifický slovník každé knihy.",
        "x_frequency": "Četnost",
        "x_ngram": "Slovní spojení",
        # Section 14 — Semantics
        "sec_semantics": "🔬 Sémantická analýza",
        "radar_title": "Sémantické typy vět podle knih",
        "radar_desc": "Paprskový (radar) graf zobrazuje **podíl různých sémantických typů vět** v každé biblické knize. Každá osa odpovídá jednomu sémantickému typu: popis, neutrální výrok, žádost, negace/protiklad. Čím dále od středu, tím vyšší podíl vět tohoto typu.",
        "antithetical_title": "Věty s protikladnou strukturou",
        "antithetical_desc": "Zobrazuje věty, v nichž byl algoritmem detekován **protikladný nebo negační vzorec** — věty, kde je něco odmítáno, negováno nebo kladeno do protikladu. Příklad: 'Nekradni', 'Nezabiješ', 'Nejsem..., ale...'",
        "antithetical_count_title": "Počet protikladných vět podle knih",
        "antithetical_count_desc": "Kolik vět s protikladným vzorcem obsahuje každá biblická kniha.",
        "lexical_reinf_title": "Míra lexikálního opakování podle knih",
        "lexical_reinf_desc": "**Lexikální opakování** měří, jak často se stejná slova opakují uvnitř jedné věty. Vyšší hodnota = věty v dané knize obsahují více opakujících se slov (typické pro poetické nebo rituální texty). Hodnota 0 = každé slovo se ve větě vyskytuje jen jednou.",
        "x_reinforcement": "Míra opakování",
        "filter_book_label": "Filtrovat knihu",
        "filter_group_label": "Skupina knih",
        "group_all": "— Celá Bible",
        "group_pentateuch":     "Pentateuch",
        "group_historical":     "Historické knihy",
        "group_wisdom":         "Knihy moudrosti",
        "group_major_prophets": "Velcí proroci",
        "group_minor_prophets": "Malí proroci",
        "group_gospels_acts":   "Evangelia a Skutky",
        "group_pauline":        "Pavlovy listy",
        "group_general":        "Obecné listy",
        "group_apocalypse":     "Apokalypsa",
        "no_patterns": "Data nejsou k dispozici.",
        "no_group_data": "Pro vybranou skupinu nejsou dostupná data.",
        # Section 15 — Pipeline Quality
        "sec_quality": "✅ Kvalita pipeline",
        "quality_overall_desc": "Přehled **kvality automatické klasifikace** celého korpusu: kolik vět bylo klasifikováno, jak jistý byl algoritmus a které knihy nebo třídy se klasifikovaly méně spolehlivě.",
        "coverage_book_title": "Pokrytí klasifikací podle knih",
        "coverage_book_desc": "Procentuální podíl **správně klasifikovaných vět** v každé biblické knize. Hodnoty pod 95 % signalizují, že algoritmus měl s danou knihou více potíží.",
        "conf_bins_title": "Rozložení jistoty klasifikace",
        "conf_bins_desc": "Věty rozdělené do tří pásem jistoty: **0–30 %** = nebylo možné klasifikovat, **30–60 %** = nízká jistota, **60–100 %** = spolehlivá klasifikace. Ideálně by pásmo 60–100 % mělo zahrnovat co nejvíce vět.",
        "consistency_title": "Konzistence klasifikace lemmat",
        "consistency_desc": "Každé lemma (základní tvar slova) by mělo být konzistentně klasifikováno do stejné třídy záměru. Graf zobrazuje **lemmata klasifikovaná do více různých tříd** — tato lemmata jsou pro algoritmus nejednoznačná.",
        "outliers_title": "Knihy s neobvyklým poměrem tříd",
        "outliers_desc": "Knihy, kde je podíl určité třídy záměru **výrazně vyšší nebo nižší** oproti průměru celého korpusu (statistická odchylka |z| > 2). Označuje knihy s neobvyklou rétorickotextovou strukturou.",
        "sample_title": "Vzorové věty — manuální kontrola",
        "sample_desc": "Náhodný výběr 20 klasifikovaných vět pro **manuální ověření správnosti** klasifikace. Doporučujeme zkontrolovat zejména věty s nižší jistotou.",
        "x_coverage": "Pokrytí (%)",
        "no_eval": "Spusťte `v_eval_pipeline.py` pro výpočet metrik kvality.",
        "col_total": "Celkem",
        "col_classified_q": "Klasif.",
        "col_coverage_q": "Pokrytí (%)",
        "col_z_score": "Z-skóre",
        "col_label_q": "Třída",
        "conf_band_low": "Nízká (0–30 %)",
        "conf_band_mid": "Střední (30–60 %)",
        "conf_band_high": "Vysoká (60–100 %)",
        "x_sentences": "Počet vět",
        "ambiguous_lemma_title": "Nejednoznačná lemmata",
        "col_lemma": "Lemma",
        "col_classes": "Třídy",
        "col_n_classes": "Počet tříd",
        "lbl_directive": "Direktiva",
        "lbl_assertive": "Asertiv",
        "lbl_legitimation": "Legitimace",
        "lbl_contestation": "Zpochybnění",
        "lbl_intervention": "Intervence",
        "col_style_cluster": "Stylový shluk",
        "col_silhouette": "Silhouette",
        # Section 16 — Linguistic features
        "sec_ling_features": "🔡 Lingvistické příznaky",
        "ling_ttr_desc": "**Lexikální diverzita** (type-token ratio) — poměr jedinečných lemmat k celkovému počtu. Nižší hodnota = formulaičtější, rituálnější text.",
        "ling_ttr_title": "Průměrná lexikální diverzita (TTR) podle knih",
        "ling_bool_desc": "Procentuální podíl vět s koordinací, dativem a nepřímým objektem. Signalizuje syntaktickou komplexitu a argumentační strukturu.",
        "ling_bool_title": "Syntaktické příznaky (% vět) podle knih",
        "ling_pos_desc": "Průměrný počet přídavných jmen, příslovcí a zájmen na větu. Signalizuje deskriptivní bohatost a přímé oslovení.",
        "ling_pos_title": "Morfologické příznaky (průměr na větu) podle knih",
        "ling_formulaic_desc": "Top 15 vět s nejnižší lexikální diverzitou (min. 5 slov) — pravděpodobně formulaické nebo rituální výroky.",
        "ling_formulaic_title": "Nejformulaičtější věty (nejnižší TTR)",
        "col_ttr": "TTR",
        "lbl_coordination": "Koordinace",
        "lbl_dative": "Dativ",
        "lbl_iobj": "Nepřímý objekt",
        "lbl_adj": "Přídavná jména",
        "lbl_adv": "Příslovce",
        "lbl_pron": "Zájmena",
        # Save to DB
        "save_button": "💾  Uložit do databáze",
        "save_caption": "Uloží výsledky analýzy do `bible_analysis.db` jako samostatný běh — oddělený od biblického korpusu.",
        "save_success": "Uloženo",
        "save_run_id_label": "run_id",
        "save_rows_label": "vět uloženo",
        "save_already": "Již uloženo",
        "save_error": "Chyba při ukládání",
        # Tab 3 + checkboxes
        "tab_results": "📋 Výsledky",
        "about_title": "ℹ️ O analýzách",
        "about_text": (
            "Přehled 10 analytických okruhů:\n\n"
            "1. **B.F. Skinner** — Klasifikuje věty podle behaviorální taxonomie jazyka: "
            "mand (příkaz), tact (popis světa), echoic (citace), intraverbální (reakce na řeč), "
            "autoklit (komentář k vlastní řeči). Vychází z Verbal Behavior (Skinner, 1957).\n\n"
            "2. **Q. Skinner** — Identifikuje ilokuční záměr každé věty (co chce mluvčí vykonat) "
            "a rétorickou strategii (jak záměru dosahuje). Vychází z teorie řečových aktů Austina "
            "a Quintina Skinnera (1969–2002).\n\n"
            "3. **Verbální vztahy** — Klasifikuje žánr verbální interakce: přímá řeč, genealogie, "
            "lyrika, proroctví, modlitba, moudrostný výrok.\n\n"
            "4. **Sémantika a obsah** — Zpracovává text přes Stanza NLP (lemmatizace, POS, dependency) "
            "a extrahuje sémantické shluky a obsahové kategorie.\n\n"
            "5. **Náboženské prvky** — Detekuje přítomnost 23 náboženských tradic "
            "a 15 filozofických vlivů pomocí specializovaných lexikálních slovníků.\n\n"
            "6. **Síť slov** — Buduje sémantickou síť na základě PMI (síla asociace slov); "
            "identifikuje centrální pojmy a tematické shluky.\n\n"
            "7. **Textové vzory** — Analyzuje n-gramy, sémantické opozice (±3 věty) "
            "a formulaické výrazy; odhaluje rytmiku a opakující se struktury.\n\n"
            "8. **Styl a syntax** — Měří syntaktickou složitost větnou přes hloubku "
            "dependency stromu a počet klauzulí; identifikuje stylové shluky.\n\n"
            "9. **Kvalita výsledků** — Hodnotí spolehlivost klasifikace distribucí skóre jistoty "
            "a identifikuje věty s nízkou jistotou.\n\n"
            "10. **Dashboard** — Technický přehled: stav databáze, NLP model, zdroj textu, "
            "počet běhů a jejich historie.\n\n"
            "*Pro podrobnější popis viz sekci **Podrobný popis analýz** pod tlačítkem Spustit.*"
        ),
        "detail_expander_title": "📖 Podrobný popis analýz",
        "ana_bf_detail": (
            "**Teoretické zakotvení:** B. F. Skinner v díle *Verbal Behavior* (1957) redefinoval jazyk "
            "jako chování kontrolované stimuly a zpevňováním — ne jako systém znaků, ale jako funkci.\n\n"
            "**Typy verbálního chování:**\n"
            "- **Mand** — výrok kontrolovaný potřebou mluvčího (příkaz, prosba, žádost)\n"
            "- **Tact** — výrok kontrolovaný neverbálním stimulem (popis, pojmenování světa)\n"
            "- **Echoic** — výrok reprodukující verbální stimul jiné osoby (citace, opakování)\n"
            "- **Intraverbální** — výrok kontrolovaný vlastní předchozí řečí (odpověď, reakce)\n"
            "- **Autoklit** — výrok modifikující jiný výrok (kvalifikace, zdůraznění)\n\n"
            "**Interpretace:** Vysoký podíl mand výroků = direktivní text (zákon, rituál). "
            "Převaha tact výroků = deskriptivní nebo narativní text. "
            "Echoické formule jsou typické pro liturgické a rituální texty."
        ),
        "ana_qs_detail": (
            "**Teoretické zakotvení:** Quentin Skinner (1969–2002) rozvinul metodologii analýzy "
            "politického myšlení, v níž klíčovým pojmem je ilokuční záměr — co chce autor textem "
            "v konkrétním historickém kontextu *vykonat*. Vychází z teorie řečových aktů "
            "J. L. Austina a J. R. Searla.\n\n"
            "**Klíčové kategorie:**\n"
            "- **Ilokuční síla** — základní typ řečového aktu: direktiv, asertiv, komisiv, "
            "expresiv, deklarativ\n"
            "- **Primární záměr** — co autor chce dosáhnout: legitimace, příkaz, přesvědčování, "
            "varování, ideologické zpochybnění...\n"
            "- **Rétorická strategie** — jak záměr realizuje: apel na autoritu, přímé oslovení, "
            "rétorická otázka, příběhový příklad...\n\n"
            "**Interpretace:** Dominance direktiv a legitimace = autoritativní text. "
            "Převaha asertivů s apelem na písmo = exegetický charakter. "
            "Přítomnost ideologického zpochybnění = polemický kontext."
        ),
        "ana_verbal_detail": (
            "**Teoretické zakotvení:** Verbální vztahy klasifikují syntaktické vzorce "
            "přes kombinaci dependency vztahů a lexikálních markerů charakteristických "
            "pro daný komunikační žánr.\n\n"
            "**Žánrové typy:**\n"
            "- **Reported speech** — přímá řeč, citace, slovesa komunikace\n"
            "- **Genealogical** — záznamy rodokmenu (zplodit, narodit se, pokolení)\n"
            "- **Lyrical** — poetické a hymnické pasáže\n"
            "- **Prophetic** — prorocké výroky s formulí 'praví Hospodin'\n"
            "- **Request** — modlitba, prosba, žádost\n"
            "- **Wisdom** — moudrostné výroky (přísloví, poučení)\n\n"
            "**Interpretace:** Dominantní žánr odhaluje funkci textu v jeho literárním "
            "a kulturním kontextu. Srovnání žánrů mezi knihami ukazuje typologické rozdíly "
            "biblického kánonu."
        ),
        "ana_semantics_detail": (
            "**Technické zpracování:** Sémantická analýza pracuje s lemmatizovanými tokeny "
            "a syntaktickými závislostmi z Stanza NLP (model cs/pdt nebo en/ewt). "
            "Každá věta dostane sémantický shluk na základě distribuce klíčových lemmat.\n\n"
            "**Komponenty:**\n"
            "- **Lemmatizace** — převod slov na základní tvar\n"
            "- **POS-tagging** — slovní druhy a morfologické vlastnosti\n"
            "- **Dependency parsing** — syntaktické závislosti (podmět, předmět, přívlastek...)\n"
            "- **Sémantický shluk** — description / request / negation / neutral / uncertainty\n\n"
            "**Interpretace:** Vysoká frekvence negačních konstrukcí = polemický nebo prohibitivní "
            "charakter. Dominance description = narativní nebo deskriptivní register. "
            "Vysoký podíl request = modlitební nebo direktivní žánr."
        ),
        "ana_religious_detail": (
            "**Metodika:** Detekce náboženských elementů probíhá přes lexikální porovnávání "
            "s rozsáhlými frozenset slovníky 23 tradic a 15 filozofických vlivů. "
            "Každý element je reprezentován sadou lemmat typických pro danou tradici.\n\n"
            "**Tradice (výběr):** kresťanská česká/anglická, hebrejská, islámská, buddhistická, "
            "hinduistická, hermetická, kabalistická, súfijská, teosofická, šamanská, tantrická.\n\n"
            "**Filozofické vlivy:** platonismus, neoplatonismus, gnosticismus, stoicismus, "
            "aristotelismus, hermetismus, jungiánismus, new-age a další.\n\n"
            "**Interpretace:** Přítomnost tradice je měřena počtem lemmat z daného slovníku "
            "v textu. Nejde o důkaz příslušnosti textu k tradici — spíše o ukazatel "
            "tematické příbuznosti. Různé tradice mohou sdílet lexikum (např. 'duch', 'světlo')."
        ),
        "ana_network_detail": (
            "**Metodika:** Sémantická síť je budována na základě PMI "
            "(Pointwise Mutual Information) — statistické míry, která měří, "
            "o kolik častěji se dvě slova vyskytují spolu oproti náhodě.\n\n"
            "**Komponenty sítě:**\n"
            "- **PMI score** — síla asociace dvou slov; vyšší = silnější koexistence\n"
            "- **Degree centrality** — počet sémantických vazeb slova\n"
            "- **Weighted centrality** — kombinace PMI a počtu vazeb\n\n"
            "**Interpretace:** Slova s vysokou centralitou jsou sémantickým jádrem textu. "
            "Sémantické shluky odhalují tematická uskupení pojmů. "
            "Metoda je náročná na výpočetní zdroje a doporučujeme ji pouze "
            "pro analýzu celého korpusu (záložka Biblický korpus)."
        ),
        "ana_patterns_detail": (
            "**Metodika:** Analýza opakujících se vzorů na lexikální, stylistické "
            "a sémantické úrovni.\n\n"
            "**Komponenty:**\n"
            "- **Bigramy/trigramy** — nejčastější slovní dvojice a trojice; "
            "odhalují ustálené fráze a kolokace\n"
            "- **Sémantické opozice** — protikladné páry slov (život/smrt, světlo/tma) "
            "detegované v kontextu ±3 vět; ukazují rétorickou polarizaci textu\n"
            "- **TF-IDF** — slova charakteristická pro konkrétní knižní jednotku "
            "oproti ostatním\n\n"
            "**Interpretace:** Opakující se n-gramy odhalují formulaické a rituální vzorce. "
            "Sémantické opozice jsou klíčovým rétorický nástrojem biblického diskurzu."
        ),
        "ana_style_detail": (
            "**Metodika:** Syntaktická analýza měří složitost vět přes metriky "
            "dependency stromu. Stylová analýza identifikuje shluky knih "
            "na základě TF-IDF frekvencí slov.\n\n"
            "**Metriky:**\n"
            "- **Avg tree depth** — průměrná hloubka dependency stromu "
            "(1–2 = jednoduchá věta, 4+ = komplexní)\n"
            "- **Avg clause count** — průměrný počet vedlejších vět na větu\n"
            "- **Silhouette score** — míra shody knihy se svým stylovým shlukem\n\n"
            "**Interpretace:** Nízká hloubka stromu = direktivní nebo aforistický styl "
            "(zákon, moudrostná literatura). Vysoká hloubka = argumentativní nebo "
            "narativní styl. Tato analýza je výpočetně náročná."
        ),
        "ana_quality_detail": (
            "**Metodika:** Spolehlivost klasifikace je hodnocena přes skóre jistoty "
            "(confidence score 0.0–1.0), které odráží shodu klasifikátoru "
            "s trénovanými vzory.\n\n"
            "**Pásma jistoty:**\n"
            "- **0–30 %** — věta nebyla spolehlivě klasifikována "
            "(krátké nebo syntakticky nestandardní věty)\n"
            "- **30–60 %** — nízká jistota (nejasný rétorický kontext, "
            "více možných záměrů)\n"
            "- **60–100 %** — spolehlivá klasifikace\n\n"
            "**Interpretace:** Vyšší podíl vět s nízkou jistotou naznačuje rétorickou "
            "komplexnost textu nebo nedostatečné pokrytí trénovacích vzorů. "
            "Doporučujeme manuálně ověřit věty s confidence < 0.4."
        ),
        "ana_dashboard_detail": (
            "**Obsah dashboardu:**\n"
            "- **Source** — zdroj textu (název souboru nebo 'pasted_text')\n"
            "- **Sentences** — počet analyzovaných vět\n"
            "- **DB rows** — celkový počet řádků v databázi skinner_analysis\n"
            "- **Bible runs** — počet behů z biblického korpusu\n"
            "- **Upload runs** — počet behů z nahraných textů\n"
            "- **NLP model** — aktivní model Stanza (cs nebo en)\n\n"
            "**Doporučení:** Pokud počet řádků v DB neočekávaně roste, "
            "zkontrolujte duplicitní behy. Doporučujeme pravidelné zálohování "
            "`output/bible_analysis.db`. Pro reset databáze smažte soubor DB "
            "a spusťte `k_apply_all_to_bible.py` znovu."
        ),
        "select_analyses": "Vyberte okruhy analýz",
        "run_hint": "Výsledky se zobrazí v záložce **Výsledky**.",
        "results_empty": "Nejprve spusťte analýzu v záložce Analyzovat text.",
        "results_title": "Výsledky analýzy",
        "results_ready_msg": "Analýza dokončena — výsledky jsou v záložce Výsledky.",
        # 10 analysis modules
        "ana_bf_name":        "B.F. Skinner",
        "ana_bf_q":           "Jaký typ verbálního chování text reprezentuje — příkaz, pozorování, citace?",
        "ana_qs_name":        "Q. Skinner",
        "ana_qs_q":           "Co chce autor textem dosáhnout a jakou rétorickou strategii použil?",
        "ana_verbal_name":    "Verbální vztahy",
        "ana_verbal_q":       "Jaký žánr verbální interakce dominuje — dialog, chvála, nářek, moudrý výrok?",
        "ana_semantics_name": "Sémantika a obsah",
        "ana_semantics_q":    "Jaká sémantická pole a obsahové kategorie v textu dominují?",
        "ana_religious_name": "Náboženské prvky",
        "ana_religious_q":    "Které náboženské tradice, prvky a filozofické vlivy jsou v textu přítomny?",
        "ana_network_name":   "Síť slov",
        "ana_network_q":      "Které pojmy tvoří jádro sémantické sítě a jak jsou navzájem propojeny?",
        "ana_patterns_name":  "Textové vzory",
        "ana_patterns_q":     "Jaké lexikální a stylistické vzory se v textu opakují?",
        "ana_style_name":     "Styl a syntax",
        "ana_style_q":        "Jaká je syntaktická složitost textu a liší se styl mezi jeho částmi?",
        "ana_quality_name":   "Kvalita výsledků",
        "ana_quality_q":      "Jak spolehlivá je klasifikace a kde může být nejistá?",
        "ana_dashboard_name": "Dashboard",
        "ana_dashboard_q":    "Jaký je technický stav analýzy a které moduly proběhly úspěšně?",
        # Section 16 — new analytics
        "complexity_title": "Syntaktická složitost podle knih",
        "complexity_desc": "Průměrná hloubka závislostního stromu a průměrný počet vedlejších vět na větu v každé biblické knize. Vyšší hodnota = syntakticky složitější text.",
        "tact_autoclitic_title": "Tact vs. Autoclitic podle knih",
        "tact_autoclitic_desc": "Podíl vět klasifikovaných jako **tact** (asertiv — popis skutečnosti) vs. **autoclitic** (deklarativ — komentář k vlastní řeči) v každé biblické knize.",
        "traditions_title": "Tradice a filozofické vlivy — přehled",
        "cluster_labels": {
            "royal":       "Královská moc",
            "kinship":     "Příbuzenství",
            "theological": "Teologické",
            "war":         "Válka",
            "wisdom":      "Moudrost",
            "cultic":      "Kultický",
            "divine":      "Božské",
            "moral":       "Morální",
        },
        "traditions_desc": "Počet aktivních lexikálních kategorií pro každou tradici / počet termínů pro každý filozofický vliv zahrnutý v analýze.",
        "x_depth": "Průměrná hloubka stromu",
        "x_clauses": "Průměrný počet klauzulí",
        "x_terms": "Termíny",
        "x_categories": "Kategorie",
        # Opposition polarity & directed network
        "opposition_window_note": "Opozice detekované v kontextovém okně ±3 vět.",
        "opposition_polarity_title": "Polarita opozic — pozitivní vs. negativní framing",
        "opposition_polarity_desc": "Pro každý opozičný pár: kolik vět ho rámuje z **pozitivního pólu** (světlo, život, dobro…) vs. z **negativního pólu** (tma, smrt, zlo…). Neutrální = oba póly přítomny v kotevní větě současně.",
        "opposition_directed_title": "Orientovaná síť opozic — top hrany",
        "opposition_directed_desc": "Každá hrana jde od **dominantního pólu** (přítomného v kotevní větě) k **podřízenému pólu** (přítomném v okně). Váha = počet doložených výskytů tohoto směru.",
        "opposition_examples_title": "Příklady vět s opozicí",
        "opposition_examples_desc": "Ukázkové věty, v jejichž bezprostředním kontextu (±3 věty) byl detekován opozičný pár.",
        "lbl_positive": "Pozitivní pól",
        "lbl_negative": "Negativní pól",
        "lbl_both": "Oba póly",
        "col_source": "Zdroj",
        "col_target": "Cíl",
        "col_weight": "Váha",
        "filter_pair": "Filtrovat pár",
        # Context parameter panel
        "ctx_expander":          "⚙️ Kontext analýzy (volitelné)",
        "ctx_source_label":      "Zdroj textu",
        "ctx_interaction_label": "Typ interakce",
        "ctx_stimulus_label":    "Řídící stimul",
        "ctx_source_opts": {
            "unknown":           "— neznámý",
            "written_record":    "Psaný dokument",
            "uploaded_document": "Nahraný dokument",
            "spoken_record":     "Mluvený záznam",
            "transcript":        "Přepis",
        },
        "ctx_interaction_opts": {
            "unknown":   "— neznámý",
            "monologue": "Monolog",
            "dialogue":  "Dialog",
        },
        "ctx_stimulus_opts": {
            "unknown":                 "— neznámý",
            "nonverbal_object":        "Neverbální objekt/událost",
            "written_verbal_stimulus": "Psaný text",
            "auditory_verbal_stimulus":"Slyšená řeč",
            "question_prompt":         "Otázka jako stimul",
            "answer_context":          "Výrok je odpověď",
            "private_event":           "Vnitřní stav",
            "none":                    "Žádný",
        },
        "ctx_warn_qa_mono":      "Nekonzistentní kontext: stimulus Q&A (otázka/odpověď) předpokládá dialog, ale interakce je nastavena jako monolog.",
        "ctx_warn_audio_written":"Nekonzistentní kontext: psaný/nahraný zdroj nemůže být řízen sluchovým verbálním stimulem — to předpokládá mluvenou interakci.",
        "ctx_warn_written_spoken":"Nekonzistentní kontext: mluvený záznam nemůže být řízen psaným stimulem.",
        "ctx_warn_dialogue_none":"Nekonzistentní kontext: dialog vyžaduje verbální stimul — stimulus 'žádný' dialog vylučuje.",
        # Tab 4
        "tab_compare": "🔄 Porovnání",
        "compare_title": "Porovnání analýz",
        "compare_placeholder": (
            "Tato záložka bude obsahovat nástroje pro porovnání výsledků analýzy "
            "nahraného textu s biblickým korpusem (BKR). "
            "Funkce je připravena k implementaci ve fázi 2."
        ),
        # Segmentation preview (Tab 1)
        "seg_preview_title": "Náhled segmentace",
        "seg_method_chapter": "kapitoly (strukturní nadpisy)",
        "seg_method_section": "sekce (podnadpisy)",
        "seg_method_single": "jeden dokument (bez struktury)",
        "seg_preview_unit": "jednotka",
        "seg_preview_units": "jednotky",
    },

    "sk": {
        "app_title": "📖 Skinner Pipeline",
        "app_subtitle": "Analýza českého biblického textu — komunikačná sila · zámer · rétorika",
        "tab_analyze": "📝 Analyzovať text",
        "tab_bible": "📚 Biblický korpus",
        "export_pdf": "📄  Exportovať report ako PDF",
        "pdf_generating": "Generuje sa PDF…",
        "pdf_ready": "Report pripravený na stiahnutie.",
        "pdf_error": "Chyba pri generovaní PDF",
        "pdf_filename": "skinner_report.pdf",
        "lang_label": "Jazyk",
        "upload_header": "Nahrajte alebo vložte text",
        "upload_label": "Nahrať .txt alebo .pdf",
        "paste_label": "…alebo vložiť text sem",
        "run_button": "▶  Spustiť analýzu",
        "reading_file": "Čítanie súboru…",
        "running_pipeline": "Prebieha analýza…",
        "no_text_warning": "Nahrajte súbor alebo vložte text.",
        "metric_sentences": "Viet celkom",
        "metric_classified": "Klasifikovaných",
        "metric_confidence": "Priemerná istota",
        "metric_intentions": "Rôznych zámerov",
        "intent_pie_title": "Zámery",
        "intent_pie_desc": "Koláčový graf ukazuje, **čo sa hovoriaci snaží dosiahnuť** v každej vete — či prikazuje, varuje, sľubuje, chváli atď. Každý výsek zodpovedá jednému zámeru. Väčší výsek = zámer sa v texte vyskytuje častejšie.",
        "strategy_bar_title": "Rétorické stratégie",
        "strategy_bar_desc": "**Rétorická stratégia** je spôsob, akým hovoriaci presadzuje svoj zámer — napr. odvolaním sa na autoritu, sľubom odmeny alebo kladením rečníckych otázok. Graf zobrazuje 10 najčastejších stratégií.",
        "force_pie_title": "Typ rečového aktu",
        "force_pie_desc": "Klasifikácia každej vety podľa základného komunikačného typu: **direktívy** = príkazy/žiadosti · **asertívy** = tvrdenia/výroky · **komisívy** = sľuby · **expresívy** = emocionálne výrazy · **deklaratívy** = vyhlásenia nového stavu vecí.",
        "conf_hist_title": "Istota klasifikácie per zámer",
        "conf_hist_desc": "Histogram ukazuje, ako **si bol algoritmus istý** pri klasifikácii viet. Hodnoty blízko 1,0 = vysoká istota. Hodnoty blízko 0,3 = neistá alebo chýbajúca klasifikácia.",
        "conf_table_desc": "Priemerná istota algoritmu pre každý zámer zvlášť.",
        "secondary_intent_title": "Sekundárne zámery",
        "secondary_intent_desc": "Niektoré vety nesú okrem hlavného zámeru aj **sekundárny zámer** — druhý komunikačný cieľ hovoriaceho. Graf ukazuje ich rozloženie.",
        "section_sentence_table": "Výsledky po vetách",
        "filter_intention": "Filtrovať zámer",
        "filter_strategy": "Filtrovať stratégiu",
        "download_csv": "⬇  Stiahnuť ako CSV",
        "col_id": "#",
        "col_sentence": "Veta",
        "col_intention": "Zámer",
        "col_2nd_intention": "2. zámer",
        "col_force": "Typ rečového aktu",
        "col_strategy": "Stratégia",
        "col_confidence": "Istota",
        "col_reason": "Zdôvodnenie",
        "col_locution": "Lokúcia",
        "col_convention": "Konvencia",
        "col_pol_vocab": "Polit. slovník",
        "bible_header": "Analýza biblického korpusu",
        "bible_caption": "Predpočítané z českej Biblie (Kralická, BKR) — spustite `k_apply_all_to_bible.py` pre aktualizáciu.",
        "metric_total": "Viet celkom",
        "metric_books": "Biblické knihy",
        "metric_coverage": "Klasifikovaných",
        "metric_mean_conf": "Priemerná istota",
        "no_db": "Databáza `output/bible_analysis.db` nenájdená. Najprv spustite pipeline.",
        "sec_intention": "📊 Analýza zámerov",
        "all_intentions_title": "Zámery — všetky knihy",
        "all_intentions_desc": "Distribúcia zámerov v celom korpuse — dominantné zámery charakterizujú rétoricko-komunikačné pole textu.",
        "force_all_title": "Typy rečových aktov",
        "force_all_desc": "Distribúcia typov rečových aktov v celom korpuse.",
        "intent_book_heatmap_title": "Zámery podľa kníh",
        "intent_book_heatmap_desc": "Rétoricképrofily jednotlivých kníh — tmavšia = zámer dominuje v danej knihe.",
        "sec_strategy": "🎯 Analýza stratégií",
        "all_strategies_title": "Rétorické stratégie — všetky knihy",
        "all_strategies_desc": "Rétoricke techniky v celom korpuse — srovnanie ukazuje argumentatívne stratégie textu.",
        "pvoc_title": "Najčastejšia politická slovná zásoba",
        "pvoc_desc": "Slová spjaté s mocou, autoritou a zákonom — ukazateľ politického diskurzu textu.",
        "strat_book_heatmap_title": "Stratégie podľa kníh",
        "strat_book_heatmap_desc": "Rétoricképrofily kníh — tmavšia = stratégia dominuje v danej knihe.",
        "sec_ratios": "⚖️ Kľúčové pomery podľa kníh",
        "directive_assertive_title": "Direktívne vs. asertívne vety",
        "directive_assertive_desc": "Príkazové (červená) vs. výrokové (modrá) vety — kľúčový ukazateľ autoritatívnosti a žánru textu.",
        "legit_ratio_title": "Legitimácia · Spochybnenie · Intervencia",
        "legit_ratio_desc": "Skinnerove analytické kategórie mocenského diskurzu: legitimácia autority, spochybnenie protivníka, výzva k akcii.",
        "no_ratios": "Spustite `l_taxonomy_analytics.py` pre výpočet pomerov.",
        "sec_religious": "✝️ Náboženské prvky",
        "element_coverage_title": "Výskyt náboženských prvkov",
        "element_coverage_desc": "Počet viet s danými náboženskými prvkami — ukazuje tematické zameranie korpusu.",
        "philosophy_title": "Filozofické tradície",
        "philosophy_desc": "Prítomnosť filozofických a teologických tradícií v texte.",
        "rel_elements": {
            "covenant_law":      "Zmluva a zákon",
            "prophetic_speech":  "Prorocká reč",
            "divine_hierarchy":  "Božská hierarchia",
            "legal":             "Právne prvky",
            "life_death":        "Život a smrť",
            "wisdom":            "Múdrosť",
            "ritual_sacrifice":  "Rituálna obeť",
            "moral":             "Morálne prvky",
            "war_conflict":      "Vojna a konflikt",
            "eschatology":       "Eschatológia",
            "royal_power":       "Kráľovská moc",
            "monotheism":        "Monoteizmus",
            "genealogy_lineage": "Genealógia",
            "divine":            "Božské prvky",
            "kinship":           "Príbuzenstvo",
        },
        "rel_philosophy": {
            "platonic":      "Platonizmus",
            "neoplatonic":   "Neoplatonizmus",
            "stoic":         "Stoicizmus",
            "gnostic":       "Gnóza",
            "aristotelian":  "Aristotelizmus",
            "pythagorean":   "Pythagorejci",
            "epicurean":     "Epikurejci",
            "hermetic":      "Hermétizmus",
            "sufi":          "Súfizmus",
            "kabbalistic":   "Kabala",
            "theosophical":  "Teosofia",
            "jungian":       "Jungiánizmus",
            "new_age":       "New Age",
            "shamanic":      "Šamanizmus",
            "tantric":       "Tantrické vplyvy",
        },
        "density_heatmap_title": "Hustota náboženských prvkov podľa kníh",
        "density_heatmap_desc": "Podiel viet s danými náboženskými prvkami per kniha (0–1) — tmavšia = prvok dominuje v danej knihe.",
        "sec_clusters": "🔗 Konceptové zhluky a sémantické opozície",
        "cluster_bubble_title": "Konceptové zhluky",
        "cluster_bubble_desc": "Sémantické zhluky slov — väčšia bublina = viac prepojených dvojíc, poloha vpravo = silnejšia vzájomná príťažlivosť slov.",
        "opposition_title": "Najsilnejšie sémantické opozície",
        "opposition_desc": "Najčastejšie doložené protikladné páry slov v kontexte ±3 viet.",
        "sec_centrality": "🌐 Sémantická centralita slov",
        "top_n_slider": "Počet zobrazených slov",
        "centrality_bar_title": "Najdôležitejšie slová podľa sémantickej centrality",
        "centrality_bar_desc": "Sémanticky najdôležitejšie slová — centrálne uzly siete významov textu.",
        "no_centrality": "Spustite `r_word_network.py` a `s_word_relations_analytics.py`.",
        "sec_style": "✍️ Štýl a autorstvo",
        "style_table_desc": "Štýlové zhluky biblických kníh — knihy v jednom zhluku zdieľajú podobný slovník a rétoricképrofil.",
        "cluster_terms_title": "Najcharakteristickejšie slová zhluku",
        "cluster_terms_desc": "Slová najcharakteristickejšie pre daný štýlový zhluk — odlišujú ho od ostatných.",
        "select_cluster": "Zhluk",
        "no_style": "Spustite `x_style_authorship.py`.",
        "sec_dependency": "🏗️ Syntaktická štruktúra",
        "dep_bar_title": "Najčastejšie syntaktické vzťahy",
        "dep_bar_desc": "Typy **závislostných vzťahov** medzi slovami (závislostná/dependency gramatika). Napr. `nsubj` = podmet, `obj` = predmet, `amod` = prídavné meno ako prívlastok. Graf ukazuje, ako sú vety syntakticky štruktúrované.",
        "dep_heatmap_title": "Syntaktické vzťahy podľa kníh",
        "dep_heatmap_desc": "Ako sa **distribúcia syntaktických vzťahov** líši medzi jednotlivými biblickými knihami. Tmavšia bunka = daný typ syntaktického vzťahu sa v knihe vyskytuje výraznejšie.",
        "sec_verbal": "💬 Slovesné vzťahy",
        "verbal_types_title": "Typy slovesných vzťahov",
        "verbal_types_desc": "Klasifikácia syntaktických vzťahov, v ktorých **vystupujú slovesá**. Popisné vzťahy (`descriptive_relation`) spájajú sloveso s jeho argumentmi, priama reč (`reported_speech`) zachytáva doslovné citáty, ostatné typy označujú špecifické funkcie (modlitba, proroctvo, genealógia atď.).",
        "verbal_conf_title": "Istota klasifikácie slovesných vzťahov",
        "verbal_conf_desc": "**Priemerná istota algoritmu** pri klasifikácii každého typu slovesného vzťahu. Vyššia hodnota = algoritmus je pri rozpoznávaní tohto typu sebajistejší.",
        "verbal_book_heatmap_title": "Slovesné vzťahy podľa kníh — heatmapa",
        "verbal_book_heatmap_desc": "Počet každého **typu slovesného vzťahu** v jednotlivých biblických knihách. Tmavšia bunka = daný typ sa v knihe vyskytuje výraznejšie.",
        "sec_taxonomy": "🏷️ Skinnerova behaviorálna taxonómia",
        "tax_class_title": "Skinnerove funkčné triedy",
        "tax_class_desc": "Klasifikácia viet podľa **Skinnerovej behaviorálnej taxonómie** jazyka: `tact` = popis/pomenovanie sveta · `mand` = príkaz alebo žiadosť · `echoic` = citácia alebo opakovanie · `intraverbal` = odpoveď na verbálny podnet · `autoclitic` = komentár k vlastnej reči. `none` = vety bez priradenej triedy.",
        "tax_dialogue_title": "Hustota dialógu podľa kníh",
        "tax_dialogue_desc": "**Podiel viet, ktoré sú súčasťou dialógu** (priamej reči) v každej biblickej knihe. Vyššia hodnota = kniha obsahuje viac dialógov a priamych prehovorov.",
        "tax_control_title": "Rola kontroly",
        "tax_control_desc": "Klasifikácia viet z hľadiska **vzťahu kontroly** medzi hovoriacim a poslucháčom: `stimulus` = hovoriaci kontroluje poslucháča, `response` = hovoriaci reaguje na podnet, `record` = neutrálny záznam bez jasnej kontroly.",
        "sec_word_rel": "🔤 Sémantické asociácie slov",
        "top_pmi_title": "Najsilnejšie sémantické asociácie",
        "top_pmi_desc": "Dvojice slov s **najvyšším skóre PMI** (Pointwise Mutual Information) — miera toho, ako silno sa dve slová v texte navzájom priťahujú. Vysoké PMI = tieto dve slová sa v texte vyskytujú spolu oveľa častejšie, ako by zodpovedalo náhode.",
        "top_pmi_word1": "Slovo 1",
        "top_pmi_word2": "Slovo 2",
        "top_pmi_count": "Počet výskytov",
        "top_pmi_pmi": "PMI skóre",
        "most_connected_title": "Najviac prepojené slová",
        "most_connected_desc": "Slová s **najvyšším počtom sémantických väzieb** — t.j. slová, ktoré sa v texte silno asociujú s najväčším počtom iných slov. Sú to sémantické centrá textu.",
        "no_word_rel": "Spustite `s_word_relations_analytics.py`.",
        "sec_corpus_density": "📐 Hustota tematických kategórií",
        "corpus_density_title": "Hustota kategórií podľa kníh (vety)",
        "corpus_density_desc": "Podiel viet v každej knihe, ktoré obsahujú prvky danej **tematickej kategórie** (zmluva/zákon, božskosť, eschatológia, genealógia, príbuzenstvo, morálka, proroctvo, rituál a ďalšie — celkom 16 kategórií). Hodnota 0,30 znamená, že 30 % viet v danej knihe patrí do danej kategórie.",
        "x_intention": "Zámer",
        "x_force": "Typ rečového aktu",
        "x_strategy": "Stratégia",
        "x_count": "Počet",
        "x_score": "Skóre",
        "x_book": "Kniha",
        "x_word": "Slovo",
        "x_confidence": "Istota",
        "x_avg_pmi": "Priemerné PMI",
        "x_edges": "Väzby",
        "x_ratio": "Podiel",
        "x_element": "Prvok",
        "x_relation": "Typ vzťahu",
        "x_class": "Trieda",
        "x_density": "Hustota",
        "x_tfidf": "TF-IDF",
        "x_pmi": "PMI",
        "x_connections": "Počet väzieb",
        "x_weighted": "Vážené skóre",
        # Section 13
        "sec_patterns": "🔠 Textové vzory",
        "wordcloud_title": "Oblak slov — najčastejšie slová v korpuse",
        "wordcloud_desc": "Najčastejšie lematizované slová v celom korpuse — väčšie = početnejšie.",
        "bigrams_title": "Najčastejšie slovné dvojice",
        "bigrams_desc": "Najčastejšie slovné dvojice — ustálené frázy a kolokácie textu.",
        "trigrams_title": "Najčastejšie slovné trojice",
        "trigrams_desc": "Najčastejšie slovné trojice — formulaické výrazy a opakujúce sa štruktúry.",
        "tfidf_heatmap_title": "Charakteristické slová podľa kníh",
        "tfidf_heatmap_desc": "Slová typické pre danú knihu a nie pre ostatné — odhaľuje špecifickú lexiku každej knihy.",
        "x_frequency": "Početnosť",
        "x_ngram": "Slovné spojenie",
        # Section 14
        "sec_semantics": "🔬 Sémantická analýza",
        "radar_title": "Sémantické typy viet podľa kníh",
        "radar_desc": "Lúčový (radar) graf zobrazuje **podiel rôznych sémantických typov viet** v každej biblickej knihe. Každá os zodpovedá jednému sémantickému typu: popis, neutrálny výrok, žiadosť, negácia/protiklad. Čím ďalej od stredu, tým vyšší podiel viet tohto typu.",
        "antithetical_title": "Vety s protikladnou štruktúrou",
        "antithetical_desc": "Zobrazuje vety, v ktorých bol algoritmom detekovaný **protikladný alebo negačný vzorec** — vety, kde je niečo odmietané, negované alebo kladené do protikladu. Príklad: 'Nekradni', 'Nezabiješ', 'Nie som..., ale...'",
        "antithetical_count_title": "Počet protikladných viet podľa kníh",
        "antithetical_count_desc": "Koľko viet s protikladným vzorcom obsahuje každá biblická kniha.",
        "lexical_reinf_title": "Miera lexikálneho opakovania podľa kníh",
        "lexical_reinf_desc": "**Lexikálne opakovanie** meria, ako často sa rovnaké slová opakujú v rámci jednej vety. Vyššia hodnota = vety v danej knihe obsahujú viac opakujúcich sa slov (typické pre poetické alebo rituálne texty). Hodnota 0 = každé slovo sa vo vete vyskytuje len raz.",
        "x_reinforcement": "Miera opakovania",
        "filter_book_label": "Filtrovať knihu",
        "filter_group_label": "Skupina kníh",
        "group_all": "— Celá Biblia",
        "group_pentateuch":     "Pentateuch",
        "group_historical":     "Historické knihy",
        "group_wisdom":         "Múdrostné knihy",
        "group_major_prophets": "Veľkí proroci",
        "group_minor_prophets": "Malí proroci",
        "group_gospels_acts":   "Evanjeliá a Skutky",
        "group_pauline":        "Pavlove listy",
        "group_general":        "Všeobecné listy",
        "group_apocalypse":     "Apokalypsa",
        "no_patterns": "Dáta nie sú k dispozícii.",
        "no_group_data": "Pre vybranú skupinu nie sú dostupné dáta.",
        # Section 15
        "sec_quality": "✅ Kvalita pipeline",
        "quality_overall_desc": "Prehľad **kvality automatickej klasifikácie** celého korpusu: koľko viet bolo klasifikovaných, aká istá bol algoritmus a ktoré knihy alebo triedy sa klasifikovali menej spoľahlivo.",
        "coverage_book_title": "Pokrytie klasifikáciou podľa kníh",
        "coverage_book_desc": "Percentuálny podiel **správne klasifikovaných viet** v každej biblickej knihe. Hodnoty pod 95 % signalizujú, že algoritmus mal s danou knihou viac ťažkostí.",
        "conf_bins_title": "Rozloženie istoty klasifikácie",
        "conf_bins_desc": "Vety rozdelené do troch pásiem istoty: **0–30 %** = nebolo možné klasifikovať, **30–60 %** = nízka istota, **60–100 %** = spoľahlivá klasifikácia. Ideálne by pásmo 60–100 % malo zahrnúť čo najviac viet.",
        "consistency_title": "Konzistencia klasifikácie lemmat",
        "consistency_desc": "Každé lemma (základný tvar slova) by malo byť konzistentne klasifikované do rovnakej triedy zámeru. Graf zobrazuje **lemmata klasifikované do viacerých rôznych tried** — tieto lemmata sú pre algoritmus nejednoznačné.",
        "outliers_title": "Knihy s neobvyklým pomerom tried",
        "outliers_desc": "Knihy, kde je podiel určitej triedy zámeru **výrazne vyšší alebo nižší** oproti priemeru celého korpusu (štatistická odchýlka |z| > 2). Označuje knihy s neobvyklou rétoricko-textovou štruktúrou.",
        "sample_title": "Vzorové vety — manuálna kontrola",
        "sample_desc": "Náhodný výber 20 klasifikovaných viet pre **manuálne overenie správnosti** klasifikácie. Odporúčame skontrolovať najmä vety s nižšou istotou.",
        "x_coverage": "Pokrytie (%)",
        "no_eval": "Spustite `v_eval_pipeline.py` pre výpočet metrík kvality.",
        "col_total": "Celkom",
        "col_classified_q": "Klasif.",
        "col_coverage_q": "Pokrytie (%)",
        "col_z_score": "Z-skóre",
        "col_label_q": "Trieda",
        "conf_band_low": "Nízka (0–30 %)",
        "conf_band_mid": "Stredná (30–60 %)",
        "conf_band_high": "Vysoká (60–100 %)",
        "x_sentences": "Počet viet",
        "ambiguous_lemma_title": "Nejednoznačné lemmata",
        "col_lemma": "Lemma",
        "col_classes": "Triedy",
        "col_n_classes": "Počet tried",
        "lbl_directive": "Direktíva",
        "lbl_assertive": "Asertív",
        "lbl_legitimation": "Legitimácia",
        "lbl_contestation": "Spochybnenie",
        "lbl_intervention": "Intervencia",
        "col_style_cluster": "Štýlový zhluk",
        "col_silhouette": "Silhouette",
        # Section 16 — Linguistic features
        "sec_ling_features": "🔡 Lingvistické príznaky",
        "ling_ttr_desc": "**Lexikálna diverzita** (type-token ratio) — pomer jedinečných lemiem k celkovému počtu. Nižšia hodnota = formulaickejší, rituálnejší text.",
        "ling_ttr_title": "Priemerná lexikálna diverzita (TTR) podľa kníh",
        "ling_bool_desc": "Percentuálny podiel viet s koordináciou, datívom a nepriamym objektom. Signalizuje syntaktickú komplexitu a argumentačnú štruktúru.",
        "ling_bool_title": "Syntaktické príznaky (% viet) podľa kníh",
        "ling_pos_desc": "Priemerný počet prídavných mien, prísloviek a zámen na vetu. Signalizuje deskriptívne bohatstvo a priame oslovovanie.",
        "ling_pos_title": "Morfologické príznaky (priemer na vetu) podľa kníh",
        "ling_formulaic_desc": "Top 15 viet s najnižšou lexikálnou diverzitou (min. 5 slov) — pravdepodobne formulaické alebo rituálne výroky.",
        "ling_formulaic_title": "Najformulaickejšie vety (najnižší TTR)",
        "col_ttr": "TTR",
        "lbl_coordination": "Koordinácia",
        "lbl_dative": "Datív",
        "lbl_iobj": "Nepriamy objekt",
        "lbl_adj": "Prídavné mená",
        "lbl_adv": "Príslovky",
        "lbl_pron": "Zámená",
        # Save to DB
        "save_button": "💾  Uložiť do databázy",
        "save_caption": "Uloží výsledky analýzy do `bible_analysis.db` ako samostatný beh — oddelený od biblického korpusu.",
        "save_success": "Uložené",
        "save_run_id_label": "run_id",
        "save_rows_label": "viet uložených",
        "save_already": "Už uložené",
        # Tab 3 + checkboxes
        "tab_results": "📋 Výsledky",
        "about_title": "ℹ️ O analýzach",
        "about_text": (
            "Prehľad 10 analytických okruhov:\n\n"
            "1. **B.F. Skinner** — Klasifikuje vety podľa behavioriálnej taxonómie jazyka: "
            "mand (príkaz), tact (popis sveta), echoic (citácia), intraverbálny (reakcia na reč), "
            "autoklit (komentár k vlastnej reči). Vychádza z Verbal Behavior (Skinner, 1957).\n\n"
            "2. **Q. Skinner** — Identifikuje ilokučný zámer každej vety (čo chce hovoriaci vykonať) "
            "a rétorickú stratégiu (ako zámer dosahuje). Vychádza z teórie rečových aktov Austina "
            "a Quintina Skinnera (1969–2002).\n\n"
            "3. **Verbálne vzťahy** — Klasifikuje žáner verbálnej interakcie: priama reč, "
            "genealógia, lyrika, proroctvo, modlitba, múdrostný výrok.\n\n"
            "4. **Sémantika a obsah** — Spracováva text cez Stanza NLP (lematizácia, POS, dependency) "
            "a extrahuje sémantické zhluky a obsahové kategórie.\n\n"
            "5. **Náboženské elementy** — Deteguje prítomnosť 23 náboženských tradícií "
            "a 15 filozofických vplyvov pomocou špecializovaných lexikálnych slovníkov.\n\n"
            "6. **Sieť slov** — Buduje sémantickú sieť na základe PMI (sila asociácie slov); "
            "identifikuje centrálne pojmy a tematické zoskupenia.\n\n"
            "7. **Textové vzory** — Analyzuje n-gramy, sémantické opozície (±3 vety) "
            "a formulaické výrazy; odhaľuje rytmiku a opakujúce sa štruktúry.\n\n"
            "8. **Štýl a syntax** — Meria syntaktickú komplexnosť viet cez hĺbku "
            "dependency stromu a počet vedľajších viet; identifikuje štýlové zhluky.\n\n"
            "9. **Kvalita výsledkov** — Hodnotí spoľahlivosť klasifikácie distribúciou skóre istoty "
            "a identifikuje vety s nízkou istotou.\n\n"
            "10. **Dashboard** — Technický prehľad: stav databázy, NLP model, zdroj textu, "
            "počet behov a ich história.\n\n"
            "*Pre podrobnejší popis pozri sekciu **Podrobný popis analýz** pod tlačidlom Spustiť.*"
        ),
        "detail_expander_title": "📖 Podrobný popis analýz",
        "ana_bf_detail": (
            "**Teoretické zakotvenie:** B. F. Skinner v diele *Verbal Behavior* (1957) redefinoval jazyk "
            "ako správanie kontrolované stimulmi a spevňovaním — nie ako systém znakov, ale ako funkciu.\n\n"
            "**Typy verbálneho správania:**\n"
            "- **Mand** — výrok kontrolovaný potrebou hovoriaceho (príkaz, prosba, žiadosť)\n"
            "- **Tact** — výrok kontrolovaný neverbálnym stimulom (popis, pomenovanie sveta)\n"
            "- **Echoic** — výrok reprodukujúci verbálny stimul inej osoby (citácia, opakovanie)\n"
            "- **Intraverbálny** — výrok kontrolovaný vlastnou predchádzajúcou rečou (odpoveď, reakcia)\n"
            "- **Autoklit** — výrok modifikujúci iný výrok (kvalifikácia, zdôraznenie)\n\n"
            "**Interpretácia:** Vysoký podiel mand výrokov = direktívny text (zákon, rituál). "
            "Prevaha tact výrokov = deskriptívny alebo naratívny text. "
            "Echoické formuly sú typické pre liturgické a rituálne texty."
        ),
        "ana_qs_detail": (
            "**Teoretické zakotvenie:** Quentin Skinner (1969–2002) rozvinul metodológiu analýzy "
            "politického myslenia, v ktorej je kľúčovým pojmom ilokučný zámer — čo chce autor textom "
            "v konkrétnom historickom kontexte *vykonať*. Vychádza z teórie rečových aktov "
            "J. L. Austina a J. R. Searla.\n\n"
            "**Kľúčové kategórie:**\n"
            "- **Ilokučná sila** — základný typ rečového aktu: direktív, asertív, komisív, "
            "expresív, deklaratív\n"
            "- **Primárny zámer** — čo autor chce dosiahnuť: legitimácia, príkaz, presviedčanie, "
            "varovanie, ideologické spochybnenie…\n"
            "- **Rétoricka stratégia** — ako zámer realizuje: apel na autoritu, priame oslovenie, "
            "rétoricka otázka, príbehový príklad…\n\n"
            "**Interpretácia:** Dominancia direktív a legitimácie = autoritatívny text. "
            "Prevaha asertívov s apelom na písmo = exegetický charakter. "
            "Prítomnosť ideologického spochybňovania = polemický kontext."
        ),
        "ana_verbal_detail": (
            "**Teoretické zakotvenie:** Verbálne vzťahy klasifikujú syntaktické vzorce "
            "cez kombináciu dependency vzťahov a lexikálnych markerov charakteristických "
            "pre daný komunikačný žáner.\n\n"
            "**Žánrové typy:**\n"
            "- **Reported speech** — priama reč, citácia, slovesá komunikácie\n"
            "- **Genealogical** — záznamy rodokmenu (splodiť, narodiť sa, pokolenie)\n"
            "- **Lyrical** — poetické a hymnické pasáže\n"
            "- **Prophetic** — prorocké výroky s formulou 'praví Hospodin'\n"
            "- **Request** — modlitba, prosba, žiadosť\n"
            "- **Wisdom** — múdrostné výroky (príslovie, poučenie)\n\n"
            "**Interpretácia:** Dominantný žáner odhaľuje funkciu textu v jeho literárnom "
            "a kultúrnom kontexte. Porovnanie žánrov medzi knihami ukazuje typologické rozdiely."
        ),
        "ana_semantics_detail": (
            "**Technické spracovanie:** Sémantická analýza pracuje s lematizovanými tokenmi "
            "a syntaktickými závislosťami z Stanza NLP (model cs/pdt alebo en/ewt). "
            "Každá veta dostane sémantický zhluk na základe distribúcie kľúčových lemiem.\n\n"
            "**Komponenty:**\n"
            "- **Lematizácia** — prevod slov na základný tvar\n"
            "- **POS-tagging** — slovné druhy a morfologické vlastnosti\n"
            "- **Dependency parsing** — syntaktické závislosti (podmet, predmet, prívlastok…)\n"
            "- **Sémantický zhluk** — description / request / negation / neutral / uncertainty\n\n"
            "**Interpretácia:** Vysoká frekvencia negačných konštrukcií = polemický alebo "
            "prohibitívny charakter. Dominancia description = naratívny register. "
            "Vysoký podiel request = modlitebný alebo direktívny žáner."
        ),
        "ana_religious_detail": (
            "**Metodika:** Detekcia náboženských elementov prebieha cez lexikálne porovnávanie "
            "s rozsiahlymi frozenset slovníkmi 23 tradícií a 15 filozofických vplyvov. "
            "Každý element je reprezentovaný sadou lemiem typických pre danú tradíciu.\n\n"
            "**Tradície (výber):** kresťanská česká/anglická, hebrejská, islamská, buddhistická, "
            "hinduistická, hermetická, kabalistická, súfijská, teosofická, šamanská, tantrická.\n\n"
            "**Filozofické vplyvy:** platonizmus, neoplatonizmus, gnosticizmus, stoicizmus, "
            "aristotelizmus, hermétizmus, jungiánizmus, new-age a ďalšie.\n\n"
            "**Interpretácia:** Prítomnosť tradície sa meria počtom lemiem z daného slovníka "
            "v texte. Nie je to dôkaz príslušnosti textu k tradícii — skôr ukazovateľ "
            "tematickej príbuznosti. Rôzne tradície môžu zdieľať lexikum (napr. 'duch', 'svetlo')."
        ),
        "ana_network_detail": (
            "**Metodika:** Sémantická sieť je budovaná na základe PMI "
            "(Pointwise Mutual Information) — štatistickej miery, ktorá meria, "
            "o koľko častejšie sa dve slová vyskytujú spolu v porovnaní s náhodou.\n\n"
            "**Komponenty siete:**\n"
            "- **PMI score** — sila asociácie dvoch slov; vyššie = silnejšia koexistencia\n"
            "- **Degree centrality** — počet sémantických väzieb slova\n"
            "- **Weighted centrality** — kombinácia PMI a počtu väzieb\n\n"
            "**Interpretácia:** Slová s vysokou centralitou sú sémantickým jadrom textu. "
            "Sémantické zhluky odhaľujú tematické zoskupenia pojmov. "
            "Táto analýza je výpočtovo náročná a odporúčame ju len "
            "pre celý korpus (záložka Biblický korpus)."
        ),
        "ana_patterns_detail": (
            "**Metodika:** Analýza opakujúcich sa vzorov na lexikálnej, štylistickej "
            "a sémantickej úrovni.\n\n"
            "**Komponenty:**\n"
            "- **Bigramy/trigramy** — najčastejšie slovné dvojice a trojice; "
            "odhaľujú ustálené frázy a kolokácie\n"
            "- **Sémantické opozície** — protikladné páry slov (život/smrť, svetlo/tma) "
            "detegované v kontexte ±3 viet; ukazujú rétorickú polarizáciu textu\n"
            "- **TF-IDF** — slová charakteristické pre konkrétnu knižnú jednotku oproti ostatným\n\n"
            "**Interpretácia:** Opakujúce sa n-gramy odhaľujú formulaické a rituálne vzorce. "
            "Sémantické opozície sú kľúčovým rétorickým nástrojom biblického diskurzu."
        ),
        "ana_style_detail": (
            "**Metodika:** Syntaktická analýza meria komplexnosť viet cez metriky "
            "dependency stromu. Štýlová analýza identifikuje zhluky kníh "
            "na základe TF-IDF frekvencií slov.\n\n"
            "**Metriky:**\n"
            "- **Avg tree depth** — priemerná hĺbka dependency stromu "
            "(1–2 = jednoduchá veta, 4+ = komplexná)\n"
            "- **Avg clause count** — priemerný počet vedľajších viet na vetu\n"
            "- **Silhouette score** — miera zhody knihy so svojím štýlovým zhlukm\n\n"
            "**Interpretácia:** Nízka hĺbka stromu = direktívny alebo aforistický štýl "
            "(zákon, múdrostná literatúra). Vysoká hĺbka = argumentatívny alebo "
            "naratívny štýl. Táto analýza je výpočtovo náročná."
        ),
        "ana_quality_detail": (
            "**Metodika:** Spoľahlivosť klasifikácie je hodnotená cez skóre istoty "
            "(confidence score 0.0–1.0), ktoré odráža zhodu klasifikátora "
            "s trénovanými vzormi.\n\n"
            "**Pásma istoty:**\n"
            "- **0–30 %** — veta nebola spoľahlivo klasifikovaná "
            "(krátke alebo syntakticky neštandardné vety)\n"
            "- **30–60 %** — nízka istota (nejasný rétoricý kontext, "
            "viacero možných zámerov)\n"
            "- **60–100 %** — spoľahlivá klasifikácia\n\n"
            "**Interpretácia:** Vyšší podiel viet s nízkou istotou naznačuje rétorickú "
            "komplexnosť textu alebo nedostatočné pokrytie trénovacích vzorov. "
            "Odporúčame manuálne overiť vety s confidence < 0.4."
        ),
        "ana_dashboard_detail": (
            "**Obsah dashboardu:**\n"
            "- **Source** — zdroj textu (názov súboru alebo 'pasted_text')\n"
            "- **Sentences** — počet analyzovaných viet\n"
            "- **DB rows** — celkový počet riadkov v databáze skinner_analysis\n"
            "- **Bible runs** — počet behov z biblického korpusu\n"
            "- **Upload runs** — počet behov z nahratých textov\n"
            "- **NLP model** — aktívny model Stanza (cs alebo en)\n\n"
            "**Odporúčania:** Ak počet riadkov v DB neočakávane rastie, "
            "skontrolujte duplicitné behy. Odporúčame pravidelné zálohovanie "
            "`output/bible_analysis.db`. Pre reset databázy zmažte súbor DB "
            "a spustite `k_apply_all_to_bible.py` znovu."
        ),
        "select_analyses": "Vyberte okruhy analýz",
        "run_hint": "Výsledky sa zobrazia v záložke **Výsledky**.",
        "results_empty": "Najprv spustite analýzu v záložke Analyzovať text.",
        "results_title": "Výsledky analýzy",
        "results_ready_msg": "Analýza dokončená — výsledky sú v záložke Výsledky.",
        "ana_bf_name":        "B.F. Skinner",
        "ana_bf_q":           "Aký typ verbálneho správania text reprezentuje — príkaz, pozorovanie, citácia?",
        "ana_qs_name":        "Q. Skinner",
        "ana_qs_q":           "Čo chcel autor textom dosiahnuť a akú rétorickú stratégiu použil?",
        "ana_verbal_name":    "Verbálne vzťahy",
        "ana_verbal_q":       "Aký žáner verbálnej interakcie dominuje — dialóg, nárek, chvála, múdrostný výrok?",
        "ana_semantics_name": "Sémantika a obsah",
        "ana_semantics_q":    "Aké sémantické polia a obsahové kategórie dominujú v texte?",
        "ana_religious_name": "Náboženské elementy",
        "ana_religious_q":    "Ktoré náboženské tradície, elementy a filozofické vplyvy sú v texte prítomné?",
        "ana_network_name":   "Sieť slov",
        "ana_network_q":      "Ktoré pojmy tvoria jadro sémantickej siete a ako sú navzájom prepojené?",
        "ana_patterns_name":  "Textové vzory",
        "ana_patterns_q":     "Aké lexikálne a štylistické vzory sa v texte opakujú?",
        "ana_style_name":     "Štýl a syntax",
        "ana_style_q":        "Aká je syntaktická komplexnosť textu a líši sa štýl medzi časťami?",
        "ana_quality_name":   "Kvalita výsledkov",
        "ana_quality_q":      "Ako spoľahlivá je klasifikácia a kde môže byť neistá?",
        "ana_dashboard_name": "Dashboard",
        "ana_dashboard_q":    "Aký je technický stav analýzy a ktoré moduly bežali úspešne?",
        "save_error": "Chyba pri ukladaní",
        # Section 16 — new analytics
        "complexity_title": "Syntaktická zložitosť podľa kníh",
        "complexity_desc": "Priemerná hĺbka závislostného stromu a priemerný počet vedľajších viet na vetu v každej biblickej knihe. Vyššia hodnota = syntakticky zložitejší text.",
        "tact_autoclitic_title": "Tact vs. Autoclitic podľa kníh",
        "tact_autoclitic_desc": "Podiel viet klasifikovaných ako **tact** (asertív — popis skutočnosti) vs. **autoclitic** (deklaratív — komentár k vlastnej reči) v každej biblickej knihe.",
        "traditions_title": "Tradície a filozofické vplyvy — prehľad",
        "cluster_labels": {
            "royal":       "Kráľovská moc",
            "kinship":     "Príbuzenstvo",
            "theological": "Teologické",
            "war":         "Vojna",
            "wisdom":      "Múdrosť",
            "cultic":      "Kultický",
            "divine":      "Božské",
            "moral":       "Morálne",
        },
        "traditions_desc": "Počet aktívnych lexikálnych kategórií pre každú tradíciu / počet termínov pre každý filozofický vplyv zahrnutý v analýze.",
        "x_depth": "Priemerná hĺbka stromu",
        "x_clauses": "Priemerný počet klauzúl",
        "x_terms": "Termíny",
        "x_categories": "Kategórie",
        "opposition_window_note": "Opozície detegované v kontextovom okne ±3 viet.",
        "opposition_polarity_title": "Polarita opozícií — pozitívny vs. negatívny framing",
        "opposition_polarity_desc": "Pre každý opozičný pár: koľko viet ho rámuje z **pozitívneho pólu** (svetlo, život, dobro…) vs. z **negatívneho pólu** (tma, smrť, zlo…). Neutrálne = oba póly prítomné v kotevnej vete súčasne.",
        "opposition_directed_title": "Orientovaná sieť opozícií — top hrany",
        "opposition_directed_desc": "Každá hrana ide od **dominantného pólu** (prítomného v kotevnej vete) k **podriadeného pólu** (prítomného v okne). Váha = počet doložených výskytov tohto smeru.",
        "opposition_examples_title": "Príklady viet s opozíciou",
        "opposition_examples_desc": "Ukážkové vety, v ktorých bezprostrednom kontexte (±3 vety) bol detegovaný opozičný pár.",
        "lbl_positive": "Pozitívny pól",
        "lbl_negative": "Negatívny pól",
        "lbl_both": "Oba póly",
        "col_source": "Zdroj",
        "col_target": "Cieľ",
        "col_weight": "Váha",
        "filter_pair": "Filtrovať pár",
        # Context parameter panel
        "ctx_expander":          "⚙️ Kontext analýzy (voliteľné)",
        "ctx_source_label":      "Zdroj textu",
        "ctx_interaction_label": "Typ interakcie",
        "ctx_stimulus_label":    "Riadiaci stimul",
        "ctx_source_opts": {
            "unknown":           "— neznámy",
            "written_record":    "Písaný dokument",
            "uploaded_document": "Nahraný dokument",
            "spoken_record":     "Hovorený záznam",
            "transcript":        "Prepis",
        },
        "ctx_interaction_opts": {
            "unknown":   "— neznámy",
            "monologue": "Monológ",
            "dialogue":  "Dialóg",
        },
        "ctx_stimulus_opts": {
            "unknown":                 "— neznámy",
            "nonverbal_object":        "Neverbálny objekt/udalosť",
            "written_verbal_stimulus": "Písaný text",
            "auditory_verbal_stimulus":"Počutá reč",
            "question_prompt":         "Otázka ako stimul",
            "answer_context":          "Výrok je odpoveď",
            "private_event":           "Vnútorný stav",
            "none":                    "Žiadny",
        },
        "ctx_warn_qa_mono":      "Nekonzistentný kontext: stimul Q&A (otázka/odpoveď) predpokladá dialóg, ale interakcia je nastavená ako monológ.",
        "ctx_warn_audio_written":"Nekonzistentný kontext: písaný/nahraný zdroj nemôže byť riadený sluchovým verbálnym stimulom — to predpokladá hovorenú interakciu.",
        "ctx_warn_written_spoken":"Nekonzistentný kontext: hovorený záznam nemôže byť riadený písaným stimulom.",
        "ctx_warn_dialogue_none":"Nekonzistentný kontext: dialóg vyžaduje verbálny stimul — stimul 'žiadny' dialóg vylučuje.",
        # Tab 4
        "tab_compare": "🔄 Porovnanie",
        "compare_title": "Porovnanie analýz",
        "compare_placeholder": (
            "Táto záložka bude obsahovať nástroje na porovnanie výsledkov analýzy "
            "nahratého textu s biblickým korpusom (BKR). "
            "Funkcia je pripravená na implementáciu vo fáze 2."
        ),
        # Segmentation preview (Tab 1)
        "seg_preview_title": "Náhľad segmentácie",
        "seg_method_chapter": "kapitoly (štrukturálne nadpisy)",
        "seg_method_section": "sekcie (podnadpisy)",
        "seg_method_single": "jeden dokument (bez štruktúry)",
        "seg_preview_unit": "jednotka",
        "seg_preview_units": "jednotky",
    },

    "en": {
        "app_title": "📖 Skinner Pipeline",
        "app_subtitle": "Czech biblical text analysis — speech act · intention · rhetorical strategy",
        "tab_analyze": "📝 Analyze Text",
        "tab_bible": "📚 Bible Corpus",
        "export_pdf": "📄  Export Report as PDF",
        "pdf_generating": "Generating PDF…",
        "pdf_ready": "Report ready for download.",
        "pdf_error": "PDF generation error",
        "pdf_filename": "skinner_report.pdf",
        "lang_label": "Language",
        "upload_header": "Upload or paste text",
        "upload_label": "Upload .txt or .pdf",
        "paste_label": "…or paste text here",
        "run_button": "▶  Run Pipeline",
        "reading_file": "Reading file…",
        "running_pipeline": "Running Skinner pipeline…",
        "no_text_warning": "Please upload a file or paste text first.",
        "metric_sentences": "Sentences",
        "metric_classified": "Classified",
        "metric_confidence": "Mean confidence",
        "metric_intentions": "Distinct intentions",
        "intent_pie_title": "Intentions",
        "intent_pie_desc": "Speaker intentions in the analysed text — dominant intentions reveal the rhetorical-communicative profile.",
        "strategy_bar_title": "Rhetorical Strategies",
        "strategy_bar_desc": "Most frequent rhetorical techniques used to pursue communicative goals.",
        "force_pie_title": "Speech Act Type",
        "force_pie_desc": "Basic speech act type: directives · assertives · commissives · expressives · declaratives.",
        "conf_hist_title": "Classification Confidence by Intention",
        "conf_hist_desc": "Classification reliability per intention — low confidence signals rhetorical ambiguity.",
        "conf_table_desc": "Mean confidence per intention.",
        "secondary_intent_title": "Secondary Intentions",
        "secondary_intent_desc": "Sentences with a dual intent — the secondary intention reveals argumentative subtext.",
        "section_sentence_table": "Sentence-level results",
        "filter_intention": "Filter intention",
        "filter_strategy": "Filter strategy",
        "download_csv": "⬇  Download full CSV",
        "col_id": "#",
        "col_sentence": "Sentence",
        "col_intention": "Intention",
        "col_2nd_intention": "2nd intention",
        "col_force": "Speech act",
        "col_strategy": "Strategy",
        "col_confidence": "Confidence",
        "col_reason": "Reason",
        "col_locution": "Locution",
        "col_convention": "Convention",
        "col_pol_vocab": "Pol. vocab",
        "bible_header": "Bible Corpus Analytics",
        "bible_caption": "Pre-computed from Czech Bible (Kralická, BKR) — run `k_apply_all_to_bible.py` to refresh.",
        "metric_total": "Total sentences",
        "metric_books": "Bible books",
        "metric_coverage": "Classified",
        "metric_mean_conf": "Mean confidence",
        "no_db": "Database `output/bible_analysis.db` not found. Run the pipeline first.",
        "sec_intention": "📊 Intention Analysis",
        "all_intentions_title": "Intentions — all books",
        "all_intentions_desc": "Intention distribution across the full corpus — dominant intentions characterise the rhetorical field of the text.",
        "force_all_title": "Speech Act Types",
        "force_all_desc": "Speech act type distribution across the full corpus.",
        "intent_book_heatmap_title": "Intentions by Book",
        "intent_book_heatmap_desc": "Rhetorical profiles of individual books — darker = intention dominates in that book.",
        "sec_strategy": "🎯 Strategy Analysis",
        "all_strategies_title": "Rhetorical Strategies — all books",
        "all_strategies_desc": "Rhetorical techniques across the corpus — comparison reveals argumentative strategies.",
        "pvoc_title": "Top Political Vocabulary",
        "pvoc_desc": "Words linked to power, authority and law — indicator of political discourse.",
        "strat_book_heatmap_title": "Strategies by Book",
        "strat_book_heatmap_desc": "Rhetorical profiles by book — darker = strategy dominates in that book.",
        "sec_ratios": "⚖️ Key Ratios by Book",
        "directive_assertive_title": "Directive vs. Assertive",
        "directive_assertive_desc": "Directives (red) vs. assertives (blue) per book — key indicator of text authority and genre.",
        "legit_ratio_title": "Legitimation · Contestation · Intervention",
        "legit_ratio_desc": "Skinner's analytical categories of power discourse: reinforcing authority, challenging opponents, calling to action.",
        "no_ratios": "Run `l_taxonomy_analytics.py` to compute ratios.",
        "sec_religious": "✝️ Religious Elements",
        "element_coverage_title": "Religious Element Coverage",
        "element_coverage_desc": "Sentences containing given religious elements — shows the thematic focus of the corpus.",
        "philosophy_title": "Philosophical Traditions",
        "philosophy_desc": "Presence of philosophical and theological traditions in the text.",
        "rel_elements": {
            "covenant_law":      "Covenant & Law",
            "prophetic_speech":  "Prophetic Speech",
            "divine_hierarchy":  "Divine Hierarchy",
            "legal":             "Legal Elements",
            "life_death":        "Life & Death",
            "wisdom":            "Wisdom",
            "ritual_sacrifice":  "Ritual Sacrifice",
            "moral":             "Moral Elements",
            "war_conflict":      "War & Conflict",
            "eschatology":       "Eschatology",
            "royal_power":       "Royal Power",
            "monotheism":        "Monotheism",
            "genealogy_lineage": "Genealogy",
            "divine":            "Divine Elements",
            "kinship":           "Kinship",
        },
        "rel_philosophy": {
            "platonic":      "Platonism",
            "neoplatonic":   "Neoplatonism",
            "stoic":         "Stoicism",
            "gnostic":       "Gnosticism",
            "aristotelian":  "Aristotelianism",
            "pythagorean":   "Pythagoreanism",
            "epicurean":     "Epicureanism",
            "hermetic":      "Hermeticism",
            "sufi":          "Sufism",
            "kabbalistic":   "Kabbalah",
            "theosophical":  "Theosophy",
            "jungian":       "Jungianism",
            "new_age":       "New Age",
            "shamanic":      "Shamanism",
            "tantric":       "Tantrism",
        },
        "density_heatmap_title": "Religious Element Density by Book",
        "density_heatmap_desc": "Proportion of sentences with given religious elements per book (0–1) — darker = element dominates in that book.",
        "sec_clusters": "🔗 Concept Clusters & Semantic Oppositions",
        "cluster_bubble_title": "Concept Clusters",
        "cluster_bubble_desc": "Semantic word clusters — larger bubble = more connected pairs, rightward = stronger co-occurrence.",
        "opposition_title": "Top Semantic Oppositions",
        "opposition_desc": "Most frequently attested oppositional word pairs within ±3-sentence context.",
        "sec_centrality": "🌐 Semantic Centrality",
        "top_n_slider": "Number of words",
        "centrality_bar_title": "Most Semantically Central Words",
        "centrality_bar_desc": "Semantically most important words — the hub nodes of the text's meaning network.",
        "no_centrality": "Run `r_word_network.py` and `s_word_relations_analytics.py`.",
        "sec_style": "✍️ Style & Authorship Clusters",
        "style_table_desc": "Style clusters of biblical books — books in one cluster share similar vocabulary and rhetorical profile.",
        "cluster_terms_title": "Top Cluster Terms",
        "cluster_terms_desc": "Words most characteristic of the selected style cluster — distinguish it from others.",
        "select_cluster": "Cluster",
        "no_style": "Run `x_style_authorship.py`.",
        "sec_dependency": "🏗️ Dependency Structure",
        "dep_bar_title": "Top Dependency Relations",
        "dep_bar_desc": "Syntactic dependency types in the corpus — basis for sentence complexity and style analysis.",
        "dep_heatmap_title": "Dependency Distribution by Book",
        "dep_heatmap_desc": "Syntactic dependencies per book — darker = relation type dominates in that book.",
        "sec_verbal": "💬 Verbal Relations",
        "verbal_types_title": "Verbal Relation Types",
        "verbal_types_desc": "Verbal relation types — reported speech, prophecy, genealogy, prayer, description, etc.",
        "verbal_conf_title": "Classification Confidence by Relation Type",
        "verbal_conf_desc": "Classification reliability per verbal relation type.",
        "verbal_book_heatmap_title": "Verbal Relations by Book",
        "verbal_book_heatmap_desc": "Verbal relations per book — darker = type dominates in that book.",
        "sec_taxonomy": "🏷️ Skinner Behavioural Taxonomy",
        "tax_class_title": "Skinner Functional Classes",
        "tax_class_desc": "Sentence classification according to **Skinner's behavioural taxonomy** of language: `tact` = description/naming of the world · `mand` = command or request · `echoic` = quotation or repetition · `intraverbal` = response to a verbal stimulus · `autoclitic` = commentary on one's own speech. `none` = unassigned.",
        "tax_dialogue_title": "Dialogue Density by Book",
        "tax_dialogue_desc": "**Proportion of sentences that are part of a dialogue** (direct speech) in each biblical book. Higher = book contains more dialogues and direct speech.",
        "tax_control_title": "Control Role",
        "tax_control_desc": "Classification of sentences in terms of the **control relationship** between speaker and listener: `stimulus` = speaker controls listener, `response` = speaker reacts to a stimulus, `record` = neutral record with no clear control.",
        "sec_word_rel": "🔤 Semantic Word Associations",
        "top_pmi_title": "Strongest Semantic Associations",
        "top_pmi_desc": "Word pairs with the **highest PMI score** (Pointwise Mutual Information) — a measure of how strongly two words attract each other in the text. High PMI = these two words co-occur far more often than chance would predict.",
        "top_pmi_word1": "Word 1",
        "top_pmi_word2": "Word 2",
        "top_pmi_count": "Occurrences",
        "top_pmi_pmi": "PMI score",
        "most_connected_title": "Most Connected Words",
        "most_connected_desc": "Words with the **highest number of semantic connections** — words that strongly associate with the largest number of other words. These are the semantic hubs of the text.",
        "no_word_rel": "Run `s_word_relations_analytics.py`.",
        "sec_corpus_density": "📐 Thematic Category Density",
        "corpus_density_title": "Category Density by Book (sentences)",
        "corpus_density_desc": "Proportion of sentences in each book containing elements of a given **thematic category** (covenant/law, divine, eschatology, genealogy, kinship, morality, prophecy, ritual, and more — 16 categories total). A value of 0.30 means 30 % of sentences in that book belong to that category.",
        "x_intention": "Intention",
        "x_force": "Speech act",
        "x_strategy": "Strategy",
        "x_count": "Count",
        "x_score": "Score",
        "x_book": "Book",
        "x_word": "Word",
        "x_confidence": "Confidence",
        "x_avg_pmi": "Avg PMI",
        "x_edges": "Edges",
        "x_ratio": "Ratio",
        "x_element": "Element",
        "x_relation": "Relation type",
        "x_class": "Class",
        "x_density": "Density",
        "x_tfidf": "TF-IDF",
        "x_pmi": "PMI",
        "x_connections": "Connections",
        "x_weighted": "Weighted score",
        # Section 13
        "sec_patterns": "🔠 Text Patterns",
        "wordcloud_title": "Word Cloud — most frequent words in the corpus",
        "wordcloud_desc": "The word cloud shows the **most frequently occurring words** in the full biblical corpus. Larger word = more frequent in the text. Words are shown in their lemmatised (base) form.",
        "bigrams_title": "Top Word Pairs (Bigrams)",
        "bigrams_desc": "Shows the **most frequently recurring pairs of adjacent words** (bigrams) in the text. Helps reveal fixed phrases and recurring collocations.",
        "trigrams_title": "Top Word Triples (Trigrams)",
        "trigrams_desc": "Same as bigrams, but for **three adjacent words** (trigrams). Captures longer recurring phrases and formulaic expressions.",
        "tfidf_heatmap_title": "Keywords by Book — TF-IDF",
        "tfidf_heatmap_desc": "Each cell shows the **importance of a word for a given book** (TF-IDF score). Darker cell = the word is more characteristic of that book compared to others. Useful for identifying vocabulary that is specific to individual biblical books.",
        "x_frequency": "Frequency",
        "x_ngram": "Word combination",
        # Section 14
        "sec_semantics": "🔬 Semantic Analysis",
        "radar_title": "Sentence Semantic Types by Book",
        "radar_desc": "The radar chart shows the **proportion of different semantic sentence types** in each biblical book. Each axis corresponds to one type: description, neutral statement, request, negation/contrast. The further from the centre, the higher the proportion of sentences of that type.",
        "antithetical_title": "Sentences with Antithetical Structure",
        "antithetical_desc": "Shows sentences in which the algorithm detected an **oppositional or negation pattern** — sentences where something is rejected, negated, or placed in contrast. Examples: 'Thou shalt not steal', 'I am not... but...'",
        "antithetical_count_title": "Antithetical Sentence Count by Book",
        "antithetical_count_desc": "How many sentences with an antithetical pattern each biblical book contains.",
        "lexical_reinf_title": "Lexical Repetition Rate by Book",
        "lexical_reinf_desc": "**Lexical repetition** measures how often the same words recur within a single sentence. Higher value = sentences in that book contain more repeated words (typical of poetic or ritual texts). Value 0 = every word appears only once per sentence.",
        "x_reinforcement": "Repetition rate",
        "filter_book_label": "Filter book",
        "filter_group_label": "Book group",
        "group_all": "— Whole Bible",
        "group_pentateuch":     "Pentateuch",
        "group_historical":     "Historical Books",
        "group_wisdom":         "Wisdom Books",
        "group_major_prophets": "Major Prophets",
        "group_minor_prophets": "Minor Prophets",
        "group_gospels_acts":   "Gospels & Acts",
        "group_pauline":        "Pauline Epistles",
        "group_general":        "General Epistles",
        "group_apocalypse":     "Apocalypse",
        "no_patterns": "Data not available.",
        "no_group_data": "No data is available for the selected group.",
        # Section 15
        "sec_quality": "✅ Pipeline Quality",
        "quality_overall_desc": "Overview of the **quality of the automatic classification** of the full corpus: how many sentences were classified, how confident the algorithm was, and which books or classes were classified less reliably.",
        "coverage_book_title": "Classification Coverage by Book",
        "coverage_book_desc": "Percentage of **successfully classified sentences** in each biblical book. Values below 95 % indicate the algorithm had more difficulty with that book.",
        "conf_bins_title": "Confidence Distribution by Band",
        "conf_bins_desc": "Sentences divided into three confidence bands: **0–30 %** = could not be classified, **30–60 %** = low confidence, **60–100 %** = reliable classification. Ideally the 60–100 % band should cover the vast majority of sentences.",
        "consistency_title": "Lemma Classification Consistency",
        "consistency_desc": "Each lemma (base word form) should consistently be classified into the same intention class. Shows **lemmas classified into multiple different classes** — these are ambiguous for the algorithm.",
        "outliers_title": "Books with Abnormal Class Ratios",
        "outliers_desc": "Books where the proportion of a given intention class is **significantly higher or lower** than the corpus average (statistical deviation |z| > 2). Flags books with an unusual rhetorical-textual structure.",
        "sample_title": "20 Sample Sentences — Manual Review",
        "sample_desc": "A random selection of 20 classified sentences for **manual verification** of classification correctness. We recommend paying special attention to sentences with lower confidence.",
        "x_coverage": "Coverage (%)",
        "no_eval": "Run `v_eval_pipeline.py` to compute quality metrics.",
        "col_total": "Total",
        "col_classified_q": "Classif.",
        "col_coverage_q": "Coverage (%)",
        "col_z_score": "Z-score",
        "col_label_q": "Class",
        "conf_band_low": "Low (0–30 %)",
        "conf_band_mid": "Medium (30–60 %)",
        "conf_band_high": "High (60–100 %)",
        "x_sentences": "Sentence count",
        "ambiguous_lemma_title": "Ambiguous Lemmas",
        "col_lemma": "Lemma",
        "col_classes": "Classes",
        "col_n_classes": "Class count",
        "lbl_directive": "Directive",
        "lbl_assertive": "Assertive",
        "lbl_legitimation": "Legitimation",
        "lbl_contestation": "Contestation",
        "lbl_intervention": "Intervention",
        "col_style_cluster": "Style cluster",
        "col_silhouette": "Silhouette",
        # Section 16 — Linguistic features
        "sec_ling_features": "🔡 Linguistic Features",
        "ling_ttr_desc": "**Lexical diversity** (type-token ratio) — ratio of unique lemmas to total lemmas. Lower = more formulaic or ritual text.",
        "ling_ttr_title": "Average Lexical Diversity (TTR) by Book",
        "ling_bool_desc": "Percentage of sentences with coordination, dative, and indirect object. Signals syntactic complexity and argumentative structure.",
        "ling_bool_title": "Syntactic Features (% of sentences) by Book",
        "ling_pos_desc": "Average count of adjectives, adverbs, and pronouns per sentence. Signals descriptive richness and direct address.",
        "ling_pos_title": "Morphological Features (mean per sentence) by Book",
        "ling_formulaic_desc": "Top 15 sentences with the lowest lexical diversity (min. 5 words) — likely formulaic or ritual utterances.",
        "ling_formulaic_title": "Most Formulaic Sentences (lowest TTR)",
        "col_ttr": "TTR",
        "lbl_coordination": "Coordination",
        "lbl_dative": "Dative",
        "lbl_iobj": "Indirect object",
        "lbl_adj": "Adjectives",
        "lbl_adv": "Adverbs",
        "lbl_pron": "Pronouns",
        # Save to DB
        "save_button": "💾  Save to database",
        "save_caption": "Saves analysis results to `bible_analysis.db` as a separate run — isolated from the biblical corpus.",
        "save_success": "Saved",
        "save_run_id_label": "run_id",
        "save_rows_label": "sentences saved",
        "save_already": "Already saved",
        "save_error": "Save error",
        # Tab 3 + checkboxes
        "tab_results": "📋 Results",
        "about_title": "ℹ️ About the Analyses",
        "about_text": (
            "Overview of 10 analysis modules:\n\n"
            "1. **B.F. Skinner** — Classifies sentences by behavioural taxonomy of language: "
            "mand (command), tact (world description), echoic (quotation), intraverbal (response to speech), "
            "autoclitic (self-commentary). Based on Verbal Behavior (Skinner, 1957).\n\n"
            "2. **Q. Skinner** — Identifies the illocutionary intent of each sentence (what the speaker aims to do) "
            "and the rhetorical strategy (how they achieve it). Based on speech act theory "
            "(Austin, Searle, Q. Skinner 1969–2002).\n\n"
            "3. **Verbal Relations** — Classifies the verbal interaction genre: reported speech, "
            "genealogy, lyric, prophecy, prayer, wisdom saying.\n\n"
            "4. **Semantics & Content** — Processes text via Stanza NLP (lemmatisation, POS, dependency) "
            "and extracts semantic clusters and content categories.\n\n"
            "5. **Religious Elements** — Detects the presence of 23 religious traditions "
            "and 15 philosophical influences using specialised lexical dictionaries.\n\n"
            "6. **Word Network** — Builds a semantic network based on PMI (word association strength); "
            "identifies central concepts and thematic clusters.\n\n"
            "7. **Text Patterns** — Analyses n-grams, semantic oppositions (±3 sentences) "
            "and formulaic expressions; reveals recurring structures and rhetorical polarisation.\n\n"
            "8. **Style & Syntax** — Measures syntactic complexity via dependency tree depth "
            "and clause count; identifies style clusters across books.\n\n"
            "9. **Result Quality** — Evaluates classification reliability via the confidence score "
            "distribution and flags sentences with low certainty.\n\n"
            "10. **Dashboard** — Technical overview: database state, NLP model, text source, "
            "run count and history.\n\n"
            "*For a detailed description of each module see **Detailed Module Descriptions** below the Run button.*"
        ),
        "detail_expander_title": "📖 Detailed Module Descriptions",
        "ana_bf_detail": (
            "**Theoretical grounding:** B. F. Skinner in *Verbal Behavior* (1957) redefined language "
            "as behaviour controlled by stimuli and reinforcement — not a sign system, but a function.\n\n"
            "**Types of verbal behaviour:**\n"
            "- **Mand** — utterance controlled by a speaker's need (command, request)\n"
            "- **Tact** — utterance controlled by a non-verbal stimulus (description, naming)\n"
            "- **Echoic** — utterance reproducing another person's verbal stimulus (quotation, repetition)\n"
            "- **Intraverbal** — utterance controlled by prior speech (response, reaction)\n"
            "- **Autoclitic** — utterance modifying another utterance (qualification, emphasis)\n\n"
            "**Interpretation:** High proportion of mands = directive text (law, ritual). "
            "Dominant tacts = descriptive or narrative text. "
            "Echoic formulas are typical of liturgical and ritual texts."
        ),
        "ana_qs_detail": (
            "**Theoretical grounding:** Quentin Skinner (1969–2002) developed a methodology "
            "of intellectual history in which the key concept is illocutionary intent — "
            "what the author aims to *do* with a text in a specific historical context. "
            "Draws on J. L. Austin's and J. R. Searle's speech act theory.\n\n"
            "**Key categories:**\n"
            "- **Illocutionary force** — basic speech act type: directive, assertive, commissive, "
            "expressive, declarative\n"
            "- **Primary intention** — what the author seeks to achieve: legitimation, command, "
            "persuasion, warning, ideological contestation…\n"
            "- **Rhetorical strategy** — how the intent is realised: appeal to authority, "
            "direct address, rhetorical question, narrative example…\n\n"
            "**Interpretation:** Dominant directives + legitimation = authoritative text. "
            "Assertives with scripture appeal = exegetical character. "
            "Ideological contestation = polemical context."
        ),
        "ana_verbal_detail": (
            "**Theoretical grounding:** Verbal relations classify syntactic patterns "
            "using combinations of dependency relations and lexical markers "
            "characteristic of each communicative genre.\n\n"
            "**Genre types:**\n"
            "- **Reported speech** — direct speech, quotation, speech verbs\n"
            "- **Genealogical** — lineage records (beget, be born, generation)\n"
            "- **Lyrical** — poetic and hymnic passages\n"
            "- **Prophetic** — oracular utterances with 'thus saith the Lord' formula\n"
            "- **Request** — prayer, petition, supplication\n"
            "- **Wisdom** — aphoristic sayings (proverb, instruction)\n\n"
            "**Interpretation:** The dominant genre reveals the function of the text "
            "in its literary and cultural context. Genre comparison across books "
            "shows typological differences within the biblical canon."
        ),
        "ana_semantics_detail": (
            "**Technical processing:** Semantic analysis works with lemmatised tokens "
            "and syntactic dependencies from Stanza NLP (cs/pdt or en/ewt model). "
            "Each sentence is assigned a semantic cluster based on its key lemma distribution.\n\n"
            "**Components:**\n"
            "- **Lemmatisation** — reduction of words to base form\n"
            "- **POS-tagging** — part of speech and morphological features\n"
            "- **Dependency parsing** — syntactic relations (subject, object, modifier…)\n"
            "- **Semantic cluster** — description / request / negation / neutral / uncertainty\n\n"
            "**Interpretation:** High negation frequency = polemical or prohibitive character. "
            "Dominant description = narrative register. "
            "High proportion of requests = prayer or directive genre."
        ),
        "ana_religious_detail": (
            "**Methodology:** Religious element detection uses lexical matching against "
            "frozenset dictionaries for 23 traditions and 15 philosophical influences. "
            "Each element is represented by a set of lemmas typical for that tradition.\n\n"
            "**Traditions (selection):** Christian Czech/English, Hebrew, Islamic, Buddhist, "
            "Hindu, Hermetic, Kabbalistic, Sufi, Theosophical, Shamanic, Tantric.\n\n"
            "**Philosophical influences:** Platonism, Neoplatonism, Gnosticism, Stoicism, "
            "Aristotelianism, Hermeticism, Jungianism, New Age and others.\n\n"
            "**Interpretation:** A tradition's presence is measured by the number of matching "
            "lemmas in the text — not proof of the text belonging to that tradition, "
            "but an indicator of thematic affinity. Different traditions may share lexis "
            "(e.g. 'spirit', 'light', 'wisdom')."
        ),
        "ana_network_detail": (
            "**Methodology:** The semantic network is built using PMI "
            "(Pointwise Mutual Information) — a statistical measure of how much more "
            "often two words co-occur compared to chance.\n\n"
            "**Network components:**\n"
            "- **PMI score** — association strength between two words; higher = stronger co-occurrence\n"
            "- **Degree centrality** — number of semantic connections a word has\n"
            "- **Weighted centrality** — combination of PMI and connection count\n\n"
            "**Interpretation:** High-centrality words are the semantic core of the text. "
            "Semantic clusters reveal thematic groupings of concepts. "
            "This analysis is computationally intensive and is best run on the full corpus "
            "(Bible Corpus tab) rather than short uploaded texts."
        ),
        "ana_patterns_detail": (
            "**Methodology:** Analysis of recurring patterns at the lexical, stylistic "
            "and semantic levels.\n\n"
            "**Components:**\n"
            "- **Bigrams / trigrams** — most frequent word pairs and triples; "
            "reveal fixed phrases and collocations\n"
            "- **Semantic oppositions** — contrastive word pairs (life/death, light/darkness) "
            "detected within a ±3-sentence window; show rhetorical polarisation\n"
            "- **TF-IDF** — words characteristic of a specific book unit compared to others\n\n"
            "**Interpretation:** Recurring n-grams reveal formulaic and ritual patterns. "
            "Semantic oppositions are a central rhetorical device of biblical discourse "
            "and can signal thematic tensions within the text."
        ),
        "ana_style_detail": (
            "**Methodology:** Syntactic analysis measures sentence complexity via "
            "dependency tree metrics. Style analysis identifies book clusters "
            "based on TF-IDF word frequencies.\n\n"
            "**Metrics:**\n"
            "- **Avg tree depth** — average dependency tree depth "
            "(1–2 = simple sentence, 4+ = complex)\n"
            "- **Avg clause count** — average number of subordinate clauses per sentence\n"
            "- **Silhouette score** — how well a book fits its style cluster (−1 to 1)\n\n"
            "**Interpretation:** Low tree depth = directive or aphoristic style "
            "(law, wisdom literature). High depth = argumentative or narrative style. "
            "This analysis is computationally intensive and may take 5–15 minutes."
        ),
        "ana_quality_detail": (
            "**Methodology:** Classification reliability is evaluated via the confidence "
            "score (0.0–1.0), which reflects how closely the classifier's output "
            "matches trained patterns.\n\n"
            "**Confidence bands:**\n"
            "- **0–30 %** — sentence could not be reliably classified "
            "(very short or syntactically non-standard)\n"
            "- **30–60 %** — low confidence (ambiguous rhetorical context, "
            "multiple plausible intentions)\n"
            "- **60–100 %** — reliable classification\n\n"
            "**Interpretation:** A higher proportion of low-confidence sentences "
            "indicates rhetorical complexity or gaps in the training patterns. "
            "We recommend manually reviewing sentences with confidence < 0.4."
        ),
        "ana_dashboard_detail": (
            "**Dashboard contents:**\n"
            "- **Source** — text source (filename or 'pasted_text')\n"
            "- **Sentences** — number of analysed sentences\n"
            "- **DB rows** — total row count in the skinner_analysis table\n"
            "- **Bible runs** — number of runs from the biblical corpus\n"
            "- **Upload runs** — number of runs from uploaded texts\n"
            "- **NLP model** — active Stanza model (cs or en)\n\n"
            "**Recommendations:** If the DB row count grows unexpectedly, "
            "check for duplicate runs. We recommend regular backups of "
            "`output/bible_analysis.db`. To reset the database, delete the DB file "
            "and re-run `k_apply_all_to_bible.py`."
        ),
        "select_analyses": "Select analysis modules",
        "run_hint": "Results will appear in the **Results** tab.",
        "results_empty": "Run an analysis in the Analyze Text tab first.",
        "results_title": "Analysis Results",
        "results_ready_msg": "Analysis complete — results are in the Results tab.",
        "ana_bf_name":        "B.F. Skinner",
        "ana_bf_q":           "What type of verbal behaviour does the text represent — command, observation, quotation?",
        "ana_qs_name":        "Q. Skinner",
        "ana_qs_q":           "What did the author intend with the text and what rhetorical strategy did they use?",
        "ana_verbal_name":    "Verbal Relations",
        "ana_verbal_q":       "What verbal interaction genre dominates — dialogue, lament, praise, wisdom saying?",
        "ana_semantics_name": "Semantics & Content",
        "ana_semantics_q":    "What semantic fields and content categories dominate in the text?",
        "ana_religious_name": "Religious Elements",
        "ana_religious_q":    "Which religious traditions, elements and philosophical influences are present?",
        "ana_network_name":   "Word Network",
        "ana_network_q":      "Which concepts form the core of the semantic network and how are they connected?",
        "ana_patterns_name":  "Text Patterns",
        "ana_patterns_q":     "What lexical and stylistic patterns recur in the text?",
        "ana_style_name":     "Style & Syntax",
        "ana_style_q":        "What is the syntactic complexity of the text and does style vary across sections?",
        "ana_quality_name":   "Result Quality",
        "ana_quality_q":      "How reliable is the classification and where might it be uncertain?",
        "ana_dashboard_name": "Dashboard",
        "ana_dashboard_q":    "What is the technical state of the analysis and which modules ran successfully?",
        # Section 16 — new analytics
        "complexity_title": "Syntactic Complexity by Book",
        "complexity_desc": "Average dependency tree depth and average clause count per sentence in each biblical book. Higher = syntactically more complex text.",
        "tact_autoclitic_title": "Tact vs. Autoclitic by Book",
        "tact_autoclitic_desc": "Proportion of sentences classified as **tact** (assertive — world description) vs. **autoclitic** (declarative — commentary on own speech) per biblical book.",
        "traditions_title": "Traditions & Philosophical Influences — Overview",
        "traditions_desc": "Number of active lexical categories per tradition / number of terms per philosophical influence included in the analysis.",
        "x_depth": "Avg tree depth",
        "x_clauses": "Avg clause count",
        "x_terms": "Terms",
        "x_categories": "Categories",
        "opposition_window_note": "Oppositions detected in a ±3-sentence context window.",
        "opposition_polarity_title": "Opposition Polarity — positive vs. negative framing",
        "opposition_polarity_desc": "For each opposition pair: how many sentences frame it from the **positive pole** (light, life, good…) vs. the **negative pole** (darkness, death, evil…). Neutral = both poles present in the anchor sentence simultaneously.",
        "opposition_directed_title": "Directed Opposition Network — top edges",
        "opposition_directed_desc": "Each edge goes from the **dominant pole** (present in the anchor sentence) to the **subordinate pole** (present in the window). Weight = number of attested occurrences of this direction.",
        "opposition_examples_title": "Example Sentences with Opposition",
        "opposition_examples_desc": "Sample sentences in whose immediate context (±3 sentences) an opposition pair was detected.",
        "lbl_positive": "Positive pole",
        "lbl_negative": "Negative pole",
        "lbl_both": "Both poles",
        "col_source": "Source",
        "col_target": "Target",
        "col_weight": "Weight",
        "filter_pair": "Filter pair",
        # Context parameter panel
        "ctx_expander":          "⚙️ Analysis Context (optional)",
        "ctx_source_label":      "Text source",
        "ctx_interaction_label": "Interaction type",
        "ctx_stimulus_label":    "Controlling stimulus",
        "ctx_source_opts": {
            "unknown":           "— unknown",
            "written_record":    "Written document",
            "uploaded_document": "Uploaded document",
            "spoken_record":     "Spoken recording",
            "transcript":        "Transcript",
        },
        "ctx_interaction_opts": {
            "unknown":   "— unknown",
            "monologue": "Monologue",
            "dialogue":  "Dialogue",
        },
        "ctx_stimulus_opts": {
            "unknown":                 "— unknown",
            "nonverbal_object":        "Non-verbal object / event",
            "written_verbal_stimulus": "Written text",
            "auditory_verbal_stimulus":"Heard speech",
            "question_prompt":         "Question as stimulus",
            "answer_context":          "Utterance is a response",
            "private_event":           "Internal state",
            "none":                    "None",
        },
        "ctx_warn_qa_mono":      "Inconsistent context: Q&A stimulus (question/answer) implies a dialogue partner, but interaction is set to monologue.",
        "ctx_warn_audio_written":"Inconsistent context: a written/uploaded source cannot be controlled by an auditory verbal stimulus — that presupposes spoken interaction.",
        "ctx_warn_written_spoken":"Inconsistent context: a spoken recording cannot be controlled by a written verbal stimulus.",
        "ctx_warn_dialogue_none":"Inconsistent context: dialogue requires a verbal stimulus — stimulus 'none' rules out dialogue.",
        # Tab 4
        "tab_compare": "🔄 Comparison",
        "compare_title": "Compare Analyses",
        "compare_placeholder": (
            "This tab will contain tools for comparing uploaded-text analysis results "
            "with the Bible corpus (BKR). "
            "Feature is ready for implementation in Phase 2."
        ),
        # Segmentation preview (Tab 1)
        "seg_preview_title": "Segmentation preview",
        "seg_method_chapter": "chapters (structural headings)",
        "seg_method_section": "sections (subheadings)",
        "seg_method_single": "single document (no structure)",
        "seg_preview_unit": "unit",
        "seg_preview_units": "units",
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# VALUE LABEL MAPS  (raw DB value → translated display label)
# ──────────────────────────────────────────────────────────────────────────────

VALUE_LABELS = {
    "force": {
        "cs": {
            "directive": "Direktiva", "assertive": "Asertiv",
            "commissive": "Komisiv", "expressive": "Expresiv",
            "declarative": "Deklarativ", "declarative_assertion": "Deklarativ",
            "unknown": "Neznámé",
        },
        "sk": {
            "directive": "Direktíva", "assertive": "Asertív",
            "commissive": "Komisív", "expressive": "Expresív",
            "declarative": "Deklaratív", "declarative_assertion": "Deklaratív",
            "unknown": "Neznáme",
        },
        "en": {
            "directive": "Directive", "assertive": "Assertive",
            "commissive": "Commissive", "expressive": "Expressive",
            "declarative": "Declarative", "declarative_assertion": "Declarative assertion",
            "unknown": "Unknown",
        },
    },
    "intention": {
        "cs": {
            "commanding": "Příkaz", "warning": "Varování",
            "mobilizing": "Mobilizace", "condemning": "Odsouzení",
            "promising": "Slib", "praising": "Chvála",
            "declaring": "Prohlášení", "justifying": "Obhajoba",
            "questioning": "Otázka", "persuading": "Přesvědčování",
            "record": "Záznam", "narrative": "Vyprávění",
            "legitimation": "Legitimace",
            "ideological_contestation": "Zpochybnění",
            "intervention": "Intervence", "unclassified": "Neklasif.",
        },
        "sk": {
            "commanding": "Príkaz", "warning": "Varovanie",
            "mobilizing": "Mobilizácia", "condemning": "Odsúdenie",
            "promising": "Sľub", "praising": "Chvála",
            "declaring": "Vyhlásenie", "justifying": "Obhajoba",
            "questioning": "Otázka", "persuading": "Presviedčanie",
            "record": "Záznam", "narrative": "Rozprávanie",
            "legitimation": "Legitimácia",
            "ideological_contestation": "Spochybnenie",
            "intervention": "Intervencia", "unclassified": "Neklasif.",
        },
        "en": {
            "commanding": "Command", "warning": "Warning",
            "mobilizing": "Mobilizing", "condemning": "Condemning",
            "promising": "Promise", "praising": "Praise",
            "declaring": "Declaration", "justifying": "Justification",
            "questioning": "Question", "persuading": "Persuasion",
            "record": "Record", "narrative": "Narrative",
            "legitimation": "Legitimation",
            "ideological_contestation": "Contestation",
            "intervention": "Intervention", "unclassified": "Unclassified",
        },
    },
    "strategy": {
        "cs": {
            "appeal_to_authority": "Autorita",
            "appeal_to_scripture": "Písmo",
            "appeal_to_tradition": "Tradice",
            "direct_address": "Oslovení",
            "rhetorical_question": "Řeč. otázka",
            "conditional_threat": "Hrozba",
            "promise_of_reward": "Odměna",
            "contrast": "Kontrast",
            "repetition": "Opakování",
            "narrative_example": "Příklad",
            "antithetical_disputation": "Antitetický spor",
            "apodictic_law": "Apodiktický zákon",
            "covenant_promise": "Smluvní zaslíbení",
            "declarative_assertion": "Deklarativní tvrzení",
            "dialogic_controversy": "Dialogický spor",
            "doxological_hymn": "Doxologický hymnus",
            "missionary_commission": "Misijní pověření",
            "narrative_chronicle": "Narativní kronika",
            "prophetic_admonition": "Prorocké napomenutí",
            "theological_rationale": "Teologické zdůvodnění",
            "theophanic_self_presentation": "Teofanické sebepředstavení",
            "woe_oracle": "Běda výrok",
            "unclassified": "Neklasif.",
        },
        "sk": {
            "appeal_to_authority": "Autorita",
            "appeal_to_scripture": "Písmo",
            "appeal_to_tradition": "Tradícia",
            "direct_address": "Oslovenie",
            "rhetorical_question": "Rečn. otázka",
            "conditional_threat": "Hrozba",
            "promise_of_reward": "Odmena",
            "contrast": "Kontrast",
            "repetition": "Opakovanie",
            "narrative_example": "Príklad",
            "antithetical_disputation": "Antitetický spor",
            "apodictic_law": "Apodiktický zákon",
            "covenant_promise": "Zmluvné zasľúbenie",
            "declarative_assertion": "Deklaratívne tvrdenie",
            "dialogic_controversy": "Dialogický spor",
            "doxological_hymn": "Doxologický hymnus",
            "missionary_commission": "Misijné poverenie",
            "narrative_chronicle": "Narativná kronika",
            "prophetic_admonition": "Prorocké napomenutie",
            "theological_rationale": "Teologické zdôvodnenie",
            "theophanic_self_presentation": "Teofanické sebapredstavenie",
            "woe_oracle": "Výrok beda",
            "unclassified": "Neklasif.",
        },
        "en": {
            "appeal_to_authority": "Authority",
            "appeal_to_scripture": "Scripture",
            "appeal_to_tradition": "Tradition",
            "direct_address": "Dir. address",
            "rhetorical_question": "Rhet. quest.",
            "conditional_threat": "Threat",
            "promise_of_reward": "Reward",
            "contrast": "Contrast",
            "repetition": "Repetition",
            "narrative_example": "Example",
            "antithetical_disputation": "Antithetical disputation",
            "apodictic_law": "Apodictic law",
            "covenant_promise": "Covenant promise",
            "declarative_assertion": "Declarative assertion",
            "dialogic_controversy": "Dialogic controversy",
            "doxological_hymn": "Doxological hymn",
            "missionary_commission": "Missionary commission",
            "narrative_chronicle": "Narrative chronicle",
            "prophetic_admonition": "Prophetic admonition",
            "theological_rationale": "Theological rationale",
            "theophanic_self_presentation": "Theophanic self-presentation",
            "woe_oracle": "Woe oracle",
            "unclassified": "Unclassif.",
        },
    },
    "semantic_cluster": {
        "cs": {
            "description": "Popis", "neutral": "Neutrální",
            "request": "Žádost", "negation": "Negace",
            "uncertainty": "Nejistota",
        },
        "sk": {
            "description": "Popis", "neutral": "Neutrálny",
            "request": "Žiadosť", "negation": "Negácia",
            "uncertainty": "Neistota",
        },
        "en": {
            "description": "Description", "neutral": "Neutral",
            "request": "Request", "negation": "Negation",
            "uncertainty": "Uncertainty",
        },
    },
    "skinner_class": {
        "cs": {
            "tact": "tact", "mand": "mand", "echoic": "echoic",
            "intraverbal": "intraverbal", "autoclitic": "autoclitic",
            "none": "žádná",
        },
        "sk": {
            "tact": "tact", "mand": "mand", "echoic": "echoic",
            "intraverbal": "intraverbal", "autoclitic": "autoclitic",
            "none": "žiadna",
        },
        "en": {
            "tact": "tact", "mand": "mand", "echoic": "echoic",
            "intraverbal": "intraverbal", "autoclitic": "autoclitic",
            "none": "none",
        },
    },
    "control_role": {
        "cs": {"stimulus": "stimulus", "response": "response", "record": "záznam"},
        "sk": {"stimulus": "stimulus", "response": "response", "record": "záznam"},
        "en": {"stimulus": "stimulus", "response": "response", "record": "record"},
    },
    "verbal_type": {
        "cs": {
            "autoclitic_relation": "Autoklit.",
            "descriptive_relation": "Popis",
            "genealogical_relation": "Genealog.",
            "historical_event_relation": "Histor.",
            "lyrical_relation": "Lyrická",
            "prophetic_relation": "Prorocká",
            "reported_speech": "Přímá řeč",
            "request_relation": "Žádost",
            "wisdom_relation": "Moudrost",
        },
        "sk": {
            "autoclitic_relation": "Autoklit.",
            "descriptive_relation": "Popis",
            "genealogical_relation": "Genealog.",
            "historical_event_relation": "Histor.",
            "lyrical_relation": "Lyrická",
            "prophetic_relation": "Prorocká",
            "reported_speech": "Priama reč",
            "request_relation": "Žiadosť",
            "wisdom_relation": "Múdrosť",
        },
        "en": {
            "autoclitic_relation": "Autoclitic",
            "descriptive_relation": "Descriptive",
            "genealogical_relation": "Genealog.",
            "historical_event_relation": "Historical",
            "lyrical_relation": "Lyrical",
            "prophetic_relation": "Prophetic",
            "reported_speech": "Rep. speech",
            "request_relation": "Request",
            "wisdom_relation": "Wisdom",
        },
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR — LANGUAGE SELECTOR
# ──────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 🌐 Language / Jazyk")
    lang = st.radio(
        "Jazyk / Language",
        options=["cs", "sk", "en"],
        format_func=lambda x: {"cs": "🇨🇿 Čeština", "sk": "🇸🇰 Slovenčina", "en": "🇬🇧 English"}[x],
        index=1,
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("### 🔬 NLP jazyk / NLP Language")
    pipeline_lang = st.radio(
        "NLP Language",
        options=["cs", "en"],
        format_func=lambda x: {
            "cs": "🇨🇿 Czech (Stanza pdt)",
            "en": "🇬🇧 English (Stanza ewt)",
        }[x],
        index=0,
        label_visibility="collapsed",
        help="Vyber jazyk NLP modelu zodpovedajúci textu ktorý chceš analyzovať. / Select the NLP model language matching the text you want to analyse.",
    )
    # Propagate to d_preprocessing at module level so get_nlp() picks it up
    import sys as _sys
    if "d_preprocessing" in _sys.modules:
        _sys.modules["d_preprocessing"].PIPELINE_LANG = pipeline_lang

T = TRANSLATIONS[lang]

VF  = VALUE_LABELS["force"][lang]
VI  = VALUE_LABELS["intention"][lang]
VS  = VALUE_LABELS["strategy"][lang]
VSC = VALUE_LABELS["semantic_cluster"][lang]
VSK = VALUE_LABELS["skinner_class"][lang]
VCR = VALUE_LABELS["control_role"][lang]
VVT = VALUE_LABELS["verbal_type"][lang]

# ──────────────────────────────────────────────────────────────────────────────
# BIBLE BOOK NAME MAPPING  (BKR abbreviation → full name per language)
# ──────────────────────────────────────────────────────────────────────────────

BOOK_NAMES: dict[str, dict[str, str]] = {
    # Pentateuch
    "Gn":  {"cs": "Genesis",            "sk": "Genezis",            "en": "Genesis"},
    "Ex":  {"cs": "Exodus",             "sk": "Exodus",             "en": "Exodus"},
    "Lv":  {"cs": "Leviticus",          "sk": "Levitikus",          "en": "Leviticus"},
    "Nu":  {"cs": "Numeri",             "sk": "Numeri",             "en": "Numbers"},
    "Dt":  {"cs": "Deuteronomium",      "sk": "Deuteronómium",      "en": "Deuteronomy"},
    # Historical books
    "Joz": {"cs": "Jozue",              "sk": "Jozua",              "en": "Joshua"},
    "Sd":  {"cs": "Soudců",             "sk": "Sudcov",             "en": "Judges"},
    "Rt":  {"cs": "Rut",                "sk": "Rút",                "en": "Ruth"},
    "1S":  {"cs": "1. Samuelova",       "sk": "1. Samuelova",       "en": "1 Samuel"},
    "2S":  {"cs": "2. Samuelova",       "sk": "2. Samuelova",       "en": "2 Samuel"},
    "1Kr": {"cs": "1. Královská",       "sk": "1. Kráľovská",       "en": "1 Kings"},
    "2Kr": {"cs": "2. Královská",       "sk": "2. Kráľovská",       "en": "2 Kings"},
    "1Pa": {"cs": "1. Paralipomenon",   "sk": "1. Kroník",          "en": "1 Chronicles"},
    "2Pa": {"cs": "2. Paralipomenon",   "sk": "2. Kroník",          "en": "2 Chronicles"},
    "Ezd": {"cs": "Ezdráš",             "sk": "Ezdráš",             "en": "Ezra"},
    "Neh": {"cs": "Nehemiáš",           "sk": "Nehemiáš",           "en": "Nehemiah"},
    "Est": {"cs": "Ester",              "sk": "Ester",              "en": "Esther"},
    # Wisdom books
    "Jb":  {"cs": "Job",                "sk": "Jób",                "en": "Job"},
    "Z":   {"cs": "Žalmy",              "sk": "Žalmy",              "en": "Psalms"},
    "Pr":  {"cs": "Přísloví",           "sk": "Príslovia",          "en": "Proverbs"},
    "Kaz": {"cs": "Kazatel",            "sk": "Kazateľ",            "en": "Ecclesiastes"},
    "Pis": {"cs": "Píseň písní",        "sk": "Pieseň piesní",      "en": "Song of Solomon"},
    # Major prophets
    "Iz":  {"cs": "Izajáš",             "sk": "Izaiáš",             "en": "Isaiah"},
    "Jr":  {"cs": "Jeremijáš",          "sk": "Jeremiáš",           "en": "Jeremiah"},
    "Pl":  {"cs": "Pláč Jeremijášův",   "sk": "Náreky Jeremiášove", "en": "Lamentations"},
    "Ez":  {"cs": "Ezechiel",           "sk": "Ezechiel",           "en": "Ezekiel"},
    "Da":  {"cs": "Daniel",             "sk": "Daniel",             "en": "Daniel"},
    # Minor prophets
    "Oz":  {"cs": "Ozeáš",              "sk": "Hozeáš",             "en": "Hosea"},
    "Jl":  {"cs": "Joel",               "sk": "Joel",               "en": "Joel"},
    "Am":  {"cs": "Ámos",               "sk": "Amos",               "en": "Amos"},
    "Abd": {"cs": "Abdiáš",             "sk": "Abdiáš",             "en": "Obadiah"},
    "Jon": {"cs": "Jonáš",              "sk": "Jonáš",              "en": "Jonah"},
    "Mi":  {"cs": "Micheáš",            "sk": "Micheáš",            "en": "Micah"},
    "Na":  {"cs": "Nahum",              "sk": "Nahum",              "en": "Nahum"},
    "Abk": {"cs": "Abakuk",             "sk": "Habakuk",            "en": "Habakkuk"},
    "Sf":  {"cs": "Sofonjáš",           "sk": "Sofoniáš",           "en": "Zephaniah"},
    "Ag":  {"cs": "Ageus",              "sk": "Aggeus",             "en": "Haggai"},
    "Za":  {"cs": "Zacharjáš",          "sk": "Zachariáš",          "en": "Zechariah"},
    "Mal": {"cs": "Malachiáš",          "sk": "Malachiáš",          "en": "Malachi"},
    # Gospels & Acts
    "Mt":  {"cs": "Matouš",             "sk": "Matúš",              "en": "Matthew"},
    "Mk":  {"cs": "Marek",              "sk": "Marek",              "en": "Mark"},
    "L":   {"cs": "Lukáš",              "sk": "Lukáš",              "en": "Luke"},
    "J":   {"cs": "Jan",                "sk": "Ján",                "en": "John"},
    "Sk":  {"cs": "Skutky apoštolů",    "sk": "Skutky apoštolov",   "en": "Acts"},
    # Pauline epistles
    "R":   {"cs": "Římanům",            "sk": "Rímskym",            "en": "Romans"},
    "1K":  {"cs": "1. Korintským",      "sk": "1. Korintanom",      "en": "1 Corinthians"},
    "2K":  {"cs": "2. Korintským",      "sk": "2. Korintanom",      "en": "2 Corinthians"},
    "Ga":  {"cs": "Galatským",          "sk": "Galaťanom",          "en": "Galatians"},
    "Ef":  {"cs": "Efezským",           "sk": "Efezanom",           "en": "Ephesians"},
    "Fp":  {"cs": "Filipským",          "sk": "Filipanom",          "en": "Philippians"},
    "Ko":  {"cs": "Kolosanům",          "sk": "Kološanom",          "en": "Colossians"},
    "1Te": {"cs": "1. Tesalonickým",    "sk": "1. Tesaloničanom",   "en": "1 Thessalonians"},
    "2Te": {"cs": "2. Tesalonickým",    "sk": "2. Tesaloničanom",   "en": "2 Thessalonians"},
    "1Tm": {"cs": "1. Timoteovi",       "sk": "1. Timotejovi",      "en": "1 Timothy"},
    "2Tm": {"cs": "2. Timoteovi",       "sk": "2. Timotejovi",      "en": "2 Timothy"},
    "Tit": {"cs": "Titovi",             "sk": "Títovi",             "en": "Titus"},
    "Fm":  {"cs": "Filemonovi",         "sk": "Filemonovi",         "en": "Philemon"},
    # General epistles
    "Zd":  {"cs": "Židům",              "sk": "Židom",              "en": "Hebrews"},
    "Jk":  {"cs": "Jakub",              "sk": "Jakub",              "en": "James"},
    "1P":  {"cs": "1. Petrův",          "sk": "1. Petrov",          "en": "1 Peter"},
    "2P":  {"cs": "2. Petrův",          "sk": "2. Petrov",          "en": "2 Peter"},
    "1J":  {"cs": "1. Janův",           "sk": "1. Jánov",           "en": "1 John"},
    "2J":  {"cs": "2. Janův",           "sk": "2. Jánov",           "en": "2 John"},
    "3J":  {"cs": "3. Janův",           "sk": "3. Jánov",           "en": "3 John"},
    "Ju":  {"cs": "Judův",              "sk": "Júda",               "en": "Jude"},
    # Apocalypse
    "Zj":  {"cs": "Zjevení",            "sk": "Zjavenie",           "en": "Revelation"},
}


def _bkr_abbr(v: object) -> str:
    """Normalize raw file names, abbreviations, or localized labels to a BKR abbreviation."""
    x = str(v or "").strip()
    if x.startswith("bible_BKR_"):
        x = x[len("bible_BKR_"):]
    if x.endswith(".txt"):
        x = x[:-4]
    if x in BOOK_NAMES:
        return x
    for abbr, names in BOOK_NAMES.items():
        if x in names.values():
            return abbr
    return x


def _bkr_book(s: "pd.Series") -> "pd.Series":
    """Convert a Series of BKR identifiers to full book names for the current UI language."""
    return s.map(lambda x: BOOK_NAMES.get(_bkr_abbr(x), {}).get(lang, str(x or "").strip()))


def _localize_book_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize Bible file/book columns to localized display labels."""
    out = df.copy()
    for col in ("file_name", "book"):
        if col in out.columns and out[col].dtype == object:
            out[col] = _bkr_book(out[col])
    return out


# ──────────────────────────────────────────────────────────────────────────────
# BOOK GROUPS  (canon sections, ordered; key matches i18n "group_*" labels)
# ──────────────────────────────────────────────────────────────────────────────

BOOK_GROUPS: list[tuple[str, list[str]]] = [
    ("group_pentateuch",     ["Gn", "Ex", "Lv", "Nu", "Dt"]),
    ("group_historical",     ["Joz", "Sd", "Rt", "1S", "2S", "1Kr", "2Kr",
                               "1Pa", "2Pa", "Ezd", "Neh", "Est"]),
    ("group_wisdom",         ["Jb", "Z", "Pr", "Kaz", "Pis"]),
    ("group_major_prophets", ["Iz", "Jr", "Pl", "Ez", "Da"]),
    ("group_minor_prophets", ["Oz", "Jl", "Am", "Abd", "Jon", "Mi",
                               "Na", "Abk", "Sf", "Ag", "Za", "Mal"]),
    ("group_gospels_acts",   ["Mt", "Mk", "L", "J", "Sk"]),
    ("group_pauline",        ["R", "1K", "2K", "Ga", "Ef", "Fp", "Ko",
                               "1Te", "2Te", "1Tm", "2Tm", "Tit", "Fm"]),
    ("group_general",        ["Zd", "Jk", "1P", "2P", "1J", "2J", "3J", "Ju"]),
    ("group_apocalypse",     ["Zj"]),
]


def _grouped_book_selectbox(key_prefix: str, available_books: list[str]) -> "str | None":
    """Two-level book selector: first a canon group, then an individual book.

    Returns the selected localized book name, or ``None`` when no specific book
    is chosen (= show all).
    """
    available_set = set(available_books)

    # Build list of (localized_group_label, [localized_book_names]) for groups
    # that have at least one book present in the available data.
    groups: list[tuple[str, list[str]]] = []
    for gkey, abbrevs in BOOK_GROUPS:
        names_in_group = [
            BOOK_NAMES[a][lang]
            for a in abbrevs
            if a in BOOK_NAMES and BOOK_NAMES[a].get(lang) in available_set
        ]
        if names_in_group:
            groups.append((T.get(gkey, gkey), names_in_group))

    all_groups_lbl = T.get("group_all", "— All groups")
    all_books_lbl  = "— " + T.get("filter_book_label", "All books")

    col1, col2 = st.columns(2)
    with col1:
        sel_grp = st.selectbox(
            T.get("filter_group_label", "Group"),
            [all_groups_lbl] + [g[0] for g in groups],
            key=f"{key_prefix}_group",
            label_visibility="collapsed",
        )

    # Determine the book list for the chosen group
    if sel_grp == all_groups_lbl:
        book_options = sorted(available_books)
    else:
        book_options = next(
            (names for lbl, names in groups if lbl == sel_grp), sorted(available_books)
        )

    with col2:
        sel_book = st.selectbox(
            T.get("filter_book_label", "Book"),
            [all_books_lbl] + book_options,
            key=f"{key_prefix}_book",
            label_visibility="collapsed",
        )

    return None if sel_book.startswith("—") else sel_book


def translate_clr(clr: dict, label_map: dict) -> dict:
    return {label_map.get(k, k): v for k, v in clr.items()}


# ──────────────────────────────────────────────────────────────────────────────
# COLOUR PALETTES
# ──────────────────────────────────────────────────────────────────────────────

INTENTION_CLR = {
    "commanding":               "#e63946",
    "warning":                  "#f4a261",
    "mobilizing":               "#e76f51",
    "condemning":               "#9d0208",
    "promising":                "#2a9d8f",
    "praising":                 "#57cc99",
    "declaring":                "#3a86ff",
    "justifying":               "#8338ec",
    "questioning":              "#fb8500",
    "persuading":               "#023e8a",
    "record":                   "#adb5bd",
    "narrative":                "#ced4da",
    "legitimation":             "#6a4c93",
    "ideological_contestation": "#c77dff",
    "intervention":             "#4cc9f0",
    "unclassified":             "#6c757d",
}

FORCE_CLR = {
    "directive":   "#e63946",
    "assertive":   "#3a86ff",
    "commissive":  "#2a9d8f",
    "expressive":  "#57cc99",
    "declarative": "#8338ec",
    "declarative_assertion": "#8338ec",
    "unknown":     "#6c757d",
}

STRATEGY_CLR = {
    "appeal_to_authority":  "#4361ee",
    "appeal_to_scripture":  "#7209b7",
    "appeal_to_tradition":  "#3a0ca3",
    "direct_address":       "#f72585",
    "rhetorical_question":  "#fb8500",
    "conditional_threat":   "#d62828",
    "promise_of_reward":    "#2a9d8f",
    "contrast":             "#118ab2",
    "repetition":           "#06d6a0",
    "narrative_example":    "#ffd166",
    "antithetical_disputation":  "#577590",
    "apodictic_law":             "#f94144",
    "covenant_promise":          "#43aa8b",
    "declarative_assertion":     "#3a86ff",
    "dialogic_controversy":      "#f3722c",
    "doxological_hymn":          "#9b5de5",
    "missionary_commission":     "#277da1",
    "narrative_chronicle":       "#4d908e",
    "prophetic_admonition":      "#f8961e",
    "theological_rationale":     "#7209b7",
    "theophanic_self_presentation":"#4361ee",
    "woe_oracle":                "#d00000",
    "unclassified":         "#adb5bd",
}

INT_CLR = translate_clr(INTENTION_CLR, VI)
FRC_CLR = translate_clr(FORCE_CLR, VF)
STR_CLR = translate_clr(STRATEGY_CLR, VS)

# ──────────────────────────────────────────────────────────────────────────────
# DATA HELPERS
# ──────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def csv(rel: str) -> pd.DataFrame | None:
    p = OUTPUT / rel
    return _localize_book_columns(pd.read_csv(p)) if p.exists() else None


@st.cache_data(ttl=300)
def load_db(lang: str = "sk") -> pd.DataFrame | None:
    db = OUTPUT / "bible_analysis.db"
    if not db.exists():
        return None
    import sqlite3
    from n_db import latest_bible_run_id
    conn = sqlite3.connect(db)
    run_id = latest_bible_run_id("skinner_analysis")
    if run_id is None:
        conn.close()
        return None
    df = pd.read_sql(
        """SELECT sentence_id, sentence, file_name,
                  illocutionary_force, primary_intention, secondary_intention,
                  primary_strategy, CAST(confidence AS REAL) AS confidence,
                  CAST(type_token_ratio AS REAL) AS type_token_ratio,
                  has_coordination, dative_present, indirect_object_present,
                  adjective_count, adverb_count, pronoun_count
           FROM skinner_analysis WHERE run_id = ?""",
        conn, params=(run_id,),
    )
    conn.close()
    return _localize_book_columns(df.assign(book=_bkr_book(df["file_name"])))


def _fig_png(fig, w: int = 820, h: int = 380) -> bytes:
    """Render a Plotly figure to PNG bytes via kaleido."""
    return fig.to_image(format="png", width=w, height=h, scale=1.5)


def _df_table(df: pd.DataFrame, max_rows: int = 40) -> list:
    """Convert a DataFrame to a list-of-lists for reportlab Table."""
    df = df.head(max_rows)
    header = list(df.columns)
    rows   = [header] + [[str(v) for v in row] for row in df.itertuples(index=False)]
    return rows


def generate_pdf_report(
    df: pd.DataFrame,
    lemmas_data: list,
    lang: str,
    pipeline_lang: str,
    translations: dict,
    vi: dict, vf: dict, vs: dict, vsk: dict,
    int_clr: dict, frc_clr: dict, str_clr: dict,
    session: dict,
) -> bytes:
    """
    Build a PDF report mirroring Tab 3 Výsledky.
    Returns raw PDF bytes.
    """
    import io as _io
    from datetime import datetime
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors as rlc
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Image as RLImage,
        Table as RLTable, TableStyle, HRFlowable, PageBreak,
    )
    from reportlab.lib.enums import TA_LEFT, TA_CENTER

    T   = translations
    buf = _io.BytesIO()
    W, H = A4
    margin = 1.8 * cm

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=margin, rightMargin=margin,
        topMargin=margin, bottomMargin=margin,
        title="Skinner Pipeline Report",
    )

    ss = getSampleStyleSheet()
    sty = {
        "title":   ParagraphStyle("rpt_title",   parent=ss["Title"],
                                   fontSize=18, spaceAfter=6),
        "h1":      ParagraphStyle("rpt_h1",      parent=ss["Heading1"],
                                   fontSize=13, textColor=rlc.HexColor("#1a1a2e"),
                                   spaceBefore=14, spaceAfter=4),
        "h2":      ParagraphStyle("rpt_h2",      parent=ss["Heading2"],
                                   fontSize=11, textColor=rlc.HexColor("#3a86ff"),
                                   spaceBefore=8, spaceAfter=3),
        "body":    ParagraphStyle("rpt_body",    parent=ss["Normal"],
                                   fontSize=9, leading=13, spaceAfter=4),
        "caption": ParagraphStyle("rpt_cap",     parent=ss["Normal"],
                                   fontSize=8, textColor=rlc.HexColor("#555555"),
                                   spaceAfter=4, fontName="Helvetica-Oblique"),
        "meta":    ParagraphStyle("rpt_meta",    parent=ss["Normal"],
                                   fontSize=8, textColor=rlc.HexColor("#888888")),
    }

    IMG_W = W - 2 * margin          # full-width chart image
    IMG_W2 = (IMG_W - 0.4*cm) / 2  # half-width (side-by-side)

    def _hr():
        return HRFlowable(width="100%", thickness=0.5,
                          color=rlc.HexColor("#dddddd"), spaceAfter=6)

    def _section(name: str, icon: str = ""):
        return [
            Spacer(1, 0.3*cm),
            Paragraph(f"{icon} {name}", sty["h1"]),
            _hr(),
        ]

    def _chart(fig, caption_text: str = "", full: bool = True) -> list:
        try:
            img_bytes = _fig_png(fig,
                                  w=int((IMG_W if full else IMG_W2) / cm * 37.8),
                                  h=300)
            img_w = IMG_W if full else IMG_W2
            elems: list = [RLImage(_io.BytesIO(img_bytes), width=img_w, height=img_w * 0.46)]
            if caption_text:
                elems.append(Paragraph(caption_text, sty["caption"]))
            return elems
        except Exception as e:
            return [Paragraph(f"[chart error: {e}]", sty["body"])]

    def _side_by_side(fig1, fig2, cap1: str = "", cap2: str = "") -> list:
        try:
            b1 = _fig_png(fig1, w=int(IMG_W2 / cm * 37.8), h=260)
            b2 = _fig_png(fig2, w=int(IMG_W2 / cm * 37.8), h=260)
            cell_h = IMG_W2 * 0.53
            data = [[
                RLImage(_io.BytesIO(b1), width=IMG_W2, height=cell_h),
                RLImage(_io.BytesIO(b2), width=IMG_W2, height=cell_h),
            ]]
            tbl = RLTable(data, colWidths=[IMG_W2, IMG_W2])
            tbl.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"),
                                     ("LEFTPADDING", (0,0), (-1,-1), 0),
                                     ("RIGHTPADDING", (0,0), (-1,-1), 6)]))
            out: list = [tbl]
            if cap1 or cap2:
                cap_data = [[Paragraph(cap1, sty["caption"]),
                             Paragraph(cap2, sty["caption"])]]
                cap_tbl = RLTable(cap_data, colWidths=[IMG_W2, IMG_W2])
                out.append(cap_tbl)
            return out
        except Exception as e:
            return [Paragraph(f"[chart error: {e}]", sty["body"])]

    def _table(df_data: pd.DataFrame, max_rows: int = 30) -> list:
        rows = _df_table(df_data, max_rows)
        if not rows:
            return []
        col_count = len(rows[0])
        col_w = (IMG_W) / col_count
        tbl = RLTable(rows, colWidths=[col_w] * col_count, repeatRows=1)
        tbl.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (-1, 0),  rlc.HexColor("#3a86ff")),
            ("TEXTCOLOR",   (0, 0), (-1, 0),  rlc.white),
            ("FONTNAME",    (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",    (0, 0), (-1, -1), 7),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [rlc.HexColor("#f8f9fa"), rlc.white]),
            ("GRID",        (0, 0), (-1, -1), 0.3, rlc.HexColor("#cccccc")),
            ("VALIGN",      (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING",(0, 0), (-1, -1), 4),
            ("TOPPADDING",  (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 2),
            ("WORDWRAP",    (0, 0), (-1, -1), True),
        ]))
        return [tbl, Spacer(1, 0.2*cm)]

    # ── Build story ──────────────────────────────────────────────────────────
    story: list = []

    # Cover
    story.append(Paragraph("Skinner Pipeline", sty["title"]))
    story.append(Paragraph(T.get("results_title", "Analysis Report"), sty["h2"]))
    _total = len(df)
    _classif = int((df["primary_intention"] != "unclassified").sum())
    _mconf = float(df["confidence"].mean())
    _src = session.get("adf_source", "—")
    meta_rows = [
        ["Source", _src],
        [T.get("metric_sentences","Sentences"), str(_total)],
        [T.get("metric_classified","Classified"), f"{_classif}/{_total}"],
        [T.get("metric_confidence","Confidence"), f"{_mconf:.2f}"],
        ["NLP model", pipeline_lang],
        ["Date", datetime.now().strftime("%Y-%m-%d %H:%M")],
    ]
    meta_tbl = RLTable(meta_rows, colWidths=[4*cm, IMG_W - 4*cm])
    meta_tbl.setStyle(TableStyle([
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("TOPPADDING", (0,0), (-1,-1), 3),
        ("LINEBELOW", (0,-1), (-1,-1), 0.5, rlc.HexColor("#dddddd")),
    ]))
    story += [meta_tbl, Spacer(1, 0.5*cm), _hr()]

    # ── 1. Q. Skinner ────────────────────────────────────────────────────────
    if session.get("sel_q_skinner", True):
        story += _section(T.get("ana_qs_name","Q. Skinner"), "⚡")
        story.append(Paragraph(T.get("ana_qs_q",""), sty["caption"]))

        ic = df["primary_intention"].value_counts().reset_index()
        ic.columns = ["_raw", "count"]
        ic["intention"] = ic["_raw"].map(vi).fillna(ic["_raw"])
        fig_int = px.bar(ic.sort_values("count"), x="count", y="intention",
                         orientation="h", title=T.get("intent_pie_title","Intentions"),
                         color="intention", color_discrete_map=int_clr)
        fig_int.update_layout(showlegend=False, margin=dict(t=40,b=4,l=4,r=4))

        sc = df["primary_strategy"].value_counts().reset_index()
        sc.columns = ["_raw", "count"]
        sc["strategy"] = sc["_raw"].map(vs).fillna(sc["_raw"])
        sc = sc[sc["_raw"] != "unclassified"].head(10)
        fig_str = px.bar(sc.sort_values("count"), x="count", y="strategy",
                         orientation="h", title=T.get("strategy_bar_title","Strategies"),
                         color="strategy", color_discrete_map=str_clr)
        fig_str.update_layout(showlegend=False, margin=dict(t=40,b=4,l=4,r=4))

        story += _side_by_side(fig_int, fig_str,
                                T.get("intent_pie_desc",""),
                                T.get("strategy_bar_desc",""))

        fc = df["illocutionary_force"].value_counts().reset_index()
        fc.columns = ["_raw", "count"]
        fc["force"] = fc["_raw"].map(vf).fillna(fc["_raw"])
        fig_fc = px.pie(fc, names="force", values="count",
                        title=T.get("force_pie_title","Speech Acts"),
                        color="force", color_discrete_map=frc_clr, hole=0.3)
        fig_fc.update_layout(margin=dict(t=40,b=4,l=4,r=4))

        df_box = df.copy()
        df_box["intention"] = df_box["primary_intention"].map(vi).fillna(df_box["primary_intention"])
        fig_box = px.box(df_box, x="intention", y="confidence", color="intention",
                         color_discrete_map=int_clr,
                         title=T.get("conf_hist_title","Confidence"), points=False)
        fig_box.update_layout(showlegend=False, margin=dict(t=40,b=4,l=4,r=4))
        fig_box.update_xaxes(tickangle=-40)

        story += _side_by_side(fig_fc, fig_box,
                                T.get("force_pie_desc",""),
                                T.get("conf_hist_desc",""))

        # Sentence table — extended columns
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph(T.get("section_sentence_table","Sentences"), sty["h2"]))
        disp_cols = ["sentence_id","sentence","primary_intention","secondary_intention",
                     "illocutionary_force","primary_strategy","secondary_strategy",
                     "convention","confidence","reason"]
        show = [c for c in disp_cols if c in df.columns]
        story += _table(df[show].head(40))

        # Secondary intention
        story.append(PageBreak())
        story += _section(T.get("secondary_intent_title","Sekundárny zámer"), "↳")
        _si = df["secondary_intention"].dropna().value_counts().reset_index()
        _si.columns = ["intention", "count"]
        _si["intention_lbl"] = _si["intention"].map(vi).fillna(_si["intention"])
        if not _si.empty:
            fig_si = px.bar(_si.sort_values("count"), x="count", y="intention_lbl",
                            orientation="h", color="intention_lbl",
                            color_discrete_map=int_clr,
                            title=T.get("secondary_intent_title","Secondary intention"))
            fig_si.update_layout(showlegend=False, margin=dict(t=40,b=4,l=4,r=4))
            _ss2 = df["secondary_strategy"].dropna().value_counts().reset_index()
            _ss2.columns = ["strategy", "count"]
            _ss2["strategy_lbl"] = _ss2["strategy"].map(vs).fillna(_ss2["strategy"])
            fig_ss2 = px.bar(_ss2.sort_values("count"), x="count", y="strategy_lbl",
                             orientation="h", color="strategy_lbl",
                             color_discrete_map=str_clr,
                             title="Sekundárna stratégia")
            fig_ss2.update_layout(showlegend=False, margin=dict(t=40,b=4,l=4,r=4))
            story += _side_by_side(fig_si, fig_ss2,
                                   T.get("secondary_intent_desc",""),
                                   T.get("strategy_bar_desc",""))

        # Convention types
        story += _section("Typy konvencie", "📜")
        _cv = df["convention"].dropna().value_counts().head(15).reset_index()
        _cv.columns = ["convention", "count"]
        if not _cv.empty:
            fig_cv = px.bar(_cv.sort_values("count"), x="count", y="convention",
                            orientation="h", color_discrete_sequence=["#8338ec"],
                            title="Typy konvencie (top 15)")
            fig_cv.update_layout(showlegend=False, margin=dict(t=40,b=4,l=4,r=4))

            # Political vocabulary
            import re as _re_pdf
            _pv = (df["political_vocabulary"].dropna()
                   .str.split(",").explode().str.strip()
                   .str.extract(r'^([^\[]+)')[0].str.strip()
                   .value_counts().head(15).reset_index())
            _pv.columns = ["term", "count"]
            if not _pv.empty:
                fig_pv = px.bar(_pv.sort_values("count"), x="count", y="term",
                                orientation="h", color_discrete_sequence=["#3a86ff"],
                                title=T.get("pvoc_title","Political vocabulary"))
                fig_pv.update_layout(showlegend=False, margin=dict(t=40,b=4,l=4,r=4))
                story += _side_by_side(fig_cv, fig_pv,
                                       "Top 15 rétorických konvencií",
                                       T.get("pvoc_desc",""))
            else:
                story += _chart(fig_cv, "Top 15 rétorických konvencií")

        # Anti-anachronism
        if "anti_anachronism" in df.columns:
            story += _section("Anti-anachronizmus", "⚠️")
            _flagged_n = (df["anti_anachronism"] != "none_flagged").sum()
            _tot_n = len(df)
            _aa_pie_df = pd.DataFrame({
                "status": ["bez príznaku", "s príznakom"],
                "count": [_tot_n - _flagged_n, _flagged_n],
            })
            fig_aapie = px.pie(_aa_pie_df, names="status", values="count",
                               color="status",
                               color_discrete_map={"bez príznaku":"#76B7B2","s príznakom":"#E15759"},
                               hole=0.35,
                               title=f"Anti-anachronizmus — {_flagged_n} viet ({100*_flagged_n/_tot_n:.1f}%)")
            fig_aapie.update_layout(margin=dict(t=40,b=4,l=4,r=4))
            _terms_pdf = []
            for _v in df["anti_anachronism"].dropna():
                if _v == "none_flagged": continue
                for _c in str(_v).split(";"):
                    _m = _re_pdf.match(r'\s*(\w+)\s*:', _c.strip())
                    if _m: _terms_pdf.append(_m.group(1).strip())
            from collections import Counter as _C
            _tc_pdf = pd.DataFrame(_C(_terms_pdf).most_common(12), columns=["term","count"])
            if not _tc_pdf.empty:
                fig_aaterms = px.bar(_tc_pdf.sort_values("count"), x="count", y="term",
                                     orientation="h", color_discrete_sequence=["#E15759"],
                                     title="Frekvencia anachronických termínov")
                fig_aaterms.update_layout(showlegend=False, margin=dict(t=40,b=4,l=4,r=4))
                story += _side_by_side(fig_aapie, fig_aaterms)
            else:
                story += _chart(fig_aapie, "Podiel viet s anachronickým príznakom")

    # ── 2. B.F. Skinner ──────────────────────────────────────────────────────
    if session.get("sel_bf_skinner", True):
        _tax_cl = OUTPUT / "taxonomy_analytics/skinner_class_counts.csv"
        _tax_ta = OUTPUT / "taxonomy_analytics/tact_vs_autoclitic_by_book.csv"
        if _tax_cl.exists():
            story += _section(T.get("ana_bf_name","B.F. Skinner"), "⚡")
            story.append(Paragraph(T.get("ana_bf_q",""), sty["caption"]))
            _tc = pd.read_csv(_tax_cl)
            _tc.columns = ["_raw", "count"]
            _tc["class"] = _tc["_raw"].map(vsk).fillna(_tc["_raw"])
            fig_tc = px.bar(_tc.sort_values("count"), x="count", y="class",
                            orientation="h", title=T.get("tax_class_title","Classes"))
            fig_tc.update_layout(showlegend=False, margin=dict(t=40,b=4,l=4,r=4))
            if _tax_ta.exists():
                _ta = pd.read_csv(_tax_ta)
                _ta["book"] = _bkr_book(
                    _ta["file_name"]
                    .str.replace("bible_BKR_","", regex=False)
                    .str.replace(".txt","", regex=False))
                fig_ta = go.Figure()
                fig_ta.add_bar(name="tact", x=_ta["book"], y=_ta["tact_ratio"],
                               marker_color="#3a86ff")
                fig_ta.add_bar(name="autoclitic", x=_ta["book"],
                               y=_ta["autoclitic_ratio"], marker_color="#8338ec")
                fig_ta.update_layout(barmode="group",
                                     title=T.get("tact_autoclitic_title","Tact vs Autoclitic"),
                                     margin=dict(t=40,b=4,l=4,r=4))
                story += _side_by_side(fig_tc, fig_ta)
            else:
                story += _chart(fig_tc)

    # ── 3. Verbálne vzťahy ────────────────────────────────────────────────────
    if session.get("sel_verbal", True):
        _vr_path = OUTPUT / "verbal_relations_analytics/relation_type_counts.csv"
        if _vr_path.exists():
            story += _section(T.get("ana_verbal_name","Verbal Relations"), "⚡")
            story.append(Paragraph(T.get("ana_verbal_q",""), sty["caption"]))
            _vr = pd.read_csv(_vr_path)
            _vr = _vr.sort_values("count", ascending=False)
            _vr.columns = ["type", "count"]
            fig_vr = px.bar(_vr, x="count", y="type", orientation="h",
                            title=T.get("verbal_types_title","Verbal Relations"))
            fig_vr.update_layout(showlegend=False, margin=dict(t=40,b=4,l=4,r=4))
            story += _chart(fig_vr, T.get("verbal_types_desc",""))

    # ── 4. Sémantika ──────────────────────────────────────────────────────────
    if session.get("sel_semantics", True) and lemmas_data:
        story += _section(T.get("ana_semantics_name","Semantics"), "⚡")
        story.append(Paragraph(T.get("ana_semantics_q",""), sty["caption"]))
        from collections import Counter as _SC
        _STOP_S = {"být","ten","on","se","si","the","be","have","that","this",
                   "which","with","from","they","their","are","was","were",
                   "not","but","and","for","its","his","her","may","also"}
        _all_l = [t for _,ls in lemmas_data for t in ls.split()
                  if len(t)>2 and t.isalpha() and t not in _STOP_S]
        _fq = _SC(_all_l)
        _fq_df = pd.DataFrame(_fq.most_common(25), columns=["lemma","count"])
        if not _fq_df.empty:
            fig_lm = px.bar(_fq_df, x="count", y="lemma", orientation="h",
                            title=T.get("ana_semantics_name","Top Lemmas"))
            fig_lm.update_layout(showlegend=False, margin=dict(t=40,b=4,l=4,r=4))
            story += _chart(fig_lm)

    # ── 5. Náboženské elementy ────────────────────────────────────────────────
    if session.get("sel_religious", True) and lemmas_data:
        story += _section(T.get("ana_religious_name","Religious Elements"), "⚡")
        story.append(Paragraph(T.get("ana_religious_q",""), sty["caption"]))
        from t_config_tradition import TRADITIONS, PHILOSOPHICAL_INFLUENCES as PHI
        _ls = set(t for _,ls in lemmas_data for t in ls.split() if len(t)>2 and t.isalpha())
        _tname = "christian_english" if pipeline_lang=="en" else "christian_czech"
        _elh = {el:len(_ls&lx) for el,lx in TRADITIONS.get(_tname,{}).items() if _ls&lx}
        _phh = {ph:len(_ls&lx) for ph,lx in PHI.items() if _ls&lx}
        if _elh:
            _edf = pd.DataFrame(sorted(_elh.items(),key=lambda x:-x[1]),
                                columns=["element","count"])
            fig_el = px.bar(_edf, x="count", y="element", orientation="h",
                            title=T.get("element_coverage_title","Religious Elements"))
            fig_el.update_layout(showlegend=False, margin=dict(t=40,b=4,l=4,r=4))
            if _phh:
                _pdf = pd.DataFrame(sorted(_phh.items(),key=lambda x:-x[1]),
                                    columns=["influence","count"])
                fig_ph = px.bar(_pdf, x="count", y="influence", orientation="h",
                                title=T.get("philosophy_title","Philosophy"))
                fig_ph.update_layout(showlegend=False, margin=dict(t=40,b=4,l=4,r=4))
                story += _side_by_side(fig_el, fig_ph)
            else:
                story += _chart(fig_el)

    # ── 6. Sieť slov ─────────────────────────────────────────────────────────
    if session.get("sel_network", False):
        _cent_path = OUTPUT / "weighted_centrality/weighted_semantic_centrality.csv"
        if _cent_path.exists():
            story += _section(T.get("ana_network_name","Word Network"), "🕐")
            story.append(Paragraph(T.get("ana_network_q",""), sty["caption"]))
            _cent = pd.read_csv(_cent_path).nlargest(25, "weighted_score")
            fig_cn = px.bar(_cent, x="weighted_score", y="word", orientation="h",
                            title=T.get("centrality_bar_title","Centrality"))
            fig_cn.update_layout(showlegend=False, margin=dict(t=40,b=4,l=4,r=4))
            story += _chart(fig_cn, T.get("centrality_bar_desc",""))

    # ── 7. Textové vzory ──────────────────────────────────────────────────────
    if session.get("sel_patterns", False) and lemmas_data:
        story += _section(T.get("ana_patterns_name","Text Patterns"), "🕐")
        story.append(Paragraph(T.get("ana_patterns_q",""), sty["caption"]))
        from w_opposition_networks import OPPOSITION_PAIRS
        from collections import Counter as _OC
        _oh: dict = {}
        _nl = len(lemmas_data)
        for _ii,(_,_ls_i) in enumerate(lemmas_data):
            _win2: set = set()
            for _,_ls_j in lemmas_data[max(0,_ii-3):min(_nl,_ii+4)]:
                _win2 |= set(_ls_j.split())
            for _w1,_w2 in OPPOSITION_PAIRS:
                if _w1 in _win2 and _w2 in _win2:
                    _k = f"{_w1} | {_w2}"
                    _oh[_k] = _oh.get(_k,0)+1
        if _oh:
            _odf = pd.DataFrame(sorted(_oh.items(),key=lambda x:-x[1])[:15],
                                columns=[T.get("opposition_title","Pair"),"count"])
            fig_op = px.bar(_odf, x="count",
                            y=T.get("opposition_title","Pair"),
                            orientation="h", title=T.get("opposition_title","Oppositions"))
            fig_op.update_layout(showlegend=False, margin=dict(t=40,b=4,l=4,r=4))
            story += _chart(fig_op, T.get("opposition_window_note",""))

    # ── 8. Štýl a syntax ─────────────────────────────────────────────────────
    if session.get("sel_style", False):
        _cplx_path = OUTPUT / "dependency_hierarchy/complexity_by_book.csv"
        if _cplx_path.exists():
            story += _section(T.get("ana_style_name","Style & Syntax"), "🕐")
            story.append(Paragraph(T.get("ana_style_q",""), sty["caption"]))
            _cx = pd.read_csv(_cplx_path)
            _cx["book"] = _bkr_book(
                _cx["file_name"]
                .str.replace("bible_BKR_","", regex=False)
                .str.replace(".txt","", regex=False))
            fig_d = px.bar(_cx, x="avg_tree_depth", y="book", orientation="h",
                           title=T.get("x_depth","Avg tree depth"))
            fig_d.update_layout(showlegend=False, margin=dict(t=40,b=4,l=4,r=4))
            fig_c = px.bar(_cx, x="avg_clause_count", y="book", orientation="h",
                           title=T.get("x_clauses","Avg clause count"))
            fig_c.update_layout(showlegend=False, margin=dict(t=40,b=4,l=4,r=4))
            story += _side_by_side(fig_d, fig_c,
                                    T.get("x_depth",""), T.get("x_clauses",""))

    # ── 9. Kvalita ────────────────────────────────────────────────────────────
    if session.get("sel_quality", True):
        story += _section(T.get("ana_quality_name","Quality"), "⚡")
        story.append(Paragraph(T.get("ana_quality_q",""), sty["caption"]))
        _cband_l = int((df["confidence"] < 0.30).sum())
        _cband_m = int(((df["confidence"]>=0.30)&(df["confidence"]<0.60)).sum())
        _cband_h = int((df["confidence"]>=0.60).sum())
        _qdf = pd.DataFrame({
            "band": [T.get("conf_band_low","Low"),
                     T.get("conf_band_mid","Mid"),
                     T.get("conf_band_high","High")],
            "count": [_cband_l, _cband_m, _cband_h],
        })
        fig_qi = px.bar(_qdf, x="count", y="band", orientation="h",
                        color="band",
                        color_discrete_map={
                            T.get("conf_band_low","Low"): "#e63946",
                            T.get("conf_band_mid","Mid"): "#f4a261",
                            T.get("conf_band_high","High"): "#57cc99",
                        },
                        title=T.get("conf_bins_title","Confidence Bands"))
        fig_qi.update_layout(showlegend=False, margin=dict(t=40,b=4,l=4,r=4))

        df_bx = df.copy()
        df_bx["intention"] = df_bx["primary_intention"].map(vi).fillna(df_bx["primary_intention"])
        fig_bx = px.box(df_bx, x="intention", y="confidence", color="intention",
                        color_discrete_map=int_clr,
                        title=T.get("conf_hist_title","Confidence"), points=False)
        fig_bx.update_layout(showlegend=False, margin=dict(t=40,b=4,l=4,r=4))
        fig_bx.update_xaxes(tickangle=-40)
        story += _side_by_side(fig_qi, fig_bx)

    # ── 10. Dashboard ─────────────────────────────────────────────────────────
    if session.get("sel_dashboard", True):
        story += _section(T.get("ana_dashboard_name","Dashboard"), "⚡")
        story.append(Paragraph(T.get("ana_dashboard_q",""), sty["caption"]))
        from n_db import count_table_rows, list_runs, TABLE_SKINNER
        _db_n = count_table_rows(TABLE_SKINNER)
        _runs = list_runs(TABLE_SKINNER)
        _upr  = [r for r in _runs if r.startswith("upload_")]
        dash_data = [
            ["Source", _src],
            ["Sentences", str(_total)],
            ["DB rows (skinner_analysis)", str(_db_n or "—")],
            ["Bible runs in DB", str(len(_runs)-len(_upr))],
            ["Upload runs in DB", str(len(_upr))],
            ["NLP model", pipeline_lang],
            ["Generated", datetime.now().strftime("%Y-%m-%d %H:%M")],
        ]
        dash_tbl = RLTable(dash_data, colWidths=[5*cm, IMG_W-5*cm])
        dash_tbl.setStyle(TableStyle([
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0,0), (-1,-1),
             [rlc.HexColor("#f0f4ff"), rlc.white]),
            ("GRID", (0,0), (-1,-1), 0.3, rlc.HexColor("#cccccc")),
            ("TOPPADDING", (0,0), (-1,-1), 3),
            ("BOTTOMPADDING", (0,0), (-1,-1), 3),
            ("LEFTPADDING", (0,0), (-1,-1), 5),
        ]))
        story.append(dash_tbl)

    doc.build(story)
    buf.seek(0)
    return buf.read()


def _make_upload_run_id(source_name: str) -> str:
    """Generate upload_{sanitized_filename}_{timestamp} run_id."""
    import re
    from datetime import datetime
    stem = Path(source_name).stem if source_name != "pasted_text" else "pasted_text"
    stem = re.sub(r"[^a-zA-Z0-9_\-]", "_", stem)[:40].strip("_") or "upload"
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    return f"upload_{stem}_{ts}"


def _save_to_db(
    skinner_df: pd.DataFrame,
    run_id: str,
    rel_df: "pd.DataFrame | None" = None,
    ref_df: "pd.DataFrame | None" = None,
) -> int:
    """Write all three analysis DataFrames to DB under run_id. Returns total row count."""
    import sys as _sys
    _sys.path.insert(0, str(SRC))
    from n_db import insert_rows, TABLE_SKINNER, TABLE_RELATIONS, TABLE_REFINED
    total = 0
    if skinner_df is not None and not skinner_df.empty:
        total += insert_rows(TABLE_SKINNER, skinner_df.to_dict("records"), run_id)
    if rel_df is not None and not rel_df.empty:
        total += insert_rows(TABLE_RELATIONS, rel_df.to_dict("records"), run_id)
    if ref_df is not None and not ref_df.empty:
        total += insert_rows(TABLE_REFINED, ref_df.to_dict("records"), run_id)
    return total


def _read_upload(f) -> str:
    if f.name.lower().endswith(".pdf"):
        import pdfplumber
        pages = []
        with pdfplumber.open(io.BytesIO(f.read())) as pdf:
            for page in pdf.pages:
                # x_tolerance=7 merges character-spaced PDFs ("T H E" → "THE")
                words = page.extract_words(x_tolerance=7, y_tolerance=5)
                if words:
                    pages.append(" ".join(w["text"] for w in words))
                else:
                    pages.append(page.extract_text() or "")
        return "\n\n".join(pages)
    return f.read().decode("utf-8", errors="replace")


@st.cache_resource(show_spinner="Loading Stanza NLP model (first run ~10 s)…")
def _pipeline():
    from c_input import create_input_from_text
    from d_preprocessing import preprocess_text
    from e_extraction import extract_features
    from f_semantics import semantic_enrichment
    from j_q_skinner_taxonomy import classify_q_skinner
    return create_input_from_text, preprocess_text, extract_features, semantic_enrichment, classify_q_skinner


def run_upload_pipeline(
    text: str,
    corpus_id: str,
    source: str = "uploaded_document",
    interaction: str = "unknown",
    stimulus: str = "unknown",
    sentence_window: int = 150,
) -> tuple:
    """Run the full 4-stage pipeline on an uploaded text, segmented into chapters.

    Returns
    -------
    (skinner_df, rel_df, ref_df, units, lemmas)
    where `units` is a list of AnalysisUnit objects and `lemmas` is the
    per-sentence (sentence, lemma_string) list for backward compatibility.
    """
    from c_segment import segment_book
    from k_pipeline_core import process_unit

    units = segment_book(
        text=text,
        corpus_id=corpus_id,
        source_name=corpus_id,
        sentence_window=sentence_window,
    )

    all_sk, all_rel, all_ref = [], [], []
    lemmas = []

    # Warm up Stanza via existing cache
    _pipeline()

    for unit in units:
        # Override source/interaction/stimulus on the unit from user selection
        unit.source = source
        unit.interaction = interaction
        unit.stimulus = stimulus

        result = process_unit(unit)

        all_sk.extend(result.skinner_rows)
        all_rel.extend(result.relation_rows)
        all_ref.extend(result.refined_rows)

    # Build backward-compat lemmas list from skinner rows (sentence + lemmas col)
    for row in all_sk:
        lemmas.append((row.get("sentence", ""), row.get("lemmas", "")))

    skinner_df = pd.DataFrame(all_sk) if all_sk else pd.DataFrame()
    rel_df = pd.DataFrame(all_rel) if all_rel else pd.DataFrame()
    ref_df = pd.DataFrame(all_ref) if all_ref else pd.DataFrame()

    return skinner_df, rel_df, ref_df, units, lemmas


def run_pipeline(
    text: str,
    source: str = "uploaded_document",
    interaction: str = "unknown",
    stimulus: str = "unknown",
) -> tuple:
    """Legacy single-stage pipeline (Q. Skinner only). Kept for compatibility."""
    from dataclasses import asdict
    mk_input, preprocess, extract, enrich, classify = _pipeline()
    inp = mk_input(text=text, source=source, interaction=interaction, stimulus=stimulus)
    pre = preprocess(inp)
    feats = extract(pre)
    sems = enrich(feats)
    rows = [asdict(classify(f, s, inp)) for f, s in zip(feats, sems)]
    lemmas = [(f.sentence, f.lemmas) for f in feats]
    return pd.DataFrame(rows), lemmas



def _context_warnings(source: str, interaction: str, stimulus: str, T: dict) -> list[str]:
    """Return list of localised warning strings for inconsistent context params."""
    warns = []
    if interaction == "monologue" and stimulus in {"question_prompt", "answer_context"}:
        warns.append(T["ctx_warn_qa_mono"])
    if source in {"written_record", "uploaded_document"} and stimulus == "auditory_verbal_stimulus":
        warns.append(T["ctx_warn_audio_written"])
    if source == "spoken_record" and stimulus == "written_verbal_stimulus":
        warns.append(T["ctx_warn_written_spoken"])
    if interaction == "dialogue" and stimulus == "none":
        warns.append(T["ctx_warn_dialogue_none"])
    return warns


# ──────────────────────────────────────────────────────────────────────────────
# CHART HELPERS
# ──────────────────────────────────────────────────────────────────────────────

_LAYOUT = dict(margin=dict(t=44, b=4, l=4, r=4))


def fig_hbar(df, x, y, title, clr=None, h=360, xlabel=None, ylabel=None):
    df = df.sort_values(x, ascending=True)
    fig = px.bar(df, x=x, y=y, orientation="h", title=title, color=y,
                 color_discrete_map=clr or {})
    fig.update_layout(showlegend=False, height=h, **_LAYOUT)
    if xlabel:
        fig.update_xaxes(title_text=xlabel)
    if ylabel:
        fig.update_yaxes(title_text=ylabel)
    return fig


def fig_pie(df, names, values, title, clr=None):
    fig = px.pie(df, names=names, values=values, title=title,
                 color=names, color_discrete_map=clr or {}, hole=0.3)
    fig.update_layout(height=360, **_LAYOUT)
    return fig


def fig_heatmap(df_wide, id_col, title, h=420, fmt=None):
    cols = [c for c in df_wide.columns if c not in (id_col, "total")]
    z = df_wide[cols].values
    if df_wide[id_col].dtype == object:
        abbrevs = (df_wide[id_col]
                   .str.replace("bible_BKR_", "", regex=False)
                   .str.replace(".txt", "", regex=False))
        y_labels = _bkr_book(abbrevs)
    else:
        y_labels = df_wide[id_col]
    fig = go.Figure(go.Heatmap(
        z=z, x=cols, y=y_labels,
        colorscale="Blues",
        hoverongaps=False,
        texttemplate=fmt,
    ))
    fig.update_layout(title=title, height=h, **_LAYOUT)
    fig.update_xaxes(tickangle=-60)
    return fig


def fig_conf_hist(df, title, xlabel):
    fig = px.histogram(df, x="confidence", nbins=20,
                       title=title,
                       color_discrete_sequence=["#3a86ff"])
    fig.update_xaxes(title_text=xlabel)
    fig.update_layout(height=300, **_LAYOUT)
    return fig


def fig_box_confidence(df, intent_col, conf_col, title, clr=None):
    fig = px.box(df, x=intent_col, y=conf_col, color=intent_col,
                 color_discrete_map=clr or {},
                 title=title, points=False)
    fig.update_xaxes(tickangle=-40, title_text="")
    fig.update_yaxes(title_text=conf_col, range=[0, 1])
    fig.update_layout(showlegend=False, height=360, **_LAYOUT)
    return fig


def _top_n_cols(df_wide: pd.DataFrame, id_col: str, n: int) -> pd.DataFrame:
    """Keep only the top-n columns by total sum (for heatmap filtering)."""
    value_cols = [c for c in df_wide.columns if c not in (id_col, "total")]
    if len(value_cols) <= n:
        return df_wide
    sums = df_wide[value_cols].sum().nlargest(n).index.tolist()
    return df_wide[[id_col] + sums]


# ──────────────────────────────────────────────────────────────────────────────
# EXTRA DATA LOADERS (sections 13–15)
# ──────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def load_refined(lang: str = "sk") -> pd.DataFrame | None:
    db = OUTPUT / "bible_analysis.db"
    if not db.exists():
        return None
    import sqlite3
    from n_db import latest_bible_run_id
    conn = sqlite3.connect(db)
    run_id = latest_bible_run_id("refined_descriptions")
    if run_id is None:
        conn.close()
        return None
    df = pd.read_sql(
        """SELECT sentence_id, sentence, file_name,
                  description_type, semantic_cluster, lemmas
           FROM refined_descriptions WHERE run_id=?""",
        conn, params=(run_id,),
    )
    conn.close()
    return _localize_book_columns(df.assign(book=_bkr_book(df["file_name"])))


@st.cache_data(ttl=300)
def load_verbal_full(lang: str = "sk") -> pd.DataFrame | None:
    db = OUTPUT / "bible_analysis.db"
    if not db.exists():
        return None
    import sqlite3
    from n_db import latest_bible_run_id
    conn = sqlite3.connect(db)
    run_id = latest_bible_run_id("verbal_relations")
    if run_id is None:
        conn.close()
        return None
    df = pd.read_sql(
        """SELECT sentence_id, sentence, file_name,
                  local_pattern, semantic_cluster
           FROM verbal_relations WHERE run_id=?""",
        conn, params=(run_id,),
    )
    conn.close()
    return _localize_book_columns(df.assign(book=_bkr_book(df["file_name"])))


@st.cache_data(ttl=600)
def compute_wordcloud_img(sentences: tuple) -> bytes:
    from wordcloud import WordCloud
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import io as _io
    text = " ".join(sentences)
    wc = WordCloud(
        width=960, height=420, background_color="white",
        colormap="Blues_r", max_words=200, collocations=False,
    ).generate(text)
    buf = _io.BytesIO()
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    fig.tight_layout(pad=0)
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


@st.cache_data(ttl=600)
def compute_ngrams(sentences: tuple, n: int, top_k: int = 20) -> pd.DataFrame:
    from sklearn.feature_extraction.text import CountVectorizer
    vec = CountVectorizer(
        ngram_range=(n, n), min_df=3, max_features=1000,
        token_pattern=r"[a-zA-ZáčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ]+",
    )
    X = vec.fit_transform(list(sentences))
    counts = X.sum(axis=0).A1
    vocab = vec.get_feature_names_out()
    df = pd.DataFrame({"ngram": vocab, "count": counts})
    return df.nlargest(top_k, "count").reset_index(drop=True)


@st.cache_data(ttl=600)
def compute_tfidf_heatmap(lemmas_items: tuple, top_n: int = 35) -> pd.DataFrame:
    from sklearn.feature_extraction.text import TfidfVectorizer
    books = [b for b, _ in lemmas_items]
    docs  = [d for _, d in lemmas_items]
    vec = TfidfVectorizer(
        max_features=600, min_df=2,
        token_pattern=r"[a-zA-ZáčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ]{3,}",
    )
    X = vec.fit_transform(docs).toarray()
    terms = vec.get_feature_names_out()
    tfidf_df = pd.DataFrame(X, index=books, columns=terms)
    top_terms = tfidf_df.var(axis=0).nlargest(top_n).index.tolist()
    result = tfidf_df[top_terms].copy()
    result.index.name = "book"
    return result.reset_index()


@st.cache_data(ttl=600)
def compute_lexical_reinforcement(lemmas_items: tuple) -> pd.DataFrame:
    from collections import Counter
    STOP = {"být", "ten", "on", "já", "my", "vy", "se", "si", "co",
            "který", "jako", "ale", "ani", "pak", "již", "jej", "jež"}
    rows = []
    for book, lemmas_str in lemmas_items:
        tokens = [t for t in str(lemmas_str or "").split()
                  if len(t) > 2 and t.isalpha() and t not in STOP]
        if not tokens:
            continue
        c = Counter(tokens)
        rows.append({"book": book, "reinforcement": 1.0 - len(c) / len(tokens)})
    if not rows:
        return pd.DataFrame(columns=["book", "reinforcement"])
    return pd.DataFrame(rows).groupby("book")["reinforcement"].mean().reset_index()


# ──────────────────────────────────────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────────────────────────────────────

st.title(T["app_title"])
st.caption(T["app_subtitle"])

# Auto-switch to Tab 3 after a completed run
if st.session_state.pop("_switch_to_results", False):
    st.markdown(
        """<script>setTimeout(()=>{
            const t=window.parent.document.querySelectorAll('[data-baseweb="tab"]');
            if(t&&t.length>=3)t[2].click();
        },350);</script>""",
        unsafe_allow_html=True,
    )

tab_analyze, tab_bible, tab_results, tab_compare = st.tabs(
    [T["tab_analyze"], T["tab_bible"], T["tab_results"], T["tab_compare"]]
)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — ANALYZE TEXT
# ══════════════════════════════════════════════════════════════════════════════

with tab_analyze:

    # ── ABOUT EXPANDER ───────────────────────────────────────────────────────
    with st.expander(T["about_title"]):
        st.markdown(T["about_text"])

    st.divider()

    # ── UPLOAD / PASTE ───────────────────────────────────────────────────────
    st.subheader(T["upload_header"])
    col_up, col_paste = st.columns([1, 2])
    with col_up:
        uploaded = st.file_uploader(T["upload_label"], type=["txt", "pdf"])
    with col_paste:
        pasted = st.text_area(
            T["paste_label"], height=130,
            placeholder=(
                "Hospodin řekl Mojžíšovi: Já jsem Hospodin Bůh tvůj. "
                "Nebudete-li činiti pokání, všickni podobně zahynete. "
                "Jděte do všeho světa a kažte evangelium."
            ),
        )

    # ── SEGMENTATION PREVIEW ─────────────────────────────────────────────────
    _preview_text = pasted.strip() if pasted.strip() else None
    if _preview_text:
        from c_segment import segment_book as _seg_preview
        _prev_units = _seg_preview(_preview_text, corpus_id="preview")
        _prev_n = len(_prev_units)
        _prev_method = (_prev_units[0].segmentation_method if _prev_units else "single_unit") or "single_unit"
        _method_labels = {
            "chapter_markers": T["seg_method_chapter"],
            "section_markers": T["seg_method_section"],
            "single_unit":     T["seg_method_single"],
        }
        _unit_word = T["seg_preview_unit"] if _prev_n == 1 else T["seg_preview_units"]
        st.info(
            f"🔍 **{T['seg_preview_title']}:** "
            f"{_method_labels.get(_prev_method, _prev_method)} · "
            f"**{_prev_n}** {_unit_word}"
        )

    # ── CONTEXT PARAMETERS ───────────────────────────────────────────────────
    with st.expander(T["ctx_expander"], expanded=False):
        _ctx_cols = st.columns(3)
        with _ctx_cols[0]:
            _src_keys  = list(T["ctx_source_opts"].keys())
            _src_labels = list(T["ctx_source_opts"].values())
            _src_idx = st.selectbox(
                T["ctx_source_label"],
                options=range(len(_src_keys)),
                format_func=lambda i: _src_labels[i],
                key="ctx_source",
            )
            ctx_source = _src_keys[_src_idx]
        with _ctx_cols[1]:
            _int_keys   = list(T["ctx_interaction_opts"].keys())
            _int_labels = list(T["ctx_interaction_opts"].values())
            _int_idx = st.selectbox(
                T["ctx_interaction_label"],
                options=range(len(_int_keys)),
                format_func=lambda i: _int_labels[i],
                key="ctx_interaction",
            )
            ctx_interaction = _int_keys[_int_idx]
        with _ctx_cols[2]:
            _stim_keys   = list(T["ctx_stimulus_opts"].keys())
            _stim_labels = list(T["ctx_stimulus_opts"].values())
            _stim_idx = st.selectbox(
                T["ctx_stimulus_label"],
                options=range(len(_stim_keys)),
                format_func=lambda i: _stim_labels[i],
                key="ctx_stimulus",
            )
            ctx_stimulus = _stim_keys[_stim_idx]

        for _w in _context_warnings(ctx_source, ctx_interaction, ctx_stimulus, T):
            st.warning(_w)
    # read back outside the expander so run_button can use them
    ctx_source      = st.session_state.get("ctx_source",      0)
    ctx_interaction = st.session_state.get("ctx_interaction", 0)
    ctx_stimulus    = st.session_state.get("ctx_stimulus",    0)
    ctx_source      = list(T["ctx_source_opts"].keys())[ctx_source]      if isinstance(ctx_source, int)      else ctx_source
    ctx_interaction = list(T["ctx_interaction_opts"].keys())[ctx_interaction] if isinstance(ctx_interaction, int) else ctx_interaction
    ctx_stimulus    = list(T["ctx_stimulus_opts"].keys())[ctx_stimulus]   if isinstance(ctx_stimulus, int)    else ctx_stimulus

    st.divider()

    # ── ANALYSIS MODULE CHECKBOXES ───────────────────────────────────────────
    st.subheader(T["select_analyses"])

    _MODS = [
        ("sel_bf_skinner",   "⚡", T["ana_bf_name"],        "~1 min",  T["ana_bf_q"]),
        ("sel_q_skinner",    "⚡", T["ana_qs_name"],         "~1 min",  T["ana_qs_q"]),
        ("sel_verbal",       "⚡", T["ana_verbal_name"],     "~1 min",  T["ana_verbal_q"]),
        ("sel_semantics",    "⚡", T["ana_semantics_name"],  "~1 min",  T["ana_semantics_q"]),
        ("sel_religious",    "⚡", T["ana_religious_name"],  "~1 min",  T["ana_religious_q"]),
        ("sel_network",      "🕐", T["ana_network_name"],    "~5 min",  T["ana_network_q"]),
        ("sel_patterns",     "🕐", T["ana_patterns_name"],   "~3 min",  T["ana_patterns_q"]),
        ("sel_style",        "🕐", T["ana_style_name"],      "~10 min", T["ana_style_q"]),
        ("sel_quality",      "⚡", T["ana_quality_name"],    "~30s",    T["ana_quality_q"]),
        ("sel_dashboard",    "⚡", T["ana_dashboard_name"],  "~10s",    T["ana_dashboard_q"]),
    ]

    _cb_cols = st.columns(2)
    for _idx, (_key, _icon, _name, _time, _question) in enumerate(_MODS):
        with _cb_cols[_idx % 2]:
            st.checkbox(
                f"{_icon} **{_name}** `{_time}`",
                value=st.session_state.get(_key, _idx < 5),
                key=_key,
                help=_question,
            )

    st.divider()

    # ── RUN BUTTON ───────────────────────────────────────────────────────────
    st.caption(T["run_hint"])
    if st.button(T["run_button"], type="primary", use_container_width=True):
        text = ""
        source_name = "pasted_text"
        if uploaded:
            with st.spinner(T["reading_file"]):
                text = _read_upload(uploaded)
            source_name = uploaded.name
        elif pasted.strip():
            text = pasted.strip()

        if not text:
            st.warning(T["no_text_warning"])
        else:
            _pre_warns = _context_warnings(ctx_source, ctx_interaction, ctx_stimulus, T)
            for _w in _pre_warns:
                st.warning(_w)
            if not _pre_warns:
                with st.spinner(T["running_pipeline"]):
                    from c_segment import make_corpus_id
                    _corpus_id = make_corpus_id(source_name)
                    adf, adf_rel, adf_ref, adf_units, adf_lemmas = run_upload_pipeline(
                        text,
                        corpus_id=_corpus_id,
                        source=ctx_source,
                        interaction=ctx_interaction,
                        stimulus=ctx_stimulus,
                    )
                    st.session_state["adf"] = adf
                    st.session_state["adf_rel"] = adf_rel
                    st.session_state["adf_ref"] = adf_ref
                    st.session_state["adf_units"] = adf_units
                    st.session_state["adf_corpus_id"] = _corpus_id
                    st.session_state["adf_lemmas"] = adf_lemmas
                    st.session_state["adf_source"] = source_name
                    st.session_state["adf_seg_mode"] = adf_units[0].unit_type if adf_units else "document"
                    st.session_state.pop("adf_saved_run_id", None)
                    st.session_state["_switch_to_results"] = True
                st.success(T["results_ready_msg"])
                st.rerun()

    # ── DETAILED MODULE DESCRIPTIONS ─────────────────────────────────────────
    st.divider()
    with st.expander(T["detail_expander_title"]):
        _DETAIL_MODS = [
            (T["ana_bf_name"],        T["ana_bf_detail"]),
            (T["ana_qs_name"],        T["ana_qs_detail"]),
            (T["ana_verbal_name"],    T["ana_verbal_detail"]),
            (T["ana_semantics_name"], T["ana_semantics_detail"]),
            (T["ana_religious_name"], T["ana_religious_detail"]),
            (T["ana_network_name"],   T["ana_network_detail"]),
            (T["ana_patterns_name"],  T["ana_patterns_detail"]),
            (T["ana_style_name"],     T["ana_style_detail"]),
            (T["ana_quality_name"],   T["ana_quality_detail"]),
            (T["ana_dashboard_name"], T["ana_dashboard_detail"]),
        ]
        for _dname, _dtext in _DETAIL_MODS:
            with st.expander(f"**{_dname}**"):
                st.markdown(_dtext)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — BIBLE CORPUS
# ══════════════════════════════════════════════════════════════════════════════

with tab_bible:

    st.subheader(T["bible_header"])
    st.caption(T["bible_caption"])

    db_df = load_db(lang)

    if db_df is None:
        st.warning(T["no_db"])
    else:
        # ── TOP METRICS ──────────────────────────────────────────────────────────
        total_b = len(db_df)
        books_b = db_df["book"].nunique()
        cov_b = 100 * (db_df["primary_intention"] != "unclassified").mean()
        conf_b = db_df["confidence"].mean()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric(T["metric_total"], f"{total_b:,}")
        c2.metric(T["metric_books"], books_b)
        c3.metric(T["metric_coverage"], f"{cov_b:.1f} %")
        c4.metric(T["metric_mean_conf"], f"{conf_b:.2f}")

        st.divider()

        # ── BOOK GROUP FILTER ─────────────────────────────────────────────────────
        _all_grps_lbl = T.get("group_all", "— All groups")
        _grp_label_options = [_all_grps_lbl] + [T.get(gk, gk) for gk, _ in BOOK_GROUPS]
        _sel_grp = st.selectbox(
            T.get("filter_group_label", "Book group"),
            _grp_label_options,
            key="bible_top_group",
        )

        # Build the set of localized book names belonging to the chosen group
        if _sel_grp == _all_grps_lbl:
            _grp_book_set: "set[str] | None" = None
        else:
            _grp_book_set = {
                a
                for gk, abbrevs in BOOK_GROUPS
                if T.get(gk, gk) == _sel_grp
                for a in abbrevs
                if a in BOOK_NAMES
            }

        def _flt(df: "pd.DataFrame | None", col: str = "book") -> "pd.DataFrame | None":
            """Filter df rows to the selected book group (no-op when all groups selected)."""
            if _grp_book_set is None or df is None or col not in df.columns:
                return df
            return df[df[col].map(_bkr_abbr).isin(_grp_book_set)]

        def _flt_csv(df: "pd.DataFrame | None", col: str = "file_name") -> "pd.DataFrame | None":
            """Filter wide CSV (rows = books) to the selected book group."""
            if _grp_book_set is None or df is None or col not in df.columns:
                return df
            return df[df[col].map(_bkr_abbr).isin(_grp_book_set)]

        # Apply the group filter to the main DB frame used by all later sections
        db_df = _flt(db_df)

        st.divider()

        # ── 1. INTENTION ANALYSIS ─────────────────────────────────────────────────
        with st.expander("📖 " + T["sec_intention"], expanded=True):

            int_cnt  = csv("q_skinner_analytics/q_intention_counts.csv")
            int_book = csv("q_skinner_analytics/q_intention_by_book.csv")
            force_cnt = csv("q_skinner_analytics/q_illocutionary_force_counts.csv")

            c1, c2 = st.columns(2)

            with c1:
                if int_cnt is not None:
                    d = int_cnt.sort_values("count", ascending=False).copy()
                    d.columns = ["_raw", T["x_count"]]
                    d[T["x_intention"]] = d["_raw"].map(VI).fillna(d["_raw"])
                    st.caption(T["all_intentions_desc"])
                    st.plotly_chart(
                        fig_hbar(d, T["x_count"], T["x_intention"],
                                 T["all_intentions_title"], INT_CLR,
                                 xlabel=T["x_count"], ylabel=T["x_intention"]),
                        use_container_width=True,
                    )
            with c2:
                if force_cnt is not None:
                    d = force_cnt.copy()
                    d.columns = ["_raw", T["x_count"]]
                    d[T["x_force"]] = d["_raw"].map(VF).fillna(d["_raw"])
                    st.caption(T["force_all_desc"])
                    st.plotly_chart(
                        fig_pie(d, T["x_force"], T["x_count"],
                                T["force_all_title"], FRC_CLR),
                        use_container_width=True,
                    )

            if int_book is not None:
                hm = _flt_csv(int_book).copy()
                if hm.empty:
                    st.info(T["no_group_data"])
                else:
                    hm_cols = [c for c in hm.columns if c not in {"file_name", "total"}]
                    hm = hm.rename(columns={c: VI.get(c, c) for c in hm_cols})
                    _n_int = st.slider(T["top_n_slider"], 5, min(30, len(hm_cols)), min(15, len(hm_cols)),
                                       key="hm_int_n")
                    hm = _top_n_cols(hm, "file_name", _n_int)
                    st.caption(T["intent_book_heatmap_desc"])
                    st.plotly_chart(
                        fig_heatmap(hm, "file_name",
                                    T["intent_book_heatmap_title"], h=420),
                        use_container_width=True,
                    )

        # ── 2. STRATEGY ANALYSIS ─────────────────────────────────────────────────
        with st.expander("📖 " + T["sec_strategy"]):

            strat_cnt  = csv("q_skinner_analytics/q_strategy_counts.csv")
            strat_book = csv("q_skinner_analytics/q_strategy_by_book.csv")
            pvoc       = csv("q_skinner_analytics/q_political_vocabulary_counts.csv")

            c1, c2 = st.columns(2)

            with c1:
                if strat_cnt is not None:
                    d = strat_cnt[strat_cnt["primary_strategy"] != "unclassified"].copy()
                    d = d.sort_values("count", ascending=False)
                    d.columns = ["_raw", T["x_count"]]
                    d[T["x_strategy"]] = d["_raw"].map(VS).fillna(d["_raw"])
                    st.caption(T["all_strategies_desc"])
                    st.plotly_chart(
                        fig_hbar(d, T["x_count"], T["x_strategy"],
                                 T["all_strategies_title"], STR_CLR,
                                 xlabel=T["x_count"], ylabel=T["x_strategy"]),
                        use_container_width=True,
                    )
            with c2:
                if pvoc is not None:
                    st.caption(T["pvoc_desc"])
                    st.plotly_chart(
                        fig_hbar(pvoc.head(20), "count", "term",
                                 T["pvoc_title"], h=400,
                                 xlabel=T["x_count"]),
                        use_container_width=True,
                    )

            if strat_book is not None:
                excl = {"file_name", "total", "unclassified"}
                s_cols = [c for c in strat_book.columns if c not in excl]
                hm2 = _flt_csv(strat_book)[["file_name"] + s_cols].copy()
                if hm2.empty:
                    st.info(T["no_group_data"])
                else:
                    hm2 = hm2.rename(columns={c: VS.get(c, c) for c in s_cols})
                    st.caption(T["strat_book_heatmap_desc"])
                    st.plotly_chart(
                        fig_heatmap(hm2, "file_name", T["strat_book_heatmap_title"], h=420),
                        use_container_width=True,
                    )

        # ── 3. KEY RATIOS ─────────────────────────────────────────────────────────
        with st.expander("📖 " + T["sec_ratios"]):

            ratios = csv("q_skinner_analytics/q_key_ratios_by_book.csv")

            if ratios is not None:
                books_lbl = _bkr_book(
                    ratios["file_name"]
                    .str.replace("bible_BKR_", "", regex=False)
                    .str.replace(".txt", "", regex=False))

                c1, c2 = st.columns(2)

                with c1:
                    st.caption(T["directive_assertive_desc"])
                    fig = go.Figure()
                    fig.add_bar(name=T["lbl_directive"], x=books_lbl,
                                y=ratios["directive"], marker_color="#e63946")
                    fig.add_bar(name=T["lbl_assertive"], x=books_lbl,
                                y=ratios["assertive"], marker_color="#3a86ff")
                    fig.update_layout(barmode="stack",
                                      title=T["directive_assertive_title"],
                                      xaxis_title=T["x_book"],
                                      yaxis_title=T["x_count"],
                                      height=360, **_LAYOUT)
                    st.plotly_chart(fig, use_container_width=True)

                with c2:
                    st.caption(T["legit_ratio_desc"])
                    ratio_map = {
                        "legitimation_ratio":             T["lbl_legitimation"],
                        "ideological_contestation_ratio": T["lbl_contestation"],
                        "intervention_ratio":             T["lbl_intervention"],
                    }
                    fig2 = go.Figure()
                    for col, label in ratio_map.items():
                        if col in ratios.columns:
                            fig2.add_bar(name=label, x=books_lbl, y=ratios[col])
                    fig2.update_layout(
                        barmode="group",
                        title=T["legit_ratio_title"],
                        xaxis_title=T["x_book"],
                        yaxis_title=T["x_ratio"],
                        height=360, **_LAYOUT,
                    )
                    st.plotly_chart(fig2, use_container_width=True)

            else:
                st.info(T["no_ratios"])

        # ── 4. RELIGIOUS ELEMENTS ─────────────────────────────────────────────────
        with st.expander("📖 " + T["sec_religious"]):

            field_sum    = csv("religious_elements/field_summary.csv")
            density_wide = csv("religious_elements/combined_density_by_book.csv")
            phil         = csv("religious_elements/philosophy_by_book.csv")

            c1, c2 = st.columns(2)

            _rel_el = T.get("rel_elements", {})
            _rel_ph = T.get("rel_philosophy", {})

            with c1:
                if field_sum is not None:
                    d = field_sum.sort_values("sentence_count", ascending=False).copy()
                    d["element"] = d["element"].map(lambda v: _rel_el.get(v, v))
                    d = d.rename(columns={"element": T["x_element"],
                                          "sentence_count": T["x_count"]})
                    st.caption(T["element_coverage_desc"])
                    st.plotly_chart(
                        fig_hbar(d, T["x_count"], T["x_element"],
                                 T["element_coverage_title"], h=420,
                                 xlabel=T["x_count"], ylabel=T["x_element"]),
                        use_container_width=True,
                    )
            with c2:
                if phil is not None:
                    pc = phil.groupby("philosophy")["matched_count"].sum().reset_index()
                    pc["philosophy"] = pc["philosophy"].map(lambda v: _rel_ph.get(v, v))
                    st.caption(T["philosophy_desc"])
                    st.plotly_chart(
                        fig_pie(pc, "philosophy", "matched_count",
                                T["philosophy_title"]),
                        use_container_width=True,
                    )

            if density_wide is not None:
                s_cols = [c for c in density_wide.columns
                          if c.endswith("_sentence_density")]
                dn = density_wide[["file_name"] + s_cols].copy()
                dn.columns = (
                    ["file_name"] +
                    [_rel_el.get(c.replace("_sentence_density", ""),
                                 c.replace("_sentence_density", "")) for c in s_cols]
                )
                _n_dens = st.slider(T["top_n_slider"], 5, min(30, len(s_cols)), min(15, len(s_cols)),
                                    key="hm_dens_n")
                dn = _top_n_cols(dn, "file_name", _n_dens)
                st.caption(T["density_heatmap_desc"])
                st.plotly_chart(
                    fig_heatmap(dn, "file_name",
                                T["density_heatmap_title"],
                                h=460, fmt="%{z:.2f}"),
                    use_container_width=True,
                )

            st.divider()
            from t_config_tradition import TRADITIONS, PHILOSOPHICAL_INFLUENCES
            st.caption(T["traditions_desc"])
            c1, c2 = st.columns(2)
            _LANG_SFXS = ("_czech", "_english", "_arabic", "_hebrew", "_pali", "_sanskrit")
            def _fmt_trad(k: str) -> str:
                for sfx in _LANG_SFXS:
                    if k.endswith(sfx):
                        return k[:-len(sfx)].replace("_", " ").title()
                return k.replace("_", " ").title()

            with c1:
                trad_df = pd.DataFrame(
                    [{"tradition": _fmt_trad(k), T["x_categories"]: len(v)}
                     for k, v in TRADITIONS.items()]
                ).sort_values(T["x_categories"], ascending=True)
                st.plotly_chart(
                    fig_hbar(trad_df, T["x_categories"], "tradition",
                             T["traditions_title"], h=520,
                             xlabel=T["x_categories"]),
                    use_container_width=True,
                )
            with c2:
                phil_df = pd.DataFrame(
                    [{"influence": k, T["x_terms"]: len(v)}
                     for k, v in PHILOSOPHICAL_INFLUENCES.items()]
                ).sort_values(T["x_terms"], ascending=True)
                st.plotly_chart(
                    fig_hbar(phil_df, T["x_terms"], "influence",
                             T["traditions_title"], h=480,
                             xlabel=T["x_terms"]),
                    use_container_width=True,
                )

        # ── 5. CONCEPT CLUSTERS & OPPOSITIONS ────────────────────────────────────
        with st.expander("📖 " + T["sec_clusters"]):

            c1, c2 = st.columns(2)

            with c1:
                clust = csv("concept_clusters/cluster_summary.csv")
                if clust is not None:
                    _cl_map = T.get("cluster_labels", {})
                    clust["label"] = clust["cluster"].str.replace("_cluster", "").map(
                        lambda v: _cl_map.get(v, v.replace("_", " ").title())
                    )
                    sz = clust["total_pair_count"]
                    fig = go.Figure(go.Scatter(
                        x=clust["avg_pmi"],
                        y=clust["edge_count"],
                        mode="markers+text",
                        text=clust["label"],
                        textposition="top center",
                        marker=dict(
                            size=(sz / sz.max() * 44 + 12).tolist(),
                            color="#3a86ff", opacity=0.7,
                            line=dict(width=1, color="white"),
                        ),
                    ))
                    fig.update_layout(
                        title=T["cluster_bubble_title"],
                        xaxis_title=T["x_avg_pmi"],
                        yaxis_title=T["x_edges"],
                        height=400, **_LAYOUT,
                    )
                    st.caption(T["cluster_bubble_desc"])
                    st.plotly_chart(fig, use_container_width=True)

            with c2:
                opp = csv("opposition_networks/opposition_counts.csv")
                if opp is not None:
                    st.caption(T["opposition_window_note"] + "  " + T["opposition_desc"])
                    st.plotly_chart(
                        fig_hbar(opp.head(18), "count", "opposition_pair",
                                 T["opposition_title"], h=420,
                                 xlabel=T["x_count"],
                                 ylabel=T["opposition_title"]),
                        use_container_width=True,
                    )

            # ── Polarity analysis ─────────────────────────────────────────────────
            polarity = csv("opposition_networks/opposition_polarity.csv")
            if polarity is not None:
                st.divider()
                st.caption(T["opposition_polarity_desc"])
                pol = polarity.copy()
                pol["pair"] = pol["opposition_pair"]
                pol = pol.sort_values("total", ascending=False).head(16)

                fig_pol = go.Figure()
                fig_pol.add_bar(
                    name=T["lbl_positive"], x=pol["pair"], y=pol["positive"],
                    marker_color="#57cc99",
                )
                fig_pol.add_bar(
                    name=T["lbl_negative"], x=pol["pair"], y=pol["negative"],
                    marker_color="#e63946",
                )
                fig_pol.add_bar(
                    name=T["lbl_both"], x=pol["pair"], y=pol["both"],
                    marker_color="#adb5bd",
                )
                fig_pol.update_layout(
                    barmode="stack",
                    title=T["opposition_polarity_title"],
                    xaxis_title=T["opposition_title"],
                    yaxis_title=T["x_count"],
                    xaxis_tickangle=-40,
                    height=400, **_LAYOUT,
                )
                st.plotly_chart(fig_pol, use_container_width=True)

            # ── Directed edges + examples ─────────────────────────────────────────
            directed = csv("opposition_networks/opposition_directed_edges.csv")
            opp_ex   = csv("opposition_networks/opposition_examples.csv")

            # ── Directed chart — full width, ylabel = word not "source" ──────────
            if directed is not None:
                st.caption(T["opposition_directed_desc"])
                st.plotly_chart(
                    fig_hbar(directed.head(20), "weight", "source",
                             T["opposition_directed_title"], h=420,
                             xlabel=T["col_weight"], ylabel=T["x_word"]),
                    use_container_width=True,
                )

            # ── Edge list | Examples — side by side ───────────────────────────────
            _d1, _d2 = st.columns([1, 2])

            with _d1:
                if directed is not None:
                    st.markdown(f"**{T['opposition_directed_title']}**")
                    for _, _row in directed.head(15).iterrows():
                        st.markdown(
                            f"**{_row['source']}** → {_row['target']} "
                            f"&nbsp; `{int(_row['weight'])}`"
                        )

            with _d2:
                if opp_ex is not None:
                    _pairs_avail = ["— " + T["filter_pair"]] + sorted(
                        opp_ex["opposition_pair"].unique()
                    )
                    _sel_pair = st.selectbox(
                        T["filter_pair"], _pairs_avail,
                        key="opp_pair_sel", label_visibility="collapsed",
                    )
                    _view_ex = (
                        opp_ex if _sel_pair.startswith("—")
                        else opp_ex[opp_ex["opposition_pair"] == _sel_pair]
                    ).copy()
                    _view_ex["book"] = _bkr_book(
                        _view_ex["file_name"]
                        .str.replace("bible_BKR_", "", regex=False)
                        .str.replace(".txt", "", regex=False))
                    st.caption(T["opposition_examples_desc"])
                    for _, _er in _view_ex.head(12).iterrows():
                        st.markdown(
                            f"*{_er['opposition_pair']}* &nbsp;·&nbsp; "
                            f"**{_er['book']}**"
                        )
                        st.markdown(f"> {_er['sentence']}")
                        st.divider()

        # ── 6. SEMANTIC CENTRALITY ────────────────────────────────────────────────
        with st.expander("📖 " + T["sec_centrality"]):

            cent = csv("weighted_centrality/weighted_semantic_centrality.csv")

            if cent is not None:
                top_n = st.slider(T["top_n_slider"], 10, 60, 30, key="cent_n")
                top_w = cent.nlargest(top_n, "weighted_score")
                st.caption(T["centrality_bar_desc"])
                st.plotly_chart(
                    fig_hbar(top_w, "weighted_score", "word",
                             T["centrality_bar_title"],
                             h=max(380, top_n * 18),
                             xlabel=T["x_weighted"], ylabel=T["x_word"]),
                    use_container_width=True,
                )
                st.dataframe(
                    top_w[["word", "weighted_score",
                            "connection_count", "avg_pmi"]]
                    .rename(columns={
                        "word":             T["x_word"],
                        "weighted_score":   T["x_weighted"],
                        "connection_count": T["x_connections"],
                        "avg_pmi":          T["x_avg_pmi"],
                    })
                    .reset_index(drop=True),
                    use_container_width=True,
                    height=360,
                    column_config={
                        T["x_weighted"]:    st.column_config.NumberColumn(format="%.1f"),
                        T["x_avg_pmi"]:     st.column_config.NumberColumn(format="%.2f"),
                    },
                )
            else:
                st.info(T["no_centrality"])

        # ── 7. STYLE & AUTHORSHIP ─────────────────────────────────────────────────
        with st.expander("📖 " + T["sec_style"]):

            style = csv("style_authorship/book_style_clusters.csv")
            terms = csv("style_authorship/cluster_top_terms.csv")

            if style is not None:
                c1, c2 = st.columns([1, 2])

                with c1:
                    sd = style.copy()
                    sd["book"] = _bkr_book(
                        sd["file_name"]
                        .str.replace("bible_BKR_", "", regex=False)
                        .str.replace(".txt", "", regex=False))
                    st.caption(T["style_table_desc"])
                    st.dataframe(
                        sd[["book", "style_cluster", "silhouette_score"]].rename(columns={
                            "book":             T["x_book"],
                            "style_cluster":    T["col_style_cluster"],
                            "silhouette_score": T["col_silhouette"],
                        }),
                        use_container_width=True, height=340,
                        column_config={
                            T["col_silhouette"]: st.column_config.NumberColumn(format="%.4f"),
                        },
                    )

                with c2:
                    if terms is not None:
                        clusters = sorted(terms["cluster"].unique())
                        sel_clust = st.selectbox(T["select_cluster"], clusters,
                                                 key="style_clust")
                        sub = terms[terms["cluster"] == sel_clust].head(15)
                        st.caption(T["cluster_terms_desc"])
                        st.plotly_chart(
                            fig_hbar(sub, "tfidf_mean", "term",
                                     T["cluster_terms_title"], h=360,
                                     xlabel=T["x_tfidf"]),
                            use_container_width=True,
                        )
            else:
                st.info(T["no_style"])

        # ── 8. DEPENDENCY HIERARCHY ───────────────────────────────────────────────
        with st.expander("📖 " + T["sec_dependency"]):

            dep      = csv("dependency_hierarchy/dependency_counts.csv")
            dep_book = csv("dependency_hierarchy/dependency_by_book.csv")

            if dep is not None:
                c1, c2 = st.columns(2)

                with c1:
                    dep_top = dep[dep["dependency"] != "punct"].head(20).copy()
                    st.caption(T["dep_bar_desc"])
                    st.plotly_chart(
                        fig_hbar(dep_top, "count", "dependency",
                                 T["dep_bar_title"], h=420,
                                 xlabel=T["x_count"], ylabel=T["x_relation"]),
                        use_container_width=True,
                    )

                with c2:
                    if dep_book is not None:
                        excl2 = {"file_name", "total"}
                        d_cols = [c for c in dep_book.columns if c not in excl2]
                        _n_dep = st.slider(T["top_n_slider"], 5, min(30, len(d_cols)),
                                           min(15, len(d_cols)), key="hm_dep_n")
                        _dep_hm = _top_n_cols(dep_book[["file_name"] + d_cols], "file_name", _n_dep)
                        st.caption(T["dep_heatmap_desc"])
                        st.plotly_chart(
                            fig_heatmap(_dep_hm, "file_name",
                                        T["dep_heatmap_title"], h=420),
                            use_container_width=True,
                        )

            complexity_df = csv("dependency_hierarchy/complexity_by_book.csv")
            if complexity_df is not None:
                st.divider()
                cplx = complexity_df.copy()
                cplx["book"] = _bkr_book(
                    cplx["file_name"]
                    .str.replace("bible_BKR_", "", regex=False)
                    .str.replace(".txt", "", regex=False))
                st.caption(T["complexity_desc"])
                c1, c2 = st.columns(2)
                with c1:
                    st.plotly_chart(
                        fig_hbar(cplx, "avg_tree_depth", "book",
                                 T["complexity_title"], h=340,
                                 xlabel=T["x_depth"], ylabel=T["x_book"]),
                        use_container_width=True,
                    )
                with c2:
                    st.plotly_chart(
                        fig_hbar(cplx, "avg_clause_count", "book",
                                 T["complexity_title"], h=340,
                                 xlabel=T["x_clauses"], ylabel=T["x_book"]),
                        use_container_width=True,
                    )

        # ── 9. VERBAL RELATIONS ───────────────────────────────────────────────────
        with st.expander("📖 " + T["sec_verbal"]):

            vrel_cnt  = csv("verbal_relations_analytics/relation_type_counts.csv")
            vrel_conf = csv("verbal_relations_analytics/confidence_by_relation.csv")
            vrel_book = csv("verbal_relations_analytics/relations_by_book.csv")

            c1, c2 = st.columns(2)

            with c1:
                if vrel_cnt is not None:
                    d = vrel_cnt.sort_values("count", ascending=False).copy()
                    d.columns = ["_raw", T["x_count"]]
                    d[T["x_relation"]] = d["_raw"].map(VVT).fillna(d["_raw"])
                    st.caption(T["verbal_types_desc"])
                    st.plotly_chart(
                        fig_hbar(d, T["x_count"], T["x_relation"],
                                 T["verbal_types_title"], h=380,
                                 xlabel=T["x_count"], ylabel=T["x_relation"]),
                        use_container_width=True,
                    )

            with c2:
                if vrel_conf is not None:
                    d = vrel_conf.sort_values("avg_confidence", ascending=False).copy()
                    d["_raw"] = d["relation_type"]
                    d[T["x_relation"]] = d["_raw"].map(VVT).fillna(d["_raw"])
                    d = d.rename(columns={"avg_confidence": T["x_confidence"]})
                    st.caption(T["verbal_conf_desc"])
                    st.plotly_chart(
                        fig_hbar(d, T["x_confidence"], T["x_relation"],
                                 T["verbal_conf_title"], h=380,
                                 xlabel=T["x_confidence"], ylabel=T["x_relation"]),
                        use_container_width=True,
                    )

            if vrel_book is not None:
                excl_v = {"file_name", "total"}
                v_cols = [c for c in vrel_book.columns if c not in excl_v]
                hm3 = vrel_book[["file_name"] + v_cols].copy()
                hm3 = hm3.rename(columns={c: VVT.get(c, c) for c in v_cols})
                if len(v_cols) > 5:
                    _n_vrel = st.slider(T["top_n_slider"], 5, min(30, len(v_cols)),
                                        min(9, len(v_cols)), key="hm_vrel_n")
                    hm3 = _top_n_cols(hm3, "file_name", _n_vrel)
                st.caption(T["verbal_book_heatmap_desc"])
                st.plotly_chart(
                    fig_heatmap(hm3, "file_name", T["verbal_book_heatmap_title"], h=420),
                    use_container_width=True,
                )

        # ── 10. TAXONOMY ANALYTICS ────────────────────────────────────────────────
        with st.expander("📖 " + T["sec_taxonomy"]):

            tax_class   = csv("taxonomy_analytics/skinner_class_counts.csv")
            tax_dial    = csv("taxonomy_analytics/dialogue_density_by_book.csv")
            tax_control = csv("taxonomy_analytics/control_role_counts.csv")

            c1, c2 = st.columns(2)

            with c1:
                if tax_class is not None:
                    d = tax_class.sort_values("count", ascending=False).copy()
                    d.columns = ["_raw", T["x_count"]]
                    d[T["x_class"]] = d["_raw"].map(VSK).fillna(d["_raw"])
                    st.caption(T["tax_class_desc"])
                    st.plotly_chart(
                        fig_hbar(d, T["x_count"], T["x_class"],
                                 T["tax_class_title"], h=320,
                                 xlabel=T["x_count"], ylabel=T["x_class"]),
                        use_container_width=True,
                    )

            with c2:
                if tax_control is not None:
                    d = tax_control.sort_values("count", ascending=False).copy()
                    d.columns = ["_raw", T["x_count"]]
                    d[T["x_class"]] = d["_raw"].map(VCR).fillna(d["_raw"])
                    st.caption(T["tax_control_desc"])
                    st.plotly_chart(
                        fig_hbar(d, T["x_count"], T["x_class"],
                                 T["tax_control_title"], h=280,
                                 xlabel=T["x_count"], ylabel=T["x_class"]),
                        use_container_width=True,
                    )

            if tax_dial is not None:
                d = tax_dial.copy()
                d["book"] = _bkr_book(
                    d["file_name"]
                    .str.replace("bible_BKR_", "", regex=False)
                    .str.replace(".txt", "", regex=False))
                d = d.sort_values("dialogue_density", ascending=True)
                st.caption(T["tax_dialogue_desc"])
                fig = px.bar(d, x="dialogue_density", y="book",
                             orientation="h",
                             title=T["tax_dialogue_title"],
                             color_discrete_sequence=["#3a86ff"])
                fig.update_xaxes(title_text=T["x_density"])
                fig.update_yaxes(title_text=T["x_book"])
                fig.update_layout(showlegend=False, height=340, **_LAYOUT)
                st.plotly_chart(fig, use_container_width=True)

            tact_auto = csv("taxonomy_analytics/tact_vs_autoclitic_by_book.csv")
            if tact_auto is not None:
                st.divider()
                ta = tact_auto.copy()
                ta["book"] = _bkr_book(
                    ta["file_name"]
                    .str.replace("bible_BKR_", "", regex=False)
                    .str.replace(".txt", "", regex=False))
                st.caption(T["tact_autoclitic_desc"])
                fig_ta = go.Figure()
                fig_ta.add_bar(name="tact",      x=ta["book"], y=ta["tact_ratio"],
                               marker_color="#3a86ff")
                fig_ta.add_bar(name="autoclitic", x=ta["book"], y=ta["autoclitic_ratio"],
                               marker_color="#8338ec")
                fig_ta.update_layout(
                    barmode="group",
                    title=T["tact_autoclitic_title"],
                    xaxis_title=T["x_book"],
                    yaxis_title=T["x_ratio"],
                    height=360, **_LAYOUT,
                )
                st.plotly_chart(fig_ta, use_container_width=True)

        # ── 11. SEMANTIC WORD RELATIONS ───────────────────────────────────────────
        with st.expander("📖 " + T["sec_word_rel"]):

            top_pmi  = csv("word_relations_analytics/top_pmi_relations.csv")
            most_con = csv("word_relations_analytics/most_connected_words.csv")

            if top_pmi is None and most_con is None:
                st.info(T["no_word_rel"])
            else:
                c1, c2 = st.columns(2)

                with c1:
                    if top_pmi is not None:
                        st.caption(T["top_pmi_desc"])
                        display_pmi = top_pmi.head(25).rename(columns={
                            "word1":      T["top_pmi_word1"],
                            "word2":      T["top_pmi_word2"],
                            "pair_count": T["top_pmi_count"],
                            "pmi":        T["top_pmi_pmi"],
                        })
                        st.dataframe(display_pmi, use_container_width=True, height=420,
                                     column_config={
                                         T["top_pmi_pmi"]: st.column_config.NumberColumn(format="%.2f"),
                                     })

                with c2:
                    if most_con is not None:
                        d = most_con.head(25).copy()
                        d.columns = [T["x_word"], T["x_connections"]]
                        st.caption(T["most_connected_desc"])
                        st.plotly_chart(
                            fig_hbar(d, T["x_connections"], T["x_word"],
                                     T["most_connected_title"], h=420,
                                     xlabel=T["x_connections"], ylabel=T["x_word"]),
                            use_container_width=True,
                        )

        # ── 12. CORPUS DENSITY ────────────────────────────────────────────────────
        with st.expander("📖 " + T["sec_corpus_density"]):

            corp_dens = csv("religious_elements/combined_density_by_book.csv")

            if corp_dens is not None:
                s_cols = [c for c in corp_dens.columns
                          if c.endswith("_sentence_density")]
                dn = corp_dens[["file_name"] + s_cols].copy()
                dn.columns = (
                    ["file_name"] +
                    [c.replace("_sentence_density", "") for c in s_cols]
                )
                st.caption(T["corpus_density_desc"])
                st.plotly_chart(
                    fig_heatmap(dn, "file_name",
                                T["corpus_density_title"],
                                h=420, fmt="%{z:.2f}"),
                    use_container_width=True,
                )
            else:
                st.info("—")

        # ── 13. TEXT PATTERNS ─────────────────────────────────────────────────────
        with st.expander("📖 " + T["sec_patterns"]):

            ref_df = load_refined(lang)
            if ref_df is not None:
                ref_df = ref_df.copy()
                ref_df["book"] = _bkr_book(ref_df["book"])

            if ref_df is None:
                st.info(T["no_patterns"])
            else:
                # ── Wordcloud ─────────────────────────────────────────────────────
                st.caption(T["wordcloud_desc"])
                sentences_tuple = tuple(db_df["sentence"].dropna().tolist())
                wc_bytes = compute_wordcloud_img(sentences_tuple)
                st.image(wc_bytes, use_container_width=True)

                st.divider()

                # ── Bigrams + Trigrams ────────────────────────────────────────────
                c1, c2 = st.columns(2)

                with c1:
                    bi_df = compute_ngrams(sentences_tuple, 2, 20)
                    if not bi_df.empty:
                        st.caption(T["bigrams_desc"])
                        st.plotly_chart(
                            fig_hbar(bi_df, "count", "ngram",
                                     T["bigrams_title"], h=480,
                                     xlabel=T["x_frequency"], ylabel=T["x_ngram"]),
                            use_container_width=True,
                        )

                with c2:
                    tri_df = compute_ngrams(sentences_tuple, 3, 15)
                    if not tri_df.empty:
                        st.caption(T["trigrams_desc"])
                        st.plotly_chart(
                            fig_hbar(tri_df, "count", "ngram",
                                     T["trigrams_title"], h=480,
                                     xlabel=T["x_frequency"], ylabel=T["x_ngram"]),
                            use_container_width=True,
                        )

                st.divider()

                # ── TF-IDF heatmap lemma × book ───────────────────────────────────
                lemmas_by_book = (
                    ref_df.groupby("book")["lemmas"]
                    .apply(lambda x: " ".join(x.dropna()))
                )
                lemmas_items = tuple(sorted(lemmas_by_book.items()))
                tfidf_df = compute_tfidf_heatmap(lemmas_items, top_n=35)

                if not tfidf_df.empty:
                    st.caption(T["tfidf_heatmap_desc"])
                    st.plotly_chart(
                        fig_heatmap(tfidf_df, "book",
                                    T["tfidf_heatmap_title"], h=460,
                                    fmt="%{z:.2f}"),
                        use_container_width=True,
                    )

        # ── 14. SEMANTIC ANALYSIS ─────────────────────────────────────────────────
        with st.expander("📖 " + T["sec_semantics"]):

            ref_df2 = load_refined(lang)
            verb_df = load_verbal_full(lang)
            if ref_df2 is not None:
                ref_df2 = ref_df2.copy()
                ref_df2["book"] = _bkr_book(ref_df2["book"])
            if verb_df is not None:
                verb_df = verb_df.copy()
                verb_df["book"] = _bkr_book(verb_df["book"])

            if ref_df2 is None:
                st.info(T["no_db"])
            else:
                # ── Radar chart: semantic clusters per book ────────────────────────
                pivot = (
                    ref_df2.groupby(["book", "semantic_cluster"])
                    .size()
                    .unstack(fill_value=0)
                )
                pivot_norm   = pivot.div(pivot.sum(axis=1), axis=0)
                clusters_raw = list(pivot_norm.columns)
                clusters_t   = [VSC.get(c, c) for c in clusters_raw]
                pivot_norm.columns = clusters_t

                st.caption(T["radar_desc"])
                colors = px.colors.qualitative.Plotly
                fig_radar = go.Figure()
                for i, book in enumerate(pivot_norm.index):
                    vals = pivot_norm.loc[book].tolist()
                    vals_closed = vals + [vals[0]]
                    cats_closed = clusters_t + [clusters_t[0]]
                    fig_radar.add_trace(go.Scatterpolar(
                        r=vals_closed, theta=cats_closed,
                        fill="toself", name=book,
                        line_color=colors[i % len(colors)],
                        opacity=0.75,
                    ))
                fig_radar.update_layout(
                    title=T["radar_title"],
                    polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                    height=500, **_LAYOUT,
                )
                st.plotly_chart(fig_radar, use_container_width=True)

                st.divider()

                # ── Antithetical sentences ─────────────────────────────────────────
                if verb_df is not None:
                    anti = verb_df[verb_df["local_pattern"] == "negated_statement"].copy()
                    c1, c2 = st.columns(2)

                    with c1:
                        anti_cnt = (
                            anti.groupby("book").size()
                            .reset_index(name=T["x_count"])
                            .sort_values(T["x_count"], ascending=False)
                        )
                        anti_cnt.columns = [T["x_book"], T["x_count"]]
                        st.caption(T["antithetical_count_desc"])
                        st.plotly_chart(
                            fig_hbar(anti_cnt, T["x_count"], T["x_book"],
                                     T["antithetical_count_title"], h=320,
                                     xlabel=T["x_count"], ylabel=T["x_book"]),
                            use_container_width=True,
                        )

                    with c2:
                        st.caption(T["antithetical_desc"])
                        sel_book = _grouped_book_selectbox(
                            "anti", sorted(anti["book"].unique().tolist())
                        )
                        view_anti = anti if sel_book is None else anti[anti["book"] == sel_book]
                        st.dataframe(
                            view_anti[["book", "sentence"]].head(40).rename(
                                columns={"book": T["x_book"],
                                         "sentence": T["col_sentence"]}
                            ),
                            use_container_width=True, height=300,
                            column_config={
                                T["col_sentence"]: st.column_config.TextColumn(width="large"),
                            },
                        )

                st.divider()

                # ── Lexical reinforcement per book ────────────────────────────────
                lemmas_items2 = tuple(
                    (row["book"], row["lemmas"])
                    for _, row in ref_df2[["book", "lemmas"]].iterrows()
                )
                reinf_df = compute_lexical_reinforcement(lemmas_items2)

                if not reinf_df.empty:
                    reinf_df_plot = reinf_df.copy()
                    reinf_df_plot.columns = [T["x_book"], T["x_reinforcement"]]
                    st.caption(T["lexical_reinf_desc"])
                    st.plotly_chart(
                        fig_hbar(reinf_df_plot, T["x_reinforcement"], T["x_book"],
                                 T["lexical_reinf_title"], h=320,
                                 xlabel=T["x_reinforcement"], ylabel=T["x_book"]),
                        use_container_width=True,
                    )

        # ── 15. PIPELINE QUALITY ──────────────────────────────────────────────────
        with st.expander("📖 " + T["sec_quality"]):

            st.caption(T["quality_overall_desc"])

            # ── Overall confidence bands ──────────────────────────────────────────
            conf_s = db_df["confidence"].dropna()
            band_low  = int((conf_s < 0.30).sum())
            band_mid  = int(((conf_s >= 0.30) & (conf_s < 0.60)).sum())
            band_high = int((conf_s >= 0.60).sum())

            c1, c2 = st.columns(2)

            with c1:
                bins_df = pd.DataFrame({
                    T["x_book"]: [T["conf_band_low"], T["conf_band_mid"], T["conf_band_high"]],
                    T["x_sentences"]: [band_low, band_mid, band_high],
                })
                clr_bins = {
                    T["conf_band_low"]:  "#e63946",
                    T["conf_band_mid"]:  "#f4a261",
                    T["conf_band_high"]: "#57cc99",
                }
                st.caption(T["conf_bins_desc"])
                fig_bins = px.bar(
                    bins_df, x=T["x_sentences"], y=T["x_book"],
                    orientation="h", color=T["x_book"],
                    color_discrete_map=clr_bins,
                    title=T["conf_bins_title"],
                )
                fig_bins.update_layout(showlegend=False, height=260, **_LAYOUT)
                st.plotly_chart(fig_bins, use_container_width=True)

            with c2:
                cov_book = csv("eval/coverage_by_book.csv")
                if cov_book is not None:
                    cov_plot = cov_book.copy()
                    cov_plot["book"] = _bkr_book(
                        cov_plot["book"]
                        .str.replace("bible_BKR_", "", regex=False)
                        .str.replace(".txt", "", regex=False))
                    cov_plot = cov_plot.sort_values("coverage_pct", ascending=True)
                    cov_plot.rename(columns={"coverage_pct": T["x_coverage"],
                                              "book": T["x_book"]}, inplace=True)
                    st.caption(T["coverage_book_desc"])
                    fig_cov = px.bar(
                        cov_plot, x=T["x_coverage"], y=T["x_book"],
                        orientation="h", title=T["coverage_book_title"],
                        color=T["x_coverage"],
                        color_continuous_scale=["#e63946", "#f4a261", "#57cc99"],
                        range_color=[85, 100],
                    )
                    fig_cov.update_layout(showlegend=False, height=320, **_LAYOUT)
                    st.plotly_chart(fig_cov, use_container_width=True)
                else:
                    st.info(T["no_eval"])

            st.divider()

            # ── Consistency (ambiguous lemmas) ────────────────────────────────────
            ambig = csv("eval/ambiguous_lemmas.csv")
            c1, c2 = st.columns(2)

            with c1:
                if ambig is not None:
                    total_lemmas = len(ambig) + max(1, len(ambig))
                    ambig_display = ambig.head(20).copy()
                    ambig_display["n_labels"] = ambig_display["labels"].str.count(r"\|") + 1
                    ambig_display = ambig_display.rename(columns={
                        "lemma":  T["col_lemma"],
                        "labels": T["col_classes"],
                        "n_labels": T["col_n_classes"],
                    })
                    st.caption(T["consistency_desc"])
                    st.dataframe(
                        ambig_display[[T["col_lemma"], T["col_classes"], T["col_n_classes"]]],
                        use_container_width=True, height=340,
                    )

            with c2:
                outliers = csv("eval/book_outliers.csv")
                if outliers is not None:
                    out_display = outliers.copy()
                    out_display["book"] = _bkr_book(
                        out_display["book"]
                        .str.replace("bible_BKR_", "", regex=False)
                        .str.replace(".txt", "", regex=False))
                    out_display = out_display.rename(columns={
                        "book":    T["x_book"],
                        "label":   T["col_label_q"],
                        "ratio":   T["x_ratio"],
                        "z_score": T["col_z_score"],
                    })
                    st.caption(T["outliers_desc"])
                    st.dataframe(
                        out_display,
                        use_container_width=True, height=200,
                        column_config={
                            T["x_ratio"]:    st.column_config.NumberColumn(format="%.3f"),
                            T["col_z_score"]: st.column_config.NumberColumn(format="%.2f"),
                        },
                    )
                else:
                    st.info(T["no_eval"])

            st.divider()

            # ── Sample sentences ──────────────────────────────────────────────────
            sample = csv("eval/random_sample.csv")
            if sample is not None:
                sample_display = sample.copy()
                sample_display["file_name"] = _bkr_book(
                    sample_display["file_name"]
                    .str.replace("bible_BKR_", "", regex=False)
                    .str.replace(".txt", "", regex=False))
                sample_display = sample_display.rename(columns={
                    "file_name":         T["x_book"],
                    "illocutionary_force": T["col_force"],
                    "primary_intention": T["col_intention"],
                    "confidence":        T["col_confidence"],
                    "sentence":          T["col_sentence"],
                })
                keep = [T["x_book"], T["col_force"], T["col_intention"],
                        T["col_confidence"], T["col_sentence"]]
                keep = [c for c in keep if c in sample_display.columns]
                st.caption(T["sample_desc"])
                st.dataframe(
                    sample_display[keep],
                    use_container_width=True, height=440,
                    column_config={
                        T["col_sentence"]:    st.column_config.TextColumn(width="large"),
                        T["col_confidence"]:  st.column_config.NumberColumn(format="%.2f"),
                    },
                )
            else:
                st.info(T["no_eval"])

        # ── 16. LINGUISTIC FEATURES ──────────────────────────────────────────────
        with st.expander("📖 " + T["sec_ling_features"]):

            _ling_cols = {
                "type_token_ratio", "has_coordination", "dative_present",
                "indirect_object_present", "adjective_count", "adverb_count",
                "pronoun_count",
            }
            if db_df is not None and _ling_cols.issubset(db_df.columns):

                _ldf = db_df.copy()
                _ldf["book"] = _bkr_book(_ldf["book"])

                # ── 1. TTR bar chart ──────────────────────────────────────────────
                st.caption(T["ling_ttr_desc"])
                _ttr = (
                    _ldf.groupby("book")["type_token_ratio"]
                    .mean()
                    .reset_index()
                    .sort_values("type_token_ratio", ascending=True)
                )
                _ttr.columns = [T["x_book"], T["col_ttr"]]
                st.plotly_chart(
                    fig_hbar(_ttr, T["col_ttr"], T["x_book"],
                             T["ling_ttr_title"], h=380,
                             xlabel=T["col_ttr"], ylabel=T["x_book"]),
                    use_container_width=True,
                )

                st.divider()

                # ── 2. Boolean syntactic features grouped bar ─────────────────────
                st.caption(T["ling_bool_desc"])
                _bool_agg = (
                    _ldf.groupby("book")[
                        ["has_coordination", "dative_present", "indirect_object_present"]
                    ]
                    .mean()
                    .mul(100)
                    .reset_index()
                    .sort_values("has_coordination", ascending=True)
                )
                _fig_bool = go.Figure()
                _fig_bool.add_trace(go.Bar(
                    name=T["lbl_coordination"],
                    x=_bool_agg["has_coordination"],
                    y=_bool_agg["book"],
                    orientation="h",
                    marker_color="#4895ef",
                ))
                _fig_bool.add_trace(go.Bar(
                    name=T["lbl_dative"],
                    x=_bool_agg["dative_present"],
                    y=_bool_agg["book"],
                    orientation="h",
                    marker_color="#f4a261",
                ))
                _fig_bool.add_trace(go.Bar(
                    name=T["lbl_iobj"],
                    x=_bool_agg["indirect_object_present"],
                    y=_bool_agg["book"],
                    orientation="h",
                    marker_color="#57cc99",
                ))
                _fig_bool.update_layout(
                    barmode="group",
                    title=T["ling_bool_title"],
                    xaxis_title="%",
                    height=420,
                    **_LAYOUT,
                )
                st.plotly_chart(_fig_bool, use_container_width=True)

                st.divider()

                # ── 3. POS counts grouped bar ────────────────────────────────────
                st.caption(T["ling_pos_desc"])
                _pos_agg = (
                    _ldf.groupby("book")[
                        ["adjective_count", "adverb_count", "pronoun_count"]
                    ]
                    .mean()
                    .reset_index()
                    .sort_values("adjective_count", ascending=True)
                )
                _fig_pos = go.Figure()
                _fig_pos.add_trace(go.Bar(
                    name=T["lbl_adj"],
                    x=_pos_agg["adjective_count"],
                    y=_pos_agg["book"],
                    orientation="h",
                    marker_color="#7b2d8b",
                ))
                _fig_pos.add_trace(go.Bar(
                    name=T["lbl_adv"],
                    x=_pos_agg["adverb_count"],
                    y=_pos_agg["book"],
                    orientation="h",
                    marker_color="#e63946",
                ))
                _fig_pos.add_trace(go.Bar(
                    name=T["lbl_pron"],
                    x=_pos_agg["pronoun_count"],
                    y=_pos_agg["book"],
                    orientation="h",
                    marker_color="#ffd166",
                ))
                _fig_pos.update_layout(
                    barmode="group",
                    title=T["ling_pos_title"],
                    height=420,
                    **_LAYOUT,
                )
                st.plotly_chart(_fig_pos, use_container_width=True)

                st.divider()

                # ── 4. Most formulaic sentences table ────────────────────────────
                st.caption(T["ling_formulaic_desc"])
                _form = (
                    _ldf[_ldf["sentence"].str.split().str.len() >= 5]
                    .nsmallest(15, "type_token_ratio")
                    [["book", "sentence", "type_token_ratio"]]
                    .rename(columns={
                        "book":             T["x_book"],
                        "sentence":         T["col_sentence"],
                        "type_token_ratio": T["col_ttr"],
                    })
                )
                st.dataframe(
                    _form,
                    use_container_width=True,
                    height=380,
                    column_config={
                        T["col_sentence"]: st.column_config.TextColumn(width="large"),
                        T["col_ttr"]:      st.column_config.NumberColumn(format="%.3f"),
                    },
                )

            else:
                st.info(T["no_db"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — RESULTS
# ══════════════════════════════════════════════════════════════════════════════

with tab_results:

    if "adf" not in st.session_state:
        st.info(T["results_empty"])
        st.stop()

    _df       = st.session_state["adf"]
    _rel_df   = st.session_state.get("adf_rel", pd.DataFrame())
    _ref_df   = st.session_state.get("adf_ref", pd.DataFrame())
    _units    = st.session_state.get("adf_units", [])
    _ldat     = st.session_state.get("adf_lemmas", [])
    _src      = st.session_state.get("adf_source", "—")
    _corpus_id = st.session_state.get("adf_corpus_id", "")

    # ── source badge ─────────────────────────────────────────────────────────
    _n_chapters = len(_units) if _units else 1
    _seg_mode   = st.session_state.get("adf_seg_mode", _units[0].unit_type if _units else "document")
    # Derive human-readable labels from the actual segmentation tier
    if _seg_mode == "chapter":
        _unit_label_sg = "kapitola"
        _unit_label_pl = "kapitol"
        _unit_metric   = T.get("metric_chapters", "Kapitol")
        _col_unit      = "Kapitola"
    elif _seg_mode == "section":
        _unit_label_sg = "sekce"
        _unit_label_pl = "sekcí"
        _unit_metric   = "Sekcí"
        _col_unit      = "Sekce"
    else:
        _unit_label_sg = "dokument"
        _unit_label_pl = "dokumentů"
        _unit_metric   = "Dokument"
        _col_unit      = "Dokument"
    _hdr_col, _btn_col = st.columns([3, 1])
    with _hdr_col:
        st.subheader(T["results_title"])
        st.caption(
            f"📁 **Nahraný text** — `{_src}` · {_n_chapters} "
            f"{_unit_label_sg if _n_chapters == 1 else _unit_label_pl}"
        )

    # ── headline metrics ──────────────────────────────────────────────────────
    _total   = len(_df)
    _classif = int((_df["primary_intention"] != "unclassified").sum()) if "primary_intention" in _df.columns else 0
    _mconf   = float(_df["confidence"].mean()) if "confidence" in _df.columns and _total else 0.0
    _c1, _c2, _c3, _c4 = st.columns(4)
    _c1.metric(T["metric_sentences"], _total)
    _c2.metric(T["metric_classified"], f"{_classif}/{_total}",
               f"{100*_classif/_total:.0f} %" if _total else "—")
    _c3.metric(T["metric_confidence"], f"{_mconf:.2f}")
    _c4.metric(_unit_metric, _n_chapters)
    st.divider()

    # ── 0. Chapter overview ───────────────────────────────────────────────────
    if _units and len(_units) > 1 and not _df.empty and "unit_id" in _df.columns:
        _overview_title = (
            "📤 📑 Přehled kapitol" if _seg_mode == "chapter"
            else ("📤 📑 Přehled sekcí" if _seg_mode == "section" else "📤 📑 Přehled")
        )
        with st.expander(_overview_title, expanded=False):
            _chap_rows = []
            for _u in _units:
                _u_df = _df[_df["unit_id"] == _u.unit_id]
                _u_total = len(_u_df)
                _u_conf  = float(_u_df["confidence"].mean()) if _u_total and "confidence" in _u_df.columns else 0.0
                _u_dom   = (
                    _u_df["primary_intention"].value_counts().index[0]
                    if _u_total and "primary_intention" in _u_df.columns
                    else "—"
                )
                _chap_rows.append({
                    "Jednotka": _u.display_name,
                    "Věty": _u_total,
                    "Průměrná jistota": round(_u_conf, 3),
                    "Dominantní záměr": _u_dom,
                })
            if _chap_rows:
                st.dataframe(pd.DataFrame(_chap_rows), use_container_width=True, height=320)

    # ── PDF export ────────────────────────────────────────────────────────────
    with _btn_col:
        st.write("")  # vertical alignment spacer
        if st.button(T["export_pdf"], key="pdf_btn", use_container_width=True):
            with st.spinner(T["pdf_generating"]):
                try:
                    _pdf_bytes = generate_pdf_report(
                        df=_df,
                        lemmas_data=_ldat,
                        lang=lang,
                        pipeline_lang=pipeline_lang,
                        translations=T,
                        vi=VI, vf=VF, vs=VS, vsk=VSK,
                        int_clr=INTENTION_CLR,
                        frc_clr=FORCE_CLR,
                        str_clr=STRATEGY_CLR,
                        session=dict(st.session_state),
                    )
                    st.session_state["_pdf_cache"] = _pdf_bytes
                    st.rerun()
                except Exception as _pdf_err:
                    st.error(f"{T['pdf_error']}: {_pdf_err}")

    if "_pdf_cache" in st.session_state:
        st.success(T["pdf_ready"])
        st.download_button(
            label=T["export_pdf"],
            data=st.session_state["_pdf_cache"],
            file_name=T["pdf_filename"],
            mime="application/pdf",
            key="pdf_dl",
        )

    # ── 1. Q. Skinner — core classification ──────────────────────────────────
    if st.session_state.get("sel_q_skinner", True):
        with st.expander(f"📤 ⚡ {T['ana_qs_name']}", expanded=True):
            _r1, _r2 = st.columns(2)
            with _r1:
                _ic = _df["primary_intention"].value_counts().reset_index()
                _ic.columns = ["_raw", T["x_count"]]
                _ic[T["x_intention"]] = _ic["_raw"].map(VI).fillna(_ic["_raw"])
                st.caption(T["intent_pie_desc"])
                st.plotly_chart(
                    fig_hbar(_ic, T["x_count"], T["x_intention"],
                             T["intent_pie_title"], INT_CLR,
                             xlabel=T["x_count"]),
                    use_container_width=True,
                )
            with _r2:
                _sc = _df["primary_strategy"].value_counts().reset_index()
                _sc.columns = ["_raw", T["x_count"]]
                _sc[T["x_strategy"]] = _sc["_raw"].map(VS).fillna(_sc["_raw"])
                _sc = _sc[_sc["_raw"] != "unclassified"].head(10)
                if not _sc.empty:
                    st.caption(T["strategy_bar_desc"])
                    st.plotly_chart(
                        fig_hbar(_sc, T["x_count"], T["x_strategy"],
                                 T["strategy_bar_title"], STR_CLR,
                                 xlabel=T["x_count"]),
                        use_container_width=True,
                    )

            _r3, _r4 = st.columns(2)
            with _r3:
                _fc = _df["illocutionary_force"].value_counts().reset_index()
                _fc.columns = ["_raw", T["x_count"]]
                _fc[T["x_force"]] = _fc["_raw"].map(VF).fillna(_fc["_raw"])
                st.caption(T["force_pie_desc"])
                st.plotly_chart(
                    fig_pie(_fc, T["x_force"], T["x_count"],
                            T["force_pie_title"], FRC_CLR),
                    use_container_width=True,
                )
            with _r4:
                _dfb = _df.copy()
                _dfb[T["x_intention"]] = (_dfb["primary_intention"]
                                          .map(VI).fillna(_dfb["primary_intention"]))
                st.caption(T["conf_hist_desc"])
                st.plotly_chart(
                    fig_box_confidence(_dfb, T["x_intention"], "confidence",
                                       T["conf_hist_title"], INT_CLR),
                    use_container_width=True,
                )

            # Sentence table
            st.divider()
            st.subheader(T["section_sentence_table"])
            _fi, _fs = st.columns(2)
            with _fi:
                _sel_int = st.multiselect(T["filter_intention"],
                                          sorted(_df["primary_intention"].unique()),
                                          key="res_fi")
            with _fs:
                _sel_str = st.multiselect(T["filter_strategy"],
                                          sorted(_df["primary_strategy"].unique()),
                                          key="res_fs")
            _view = _df.copy()
            if _sel_int: _view = _view[_view["primary_intention"].isin(_sel_int)]
            if _sel_str: _view = _view[_view["primary_strategy"].isin(_sel_str)]
            _DISP = ["sentence_id","sentence","primary_intention","secondary_intention",
                     "illocutionary_force","primary_strategy","confidence","reason",
                     "locution","convention","political_vocabulary"]
            _show = [c for c in _DISP if c in _view.columns]
            st.dataframe(
                _view[_show].rename(columns={
                    "sentence_id": T["col_id"], "sentence": T["col_sentence"],
                    "primary_intention": T["col_intention"],
                    "secondary_intention": T["col_2nd_intention"],
                    "illocutionary_force": T["col_force"],
                    "primary_strategy": T["col_strategy"],
                    "confidence": T["col_confidence"], "reason": T["col_reason"],
                    "locution": T["col_locution"], "convention": T["col_convention"],
                    "political_vocabulary": T["col_pol_vocab"],
                }),
                use_container_width=True, height=400,
                column_config={
                    T["col_sentence"]: st.column_config.TextColumn(width="large"),
                    T["col_confidence"]: st.column_config.NumberColumn(format="%.2f"),
                },
            )
            st.download_button(T["download_csv"],
                               _view.to_csv(index=False).encode(),
                               "skinner_analysis.csv", "text/csv",
                               key="res_dl")

            # ── Secondary intention ───────────────────────────────────────────
            st.divider()
            st.subheader(T.get("secondary_intent_title", "Sekundárny zámer"))
            _qs_r1, _qs_r2 = st.columns(2)
            with _qs_r1:
                _si = (_df["secondary_intention"].dropna()
                       .value_counts().reset_index())
                _si.columns = ["_raw", T["x_count"]]
                _si[T["x_intention"]] = _si["_raw"].map(VI).fillna(_si["_raw"])
                st.caption(T.get("secondary_intent_desc", ""))
                if not _si.empty:
                    st.plotly_chart(
                        fig_hbar(_si, T["x_count"], T["x_intention"],
                                 T.get("secondary_intent_title","Secondary intention"),
                                 INT_CLR, xlabel=T["x_count"]),
                        use_container_width=True,
                    )

            # ── Secondary strategy ────────────────────────────────────────────
            with _qs_r2:
                _ss = (_df["secondary_strategy"].dropna()
                       .value_counts().reset_index())
                _ss.columns = ["_raw", T["x_count"]]
                _ss[T["x_strategy"]] = _ss["_raw"].map(VS).fillna(_ss["_raw"])
                if not _ss.empty:
                    st.caption(T.get("strategy_bar_desc", ""))
                    st.plotly_chart(
                        fig_hbar(_ss, T["x_count"], T["x_strategy"],
                                 T.get("secondary_intent_title","Secondary strategy") + " (2.)",
                                 STR_CLR, xlabel=T["x_count"]),
                        use_container_width=True,
                    )

            # ── Convention types ──────────────────────────────────────────────
            st.divider()
            st.subheader(T.get("sec_strategy", "Konvencia / Stratégia"))
            _qs_r3, _qs_r4 = st.columns(2)
            with _qs_r3:
                _cv = (_df["convention"].dropna()
                       .value_counts().head(15).reset_index())
                _cv.columns = ["convention", T["x_count"]]
                if not _cv.empty:
                    st.caption(T.get("all_strategies_desc", "Top 15 convention types"))
                    _fig_cv = px.bar(
                        _cv.sort_values(T["x_count"], ascending=True),
                        x=T["x_count"], y="convention", orientation="h",
                        title="Convention types (top 15)",
                        color_discrete_sequence=["#8338ec"],
                    )
                    _fig_cv.update_layout(showlegend=False, height=420, **_LAYOUT)
                    st.plotly_chart(_fig_cv, use_container_width=True)

            # ── Political vocabulary ──────────────────────────────────────────
            with _qs_r4:
                import re as _re
                _pv_raw = (_df["political_vocabulary"].dropna()
                           .str.split(",").explode().str.strip()
                           .str.extract(r'^([^\[]+)')[0].str.strip()
                           .value_counts().head(15).reset_index())
                _pv_raw.columns = ["term", T["x_count"]]
                if not _pv_raw.empty:
                    st.caption(T.get("pvoc_desc", "Political vocabulary"))
                    _fig_pv = px.bar(
                        _pv_raw.sort_values(T["x_count"], ascending=True),
                        x=T["x_count"], y="term", orientation="h",
                        title=T.get("pvoc_title", "Political vocabulary"),
                        color_discrete_sequence=["#3a86ff"],
                    )
                    _fig_pv.update_layout(showlegend=False, height=420, **_LAYOUT)
                    st.plotly_chart(_fig_pv, use_container_width=True)

            # ── Anti-anachronism ──────────────────────────────────────────────
            st.divider()
            st.subheader("Anti-anachronizmus")
            _qs_r5, _qs_r6 = st.columns(2)
            _aa_col = "anti_anachronism"
            if _aa_col in _df.columns:
                _flagged = (_df[_aa_col] != "none_flagged").sum()
                _total_aa = len(_df)
                with _qs_r5:
                    _aa_pie = pd.DataFrame({
                        "status": ["bez príznaku", "s príznakom"],
                        T["x_count"]: [_total_aa - _flagged, _flagged],
                    })
                    _fig_aa = px.pie(
                        _aa_pie, names="status", values=T["x_count"],
                        title=f"Anti-anachronizmus — {_flagged} viet ({100*_flagged/_total_aa:.1f}%)",
                        color="status",
                        color_discrete_map={"bez príznaku": "#76B7B2", "s príznakom": "#E15759"},
                        hole=0.35,
                    )
                    _fig_aa.update_layout(height=360, **_LAYOUT)
                    st.plotly_chart(_fig_aa, use_container_width=True)

                with _qs_r6:
                    import re as _re2
                    _terms = []
                    for _v in _df[_aa_col].dropna():
                        if _v == "none_flagged":
                            continue
                        for _chunk in str(_v).split(";"):
                            _m = _re2.match(r'\s*(\w+)\s*:', _chunk.strip())
                            if _m:
                                _terms.append(_m.group(1).strip())
                    if _terms:
                        from collections import Counter as _Counter
                        _tc = pd.DataFrame(
                            _Counter(_terms).most_common(12),
                            columns=["term", T["x_count"]],
                        )
                        _fig_tc = px.bar(
                            _tc.sort_values(T["x_count"], ascending=True),
                            x=T["x_count"], y="term", orientation="h",
                            title="Anachronické termíny — frekvencia",
                            color_discrete_sequence=["#E15759"],
                        )
                        _fig_tc.update_layout(showlegend=False, height=360, **_LAYOUT)
                        st.plotly_chart(_fig_tc, use_container_width=True)

                # Sample flagged sentences
                _aa_sample = (_df[_df[_aa_col] != "none_flagged"]
                              [["sentence", "primary_intention", _aa_col]]
                              .head(10))
                if not _aa_sample.empty:
                    st.caption("Vzorka viet s príznakom anachronizmu")
                    st.dataframe(_aa_sample, use_container_width=True, height=280)

            # ── Chapter-level intention heatmap ───────────────────────────────
            if _units and len(_units) >= 3 and "unit_id" in _df.columns and "primary_intention" in _df.columns:
                st.divider()
                _int_pivot = (
                    _df.groupby(["unit_id", "primary_intention"])
                    .size()
                    .reset_index(name="count")
                )
                if not _int_pivot.empty:
                    _int_wide = _int_pivot.pivot(
                        index="unit_id", columns="primary_intention", values="count"
                    ).fillna(0).reset_index()
                    _uid2name_qs = {u.unit_id: u.display_name for u in _units}
                    _int_wide["unit_id"] = _int_wide["unit_id"].map(_uid2name_qs).fillna(_int_wide["unit_id"])
                    _int_wide = _int_wide.rename(columns={"unit_id": _col_unit})
                    st.caption(T.get("intent_book_heatmap_desc", "Záměry podle kapitol"))
                    st.plotly_chart(
                        fig_heatmap(_int_wide, _col_unit,
                                    T.get("intent_book_heatmap_title", "Záměry podle kapitol"),
                                    h=max(300, 30 * len(_units))),
                        use_container_width=True,
                    )
            elif _units and len(_units) < 3 and "primary_intention" in _df.columns:
                st.info("Kapitolová heatmapa vyžaduje alespoň 3 kapitoly.")

    # ── 2. B.F. Skinner ───────────────────────────────────────────────────────
    if st.session_state.get("sel_bf_skinner", True) and not _df.empty:
        with st.expander(f"📤 ⚡ {T['ana_bf_name']}"):
            st.caption(f"*[Nahraný text]*")
            if "skinner_class" in _df.columns:
                _bc1, _bc2 = st.columns(2)
                with _bc1:
                    _sk_counts = (_df["skinner_class"].value_counts()
                                  .reset_index())
                    _sk_counts.columns = ["_raw", T["x_count"]]
                    _sk_counts[T["x_class"]] = _sk_counts["_raw"].map(VSK).fillna(_sk_counts["_raw"])
                    st.caption(T["tax_class_desc"])
                    st.plotly_chart(
                        fig_hbar(_sk_counts, T["x_count"], T["x_class"],
                                 T["tax_class_title"], h=300,
                                 xlabel=T["x_count"]),
                        use_container_width=True,
                    )
                with _bc2:
                    if "control_role" in _df.columns:
                        _cr = _df["control_role"].value_counts().reset_index()
                        _cr.columns = ["role", T["x_count"]]
                        st.caption(T["tax_control_desc"])
                        st.plotly_chart(
                            fig_hbar(_cr, T["x_count"], "role",
                                     T["tax_control_title"], h=300,
                                     xlabel=T["x_count"]),
                            use_container_width=True,
                        )
                # Chapter-level tact vs autoclitic heatmap (if multiple chapters)
                if _units and len(_units) > 1 and "unit_id" in _df.columns:
                    st.divider()
                    _ta_rows = []
                    for _u in _units:
                        _ud = _df[_df["unit_id"] == _u.unit_id]
                        _t = len(_ud)
                        if _t == 0:
                            continue
                        _ta_rows.append({
                            _col_unit: _u.display_name,
                            "tact": (_ud["skinner_class"] == "tact").sum() / _t,
                            "autoclitic": (_ud["skinner_class"] == "autoclitic").sum() / _t,
                        })
                    if _ta_rows:
                        _ta_df2 = pd.DataFrame(_ta_rows)
                        _fig_ta2 = go.Figure()
                        _fig_ta2.add_bar(name="tact", x=_ta_df2[_col_unit],
                                         y=_ta_df2["tact"], marker_color="#3a86ff")
                        _fig_ta2.add_bar(name="autoclitic", x=_ta_df2[_col_unit],
                                         y=_ta_df2["autoclitic"], marker_color="#8338ec")
                        _fig_ta2.update_layout(barmode="group",
                                               title=T.get("tact_autoclitic_title",
                                                           "Tact vs Autoclitic podle kapitol"),
                                               height=320, **_LAYOUT)
                        st.caption(T.get("tact_autoclitic_desc", ""))
                        st.plotly_chart(_fig_ta2, use_container_width=True)
            else:
                st.info("Spusťte plnou analýzu pro zobrazení Skinnerovy taxonomie.")

    # ── 3. Verbálne vzťahy ────────────────────────────────────────────────────
    if st.session_state.get("sel_verbal", True):
        with st.expander(f"📤 ⚡ {T['ana_verbal_name']}"):
            st.caption(f"*[Nahraný text]*")
            if not _rel_df.empty and "local_pattern" in _rel_df.columns:
                _vr1, _vr2 = st.columns(2)
                with _vr1:
                    _vr_counts = _rel_df["local_pattern"].value_counts().reset_index()
                    _vr_counts.columns = ["_raw", T["x_count"]]
                    _vr_counts[T["x_relation"]] = _vr_counts["_raw"].map(VVT).fillna(_vr_counts["_raw"])
                    st.caption(T["verbal_types_desc"])
                    st.plotly_chart(
                        fig_hbar(_vr_counts, T["x_count"], T["x_relation"],
                                 T["verbal_types_title"], h=340,
                                 xlabel=T["x_count"]),
                        use_container_width=True,
                    )
                with _vr2:
                    if "confidence" in _rel_df.columns:
                        _vr_conf = _rel_df.copy()
                        _vr_conf[T["x_relation"]] = (
                            _vr_conf["local_pattern"].map(VVT).fillna(_vr_conf["local_pattern"])
                        )
                        st.caption(T["verbal_conf_desc"])
                        st.plotly_chart(
                            fig_box_confidence(_vr_conf, T["x_relation"], "confidence",
                                               T["verbal_conf_title"]),
                            use_container_width=True,
                        )
                # Chapter-level verbal relations heatmap
                if _units and len(_units) > 1 and "unit_id" in _rel_df.columns:
                    st.divider()
                    _vr_pivot = (
                        _rel_df.groupby(["unit_id", "local_pattern"])
                        .size()
                        .reset_index(name="count")
                    )
                    if not _vr_pivot.empty:
                        _vr_wide = _vr_pivot.pivot(
                            index="unit_id", columns="local_pattern", values="count"
                        ).fillna(0).reset_index()
                        # Map unit_id → display_name
                        _uid2name = {u.unit_id: u.display_name for u in _units}
                        _vr_wide["unit_id"] = _vr_wide["unit_id"].map(_uid2name).fillna(_vr_wide["unit_id"])
                        _vr_wide = _vr_wide.rename(columns={"unit_id": _col_unit})
                        st.caption(T.get("verbal_book_heatmap_desc", "Verbální vztahy podle kapitol"))
                        st.plotly_chart(
                            fig_heatmap(_vr_wide, _col_unit,
                                        T.get("verbal_book_heatmap_title",
                                              "Verbální vztahy podle kapitol"), h=400),
                            use_container_width=True,
                        )
            else:
                st.info("Spusťte plnou analýzu pro zobrazení verbálních vztahů.")

    # ── 4. Sémantika ──────────────────────────────────────────────────────────
    if st.session_state.get("sel_semantics", True) and _ldat:
        with st.expander(f"📤 ⚡ {T['ana_semantics_name']}"):
            from collections import Counter as _SC
            _STOP_S = {"být","ten","on","se","si","the","be","have","that","this",
                       "which","with","from","they","their","are","was","were",
                       "not","but","and","for","its","his","her","may","also"}
            _all_l: list = [t for _,ls in _ldat for t in ls.split()
                            if len(t)>2 and t.isalpha() and t not in _STOP_S]
            _fq = _SC(_all_l)
            _fq_df = pd.DataFrame(_fq.most_common(25), columns=["lemma","count"])
            if not _fq_df.empty:
                st.caption(T["ana_semantics_q"])
                st.plotly_chart(
                    fig_hbar(_fq_df, "count", "lemma", T["ana_semantics_name"],
                             h=480, xlabel=T["x_count"]),
                    use_container_width=True,
                )

    # ── 5. Náboženské elementy ────────────────────────────────────────────────
    if st.session_state.get("sel_religious", True) and _ldat:
        with st.expander(f"📤 ⚡ {T['ana_religious_name']}"):
            from t_config_tradition import TRADITIONS, PHILOSOPHICAL_INFLUENCES
            _ls = set(t for _,ls in _ldat for t in ls.split()
                      if len(t)>2 and t.isalpha())
            _tname = "christian_english" if pipeline_lang=="en" else "christian_czech"
            _elh = {el:len(_ls&lx) for el,lx in TRADITIONS.get(_tname,{}).items()
                    if _ls&lx}
            _phh = {ph:len(_ls&lx) for ph,lx in PHILOSOPHICAL_INFLUENCES.items()
                    if _ls&lx}
            _r3_el = T.get("rel_elements", {})
            _r3_ph = T.get("rel_philosophy", {})
            _re1, _re2 = st.columns(2)
            with _re1:
                if _elh:
                    _edf = pd.DataFrame(
                        sorted({_r3_el.get(k,k):v for k,v in _elh.items()}.items(),
                               key=lambda x:-x[1]),
                        columns=["element",T["x_count"]])
                    st.plotly_chart(
                        fig_hbar(_edf,T["x_count"],"element",
                                 T["element_coverage_title"],h=320,
                                 xlabel=T["x_count"]),
                        use_container_width=True,
                    )
                else: st.info("—")
            with _re2:
                if _phh:
                    _pdf2 = pd.DataFrame(
                        sorted({_r3_ph.get(k,k):v for k,v in _phh.items()}.items(),
                               key=lambda x:-x[1]),
                        columns=["influence",T["x_count"]])
                    st.plotly_chart(
                        fig_hbar(_pdf2,T["x_count"],"influence",
                                 T["philosophy_title"],h=320,
                                 xlabel=T["x_count"]),
                        use_container_width=True,
                    )
                else: st.info("—")

    # ── 6. Sieť slov ─────────────────────────────────────────────────────────
    if st.session_state.get("sel_network", False):
        with st.expander(f"📤 🕐 {T['ana_network_name']}"):
            st.caption(f"*[Nahraný text — výpočet živě]*")
            # Compute PMI in-memory from upload lemmas
            if _ldat:
                from collections import Counter as _PMICounter
                from math import log as _log
                _pmi_tokens = [t for _, ls in _ldat for t in str(ls).split()
                               if len(t) > 2 and t.isalpha()]
                _pmi_freq: dict = dict(_PMICounter(_pmi_tokens).most_common(500))
                _total_pmi = max(sum(_pmi_freq.values()), 1)
                _window_pairs: "_PMICounter" = _PMICounter()
                for _ii in range(len(_ldat)):
                    _win_toks = set()
                    for _, _ls_j in _ldat[max(0, _ii-2): _ii+3]:
                        _win_toks.update(_ls_j.split())
                    _win_list = sorted(_win_toks)
                    for _wi in range(len(_win_list)):
                        for _wj in range(_wi + 1, len(_win_list)):
                            if _win_list[_wi] in _pmi_freq and _win_list[_wj] in _pmi_freq:
                                _window_pairs[(_win_list[_wi], _win_list[_wj])] += 1
                _pmi_rows = []
                _pair_total = max(sum(_window_pairs.values()), 1)
                for (_w1, _w2), _cnt in _window_pairs.most_common(200):
                    if _cnt < 3:
                        continue
                    _p_joint = _cnt / _pair_total
                    _p_w1 = _pmi_freq.get(_w1, 1) / _total_pmi
                    _p_w2 = _pmi_freq.get(_w2, 1) / _total_pmi
                    _pmi_val = _log(_p_joint / (_p_w1 * _p_w2) + 1e-10)
                    if _pmi_val > 0:
                        _pmi_rows.append({
                            "word1": _w1, "word2": _w2,
                            "pair_count": _cnt, "pmi": round(_pmi_val, 3),
                        })
                if _pmi_rows:
                    _pmi_df_live = pd.DataFrame(_pmi_rows).nlargest(20, "pmi")
                    st.caption(T["top_pmi_desc"])
                    st.dataframe(_pmi_df_live.rename(columns={
                        "word1": T["top_pmi_word1"], "word2": T["top_pmi_word2"],
                        "pair_count": T["top_pmi_count"], "pmi": T["top_pmi_pmi"],
                    }), use_container_width=True, height=300)
                else:
                    st.info(T["no_word_rel"])
            else:
                st.info(T["no_word_rel"])

    # ── 7. Textové vzory + opozície ───────────────────────────────────────────
    if st.session_state.get("sel_patterns", False) and _ldat:
        with st.expander(f"📤 🕐 {T['ana_patterns_name']}"):
            from w_opposition_networks import OPPOSITION_PAIRS
            from collections import Counter as _OC
            _oh: "_OC" = _OC()
            _nl = len(_ldat)
            for _ii,(_, _ls_i) in enumerate(_ldat):
                _win2: set = set()
                for _,_ls_j in _ldat[max(0,_ii-3):min(_nl,_ii+4)]:
                    _win2 |= set(_ls_j.split())
                for _w1,_w2 in OPPOSITION_PAIRS:
                    if _w1 in _win2 and _w2 in _win2:
                        _oh[f"{_w1} | {_w2}"] += 1
            if _oh:
                _od = pd.DataFrame(_oh.most_common(15),
                                   columns=[T["opposition_title"],T["x_count"]])
                st.caption(T["opposition_window_note"])
                st.plotly_chart(
                    fig_hbar(_od,T["x_count"],T["opposition_title"],
                             T["opposition_title"],h=360,
                             xlabel=T["x_count"]),
                    use_container_width=True,
                )
            _bi = compute_ngrams(tuple(s for s,_ in _ldat),2,20)
            _tr = compute_ngrams(tuple(s for s,_ in _ldat),3,12)
            _p1, _p2 = st.columns(2)
            with _p1:
                if not _bi.empty:
                    st.plotly_chart(
                        fig_hbar(_bi,"count","ngram",T["bigrams_title"],h=400,
                                 xlabel=T["x_frequency"]),
                        use_container_width=True,
                    )
            with _p2:
                if not _tr.empty:
                    st.plotly_chart(
                        fig_hbar(_tr,"count","ngram",T["trigrams_title"],h=400,
                                 xlabel=T["x_frequency"]),
                        use_container_width=True,
                    )

            # TF-IDF by chapter heatmap (requires multiple chapters)
            if _units and len(_units) >= 3 and not _df.empty and "unit_id" in _df.columns:
                st.divider()
                _tfidf_items = []
                for _u in _units:
                    _u_lems = " ".join(
                        ls for _, ls in _ldat
                        if ls  # all lemmas available (per-sentence)
                    ) if not _df[_df["unit_id"] == _u.unit_id].empty else ""
                    # Use lemmas from skinner rows that belong to this unit
                    _u_rows = _df[_df["unit_id"] == _u.unit_id]
                    if "lemmas" in _u_rows.columns:
                        _u_lems = " ".join(_u_rows["lemmas"].dropna().astype(str))
                    if _u_lems.strip():
                        _tfidf_items.append((_u.display_name, _u_lems))
                if len(_tfidf_items) >= 3:
                    _tfidf_heat = compute_tfidf_heatmap(tuple(_tfidf_items), top_n=25)
                    if not _tfidf_heat.empty:
                        st.caption(T["tfidf_heatmap_desc"])
                        _th_wide = _tfidf_heat.copy()
                        _th_wide = _th_wide.rename(columns={"book": _col_unit})
                        st.plotly_chart(
                            fig_heatmap(_th_wide, _col_unit,
                                        T["tfidf_heatmap_title"], h=420,
                                        fmt=".2f"),
                            use_container_width=True,
                        )
            elif _units and len(_units) < 3:
                st.info("Kapitolová TF-IDF heatmapa vyžaduje alespoň 3 kapitoly.")

    # ── 8. Štýl a syntax ─────────────────────────────────────────────────────
    if st.session_state.get("sel_style", False):
        with st.expander(f"📤 🕐 {T['ana_style_name']}"):
            st.caption(f"*[Nahraný text — výpočet živě]*")
            if not _df.empty and "unit_id" in _df.columns and _units and len(_units) >= 2:
                # Tree depth and clause count from refined_descriptions if available
                if not _ref_df.empty and "avg_tree_depth" in _ref_df.columns and "unit_id" in _ref_df.columns:
                    _cx_agg = (
                        _ref_df.groupby("unit_id")[["avg_tree_depth", "avg_clause_count"]]
                        .mean()
                        .reset_index()
                    )
                    _uid2name = {u.unit_id: u.display_name for u in _units}
                    _cx_agg[_col_unit] = _cx_agg["unit_id"].map(_uid2name).fillna(_cx_agg["unit_id"])
                    st.caption(T.get("complexity_desc", "Syntaktická složitost"))
                    _sx1, _sx2 = st.columns(2)
                    with _sx1:
                        st.plotly_chart(
                            fig_hbar(_cx_agg, "avg_tree_depth", _col_unit,
                                     T.get("complexity_title", "Hloubka stromu"), h=320,
                                     xlabel=T.get("x_depth", "Hloubka")),
                            use_container_width=True,
                        )
                    with _sx2:
                        if "avg_clause_count" in _cx_agg.columns:
                            st.plotly_chart(
                                fig_hbar(_cx_agg, "avg_clause_count", _col_unit,
                                         T.get("complexity_title", "Počet klauzulí"), h=320,
                                         xlabel=T.get("x_clauses", "Klauzule")),
                                use_container_width=True,
                            )
                # TF-IDF chapter style clustering
                if not _df.empty and "lemmas" in _df.columns and len(_units) >= 4:
                    st.divider()
                    _sty_items = []
                    for _u in _units:
                        _u_rows = _df[_df["unit_id"] == _u.unit_id]
                        _u_lems = " ".join(_u_rows["lemmas"].dropna().astype(str))
                        if _u_lems.strip():
                            _sty_items.append((_u.display_name, _u_lems))
                    if len(_sty_items) >= 4:
                        try:
                            from sklearn.cluster import KMeans as _KM
                            from sklearn.feature_extraction.text import TfidfVectorizer as _TfV
                            _n_cl = min(4, len(_sty_items))
                            _tfidf_v = _TfV(max_features=300, min_df=1,
                                            token_pattern=r"[a-zA-ZáčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ]{3,}")
                            _X_sty = _tfidf_v.fit_transform([d for _, d in _sty_items]).toarray()
                            _km = _KM(n_clusters=_n_cl, random_state=42, n_init=10)
                            _labels = _km.fit_predict(_X_sty)
                            _sty_df2 = pd.DataFrame({
                                _col_unit: [b for b, _ in _sty_items],
                                T.get("col_style_cluster", "Stylový shluk"): [f"Shluk {l+1}" for l in _labels],
                            })
                            st.caption(T["style_table_desc"])
                            st.dataframe(_sty_df2, use_container_width=True)
                        except Exception:
                            pass
            else:
                st.info("Spusťte plnou analýzu s alespoň 2 kapitolami pro zobrazení stylu.")

    # ── 9. Kvalita výsledkov ──────────────────────────────────────────────────
    if st.session_state.get("sel_quality", True):
        with st.expander(f"📤 ⚡ {T['ana_quality_name']}"):
            if "confidence" in _df.columns and not _df.empty:
                _cband_l = int((_df["confidence"] < 0.30).sum())
                _cband_m = int(((_df["confidence"]>=0.30)&(_df["confidence"]<0.60)).sum())
                _cband_h = int((_df["confidence"]>=0.60).sum())
                _qdf = pd.DataFrame({
                    T["x_book"]: [T["conf_band_low"],T["conf_band_mid"],T["conf_band_high"]],
                    T["x_sentences"]: [_cband_l,_cband_m,_cband_h],
                })
                _qclr = {T["conf_band_low"]:"#e63946",
                         T["conf_band_mid"]:"#f4a261",
                         T["conf_band_high"]:"#57cc99"}
                st.caption(T["conf_bins_desc"])
                _fig_q = px.bar(_qdf, x=T["x_sentences"], y=T["x_book"],
                                orientation="h", color=T["x_book"],
                                color_discrete_map=_qclr, title=T["conf_bins_title"])
                _fig_q.update_layout(showlegend=False, height=220, **_LAYOUT)
                st.plotly_chart(_fig_q, use_container_width=True)

                if "primary_intention" in _df.columns:
                    _dfbx = _df.copy()
                    _dfbx[T["x_intention"]] = (_dfbx["primary_intention"]
                                               .map(VI).fillna(_dfbx["primary_intention"]))
                    st.plotly_chart(
                        fig_box_confidence(_dfbx, T["x_intention"], "confidence",
                                           T["conf_hist_title"], INT_CLR),
                        use_container_width=True,
                    )
            else:
                st.info("Spusťte plnou analýzu pro zobrazení kvality klasifikace.")

    # ── 10. Dashboard ─────────────────────────────────────────────────────────
    if st.session_state.get("sel_dashboard", True):
        with st.expander(f"📤 ⚡ {T['ana_dashboard_name']}"):
            from n_db import count_table_rows, list_runs, TABLE_SKINNER
            _db_n = count_table_rows(TABLE_SKINNER)
            _runs = list_runs(TABLE_SKINNER)
            _upload_runs = [r for r in _runs if "upload_" in r]
            _seg_method = "marker" if _units and len(_units) > 1 else "single"
            st.markdown(f"""
| | |
|---|---|
| **Zdroj** | `{_src}` |
| **Korpus ID** | `{_corpus_id}` |
| **{_unit_metric}** | {_n_chapters} |
| **Věty celkem** | {_total} |
| **DB řádky (skinner_analysis)** | {_db_n or "—"} |
| **Biblické běhy v DB** | {len(_runs) - len(_upload_runs)} |
| **Upload běhy v DB** | {len(_upload_runs)} |
| **NLP model** | `{pipeline_lang}` |
""")

    # ── Save to DB ────────────────────────────────────────────────────────────
    st.divider()
    _already_saved = "adf_saved_run_id" in st.session_state
    if _already_saved:
        st.success(f"{T['save_already']}: `{st.session_state['adf_saved_run_id']}`")
    else:
        st.caption(T["save_caption"])
        if st.button(T["save_button"], type="secondary", key="res_save"):
            _src2 = st.session_state.get("adf_source","unknown")
            _rid = _make_upload_run_id(_src2)
            try:
                _nn = _save_to_db(
                    _df, _rid,
                    rel_df=st.session_state.get("adf_rel"),
                    ref_df=st.session_state.get("adf_ref"),
                )
                st.session_state["adf_saved_run_id"] = _rid
                st.success(
                    f"{T['save_success']}  ·  "
                    f"{T['save_run_id_label']}: `{_rid}`  ·  "
                    f"{_nn} {T['save_rows_label']}"
                )
                st.rerun()
            except Exception as _exc:
                st.error(f"{T['save_error']}: {_exc}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — COMPARISON  (placeholder — Phase 2)
# ══════════════════════════════════════════════════════════════════════════════

with tab_compare:

    st.subheader(T["compare_title"])
    st.info(T["compare_placeholder"])
