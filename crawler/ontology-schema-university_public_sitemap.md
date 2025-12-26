# Ontologie basée sur le Sitemap de FH Südwestfalen

Cette ontologie reflète la structure réelle du site web de la Fachhochschule Südwestfalen telle qu'elle apparaît dans le sitemap HTML. Elle est optimisée pour le crawling et l'indexation des informations publiques.

## 1. Structure Hiérarchique du Site Web

### 1.1 Sections Principales (Hauptbereiche)

#### 1.1.1 International
**Eigenschaften:**
- `section_id` (String, eindeutig): international
- `name` (String): International
- `url` (String): https://www.fh-swf.de/de/international_3/index.php
- `level` (Integer): 1
- `parent_section_id` (String): null (root)

#### 1.1.2 Studieninteressierte (Prospective Students)
**Eigenschaften:**
- `section_id` (String, eindeutig): studieninteressierte
- `name` (String): Studieninteressierte
- `url` (String): https://www.fh-swf.de/de/studieninteressierte/index.php
- `level` (Integer): 1
- `parent_section_id` (String): null
- `zielgruppe` (String): Studieninteressierte, Studienanfänger*innen

#### 1.1.3 Studienangebot (Study Programs)
**Eigenschaften:**
- `section_id` (String, eindeutig): studienangebot
- `name` (String): Studienangebot
- `url` (String): https://www.fh-swf.de/de/studienangebot/index.php
- `level` (Integer): 1
- `parent_section_id` (String): null

#### 1.1.4 Studierende (Students)
**Eigenschaften:**
- `section_id` (String, eindeutig): studierende
- `name` (String): Studierende
- `url` (String): https://www.fh-swf.de/de/studierende/index.php
- `level` (Integer): 1
- `parent_section_id` (String): null
- `zielgruppe` (String): Studierende

#### 1.1.5 Forschung & Transfer
**Eigenschaften:**
- `section_id` (String, eindeutig): forschung_transfer
- `name` (String): Forschung & Transfer
- `url` (String): https://www.fh-swf.de/de/forschung___transfer_4/test_1.php
- `level` (Integer): 1
- `parent_section_id` (String): null
- `zielgruppe` (String): Forschende, Unternehmen

#### 1.1.6 Karriere (Career)
**Eigenschaften:**
- `section_id` (String, eindeutig): karriere
- `name` (String): Karriere
- `url` (String): https://www.fh-swf.de/de/karriere/karriere_fhswf/index.php
- `level` (Integer): 1
- `parent_section_id` (String): null
- `zielgruppe` (String): Studierende, Absolventinnen, Beschäftigte

#### 1.1.7 Über uns (About Us)
**Eigenschaften:**
- `section_id` (String, eindeutig): ueber_uns
- `name` (String): Über uns
- `url` (String): https://www.fh-swf.de/de/ueber_uns/index.php
- `level` (Integer): 1
- `parent_section_id` (String): null
- `zielgruppe` (String): Alle Zielgruppen

### 1.2 Sous-sections Studieninteressierte

#### 1.2.1 Information & Beratung
**Eigenschaften:**
- `section_id` (String, eindeutig): information_beratung
- `name` (String): Information & Beratung
- `url` (String): https://www.fh-swf.de/de/studieninteressierte/information___beratung/allgemeine_studienberatung/index.php
- `level` (Integer): 2
- `parent_section_id` (String): studieninteressierte
- `unterabschnitte` (Array): Liste des IDs des sous-sections

**Sous-sections:**
- Allgemeine Studienberatung
- Talentscouting
- Info-Veranstaltungen
- Warum bei uns studieren?
- Studieren ohne Abitur
- Wir erklären die Hochschulwelt
- Studium von A-Z (FAQs)

#### 1.2.2 Bewerbung & Einschreibung
**Eigenschaften:**
- `section_id` (String, eindeutig): bewerbung_einschreibung
- `name` (String): Bewerbung & Einschreibung
- `url` (String): https://www.fh-swf.de/de/studieninteressierte/bewerbung/index.php
- `level` (Integer): 2
- `parent_section_id` (String): studieninteressierte

**Sous-sections:**
- Bewerbung für ein Bachelorstudium
- Bewerbung für ein Masterstudium
- Bewerbung für Gasthörer/Quereinsteiger/Zweithörer
- Bewerbung für ein Promotionsstudium
- Bewerbungsfristen

#### 1.2.3 Studienvorbereitung
**Eigenschaften:**
- `section_id` (String, eindeutig): studienvorbereitung
- `name` (String): Studienvorbereitung
- `url` (String): https://www.fh-swf.de/de/studieninteressierte/studienvorbereitung/studienvorbereitung_2.php
- `level` (Integer): 2
- `parent_section_id` (String): studieninteressierte

**Sous-sections:**
- Finanzielles
- Wohnen
- Studienstart

#### 1.2.4 Beiträge und Gebühren
**Eigenschaften:**
- `section_id` (String, eindeutig): beitraege_gebuehren
- `name` (String): Beiträge und Gebühren
- `url` (String): https://www.fh-swf.de/de/studieninteressierte/bewerbung/beitraege_und_gebuehren_1/index.php
- `level` (Integer): 2
- `parent_section_id` (String): studieninteressierte

#### 1.2.5 Schnupperangebote
**Eigenschaften:**
- `section_id` (String, eindeutig): schnupperangebote
- `name` (String): Schnupperangebote
- `url` (String): https://www.fh-swf.de/de/studieninteressierte/schnupperangebote/angebote_fuer_schueler_innen/index.php
- `level` (Integer): 2
- `parent_section_id` (String): studieninteressierte

#### 1.2.6 Angebote für Geflüchtete
**Eigenschaften:**
- `section_id` (String, eindeutig): angebote_gefluechtete
- `name` (String): Angebote für Geflüchtete
- `url` (String): https://www.fh-swf.de/de/studieninteressierte/angebote_fuer_gefluechtete/index.php
- `level` (Integer): 2
- `parent_section_id` (String): studieninteressierte

### 1.3 Sous-sections Studienangebot

#### 1.3.1 Studiengänge (organisés par Standorte)
**Eigenschaften:**
- `section_id` (String, eindeutig): studiengaenge
- `name` (String): Studiengänge
- `url` (String): https://www.fh-swf.de/de/studienangebot/studiengaenge/index.php
- `level` (Integer): 2
- `parent_section_id` (String): studienangebot

**Standorte (Level 3):**
- Hagen
- Iserlohn
- Lüdenscheid
- Meschede
- Soest
- Hagen-Meschede (multi-standort)
- Hagen-Lüdenscheid (multi-standort)
- Iserlohn Meschede Lüdenscheid (multi-standort)

**Eigenschaften Standort:**
- `standort_id` (String, eindeutig): hagen, iserlohn, luedenscheid, meschede, soest
- `name` (String): Nom du Standort
- `url` (String): URL de la page du Standort
- `level` (Integer): 3
- `parent_section_id` (String): studiengaenge
- `studiengaenge` (Array): Liste des IDs des Studiengänge à ce Standort

#### 1.3.2 Studienmodelle
**Eigenschaften:**
- `section_id` (String, eindeutig): studienmodelle
- `name` (String): Studienmodelle
- `url` (String): https://www.fh-swf.de/de/studienangebot/studienmodelle/index.php
- `level` (Integer): 2
- `parent_section_id` (String): studienangebot

#### 1.3.3 Fachgebiete (Fachbereiche)
**Eigenschaften:**
- `section_id` (String, eindeutig): fachgebiete
- `name` (String): Fachgebiete
- `url` (String): https://www.fh-swf.de/de/studienangebot/fachbereiche_3/test_5.php
- `level` (Integer): 2
- `parent_section_id` (String): studienangebot

**Fachbereiche (Level 3):**
- Agrarwirtschaft
- Designmanagement und Produktentwicklung
- Gesundheits- und Naturwissenschaften
- Informatik und Digitalisierung
- Pädagogik und Psychologie
- Technik und Ingenieurwesen
- Umwelt und Nachhaltigkeit
- Wirtschaft und Recht

**Eigenschaften Fachbereich:**
- `fachbereich_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Nom du Fachbereich
- `url` (String): URL de la page du Fachbereich
- `level` (Integer): 3
- `parent_section_id` (String): fachgebiete

#### 1.3.4 Weitere Angebote
**Eigenschaften:**
- `section_id` (String, eindeutig): weitere_angebote
- `name` (String): Weitere Angebote
- `url` (String): https://www.fh-swf.de/de/studierende/zusaetzliche_angebote/zusatzqualifikationen/index.php
- `level` (Integer): 2
- `parent_section_id` (String): studienangebot

**Sous-sections:**
- Berufsschullehrer*in werden
- Studium Flexibel
- Zusatzqualifikationen

### 1.4 Sous-sections Studierende

#### 1.4.1 Rund ums Studium
**Eigenschaften:**
- `section_id` (String, eindeutig): rund_ums_studium
- `name` (String): Rund ums Studium
- `url` (String): https://www.fh-swf.de/de/studierende/studienorganisation/index.php
- `level` (Integer): 2
- `parent_section_id` (String): studierende

**Sous-sections:**
- Studienorganisation
- Online-Services
- Semestertermine
- Studienstart
- Beiträge und Gebühren
- BaFöG und Stipendien
- Studium von A-Z (FAQs)

#### 1.4.2 Serviceeinrichtungen
**Eigenschaften:**
- `section_id` (String, eindeutig): serviceeinrichtungen
- `name` (String): Serviceeinrichtungen
- `url` (String): https://www.fh-swf.de/de/studierende/rund_ums_studium/index.php
- `level` (Integer): 2
- `parent_section_id` (String): studierende

**Services (Level 3):**
- Bibliothek
  - Open Educational Resources
  - Forschungsnahe Dienste
  - Forschungsdatenmanagement (FDM)
  - Services für Promovierende
- IT-Services
- Mensa
- Studierenden-Servicebüros
- International Office
- Lernzentren / Studi-Points
- Institut für Verbundstudien
- AudioVisuellesMedienZentrum
- Qualitätsverbesserungskommission
- Beratung & Unterstützung

#### 1.4.3 Beratung & Unterstützung
**Eigenschaften:**
- `section_id` (String, eindeutig): beratung_unterstuetzung
- `name` (String): Beratung & Unterstützung
- `url` (String): https://www.fh-swf.de/de/studierende/ansprechpartner_1/ansprechpartner_2.php
- `level` (Integer): 2
- `parent_section_id` (String): studierende

**Sous-sections:**
- Studierenden-Servicebüros
- Studienfachberatung
- Studierendencoaching
- Studierendenwerk Dortmund
- Studium und Behinderung
  - Bewerbung und Zulassung
  - Nachteilsausgleiche bei Prüfungen
- Career Service
- Familienbüro
  - Kinderbetreuung
    - Ferienbetreuung
  - Väter
  - Hilfe und Beratung
  - Pflege von Angehörigen
    - Vorsorge
    - Vereinbarkeit von Pflege und Beruf
    - Linkliste und Downloads
  - Studieren mit Kind
    - Infos für werdende Eltern
    - Finanzierung des Studiums mit Kind(ern)
  - Arbeiten mit Kind
  - Veranstaltungen
- Gleichstellung
- Psychotherapeutische Sprechstunde
- Serviceeinrichtungen

#### 1.4.4 International studieren
**Eigenschaften:**
- `section_id` (String, eindeutig): international_studieren
- `name` (String): International studieren
- `url` (String): https://www.fh-swf.de/de/studierende/international_studieren/index.php
- `level` (Integer): 2
- `parent_section_id` (String): studierende

#### 1.4.5 Studentisches Engagement & Leben
**Eigenschaften:**
- `section_id` (String, eindeutig): studentisches_engagement
- `name` (String): Studentisches Engagement & Leben
- `url` (String): https://www.fh-swf.de/de/studierende/zusaetzliche_angebote/dezentrale_angebote/index.php
- `level` (Integer): 2
- `parent_section_id` (String): studierende

**Sous-sections:**
- Studentische Selbstverwaltung
- Hochschulsport
- Big Band
- Studentische Projekte
- Tutorien
- Wohnen

### 1.5 Sous-sections Forschung & Transfer

#### 1.5.1 Forschungsfelder
**Eigenschaften:**
- `section_id` (String, eindeutig): forschungsfelder
- `name` (String): Forschungsfelder
- `url` (String): https://www.fh-swf.de/de/forschung___transfer_4/forschungsfelder/index.php
- `level` (Integer): 2
- `parent_section_id` (String): forschung_transfer

#### 1.5.2 Forschungs- und Transferprojekte
**Eigenschaften:**
- `section_id` (String, eindeutig): forschungsprojekte
- `name` (String): Forschungs- und Transferprojekte
- `url` (String): https://www.fh-swf.de/de/forschung___transfer_4/forschungsprojekte_1/institute_allgemein_neu_1.php
- `level` (Integer): 2
- `parent_section_id` (String): forschung_transfer

#### 1.5.3 Transfer und Dienstleistungen
**Eigenschaften:**
- `section_id` (String, eindeutig): transfer_dienstleistungen
- `name` (String): Transfer und Dienstleistungen für Partner und Interessierte
- `url` (String): https://www.fh-swf.de/de/forschung___transfer_4/transfer_und_dienstleistungen/transfer_und_dienstleistungen_1.php
- `level` (Integer): 2
- `parent_section_id` (String): forschung_transfer

#### 1.5.4 Zentrum für Forschungsmanagement und Transfer
**Eigenschaften:**
- `section_id` (String, eindeutig): zentrum_forschungsmanagement
- `name` (String): Hochschulinternes Zentrum für Forschungsmanagement und Transfer
- `url` (String): https://www.fh-swf.de/de/forschung___transfer_4/zentrum_fuer_forschungsmanagement_und_transfer/zentrum_fuer_forschungsmanagement_1.php
- `level` (Integer): 2
- `parent_section_id` (String): forschung_transfer

#### 1.5.5 Innovative Hochschule
**Eigenschaften:**
- `section_id` (String, eindeutig): innovative_hochschule
- `name` (String): Innovative Hochschule
- `url` (String): https://www.fh-swf.de/de/forschung___transfer_4/innovative_hochschule/index.php
- `level` (Integer): 2
- `parent_section_id` (String): forschung_transfer

### 1.6 Sous-sections Karriere

#### 1.6.1 Die FH Südwestfalen als Arbeitgeber
**Eigenschaften:**
- `section_id` (String, eindeutig): arbeitgeber
- `name` (String): Die FH Südwestfalen als Arbeitgeber
- `url` (String): https://www.fh-swf.de/de/karriere/karriere_fhswf/index.php
- `level` (Integer): 2
- `parent_section_id` (String): karriere

#### 1.6.2 Wissenschaftlicher Nachwuchs und Promotion
**Eigenschaften:**
- `section_id` (String, eindeutig): wissenschaftlicher_nachwuchs
- `name` (String): Wissenschaftlicher Nachwuchs und Promotion
- `url` (String): https://www.fh-swf.de/de/karriere/promotionsmoeglichkeiten_1/index.php
- `level` (Integer): 2
- `parent_section_id` (String): karriere

#### 1.6.3 Jobs für Studierende und Absolventinnen
**Eigenschaften:**
- `section_id` (String, eindeutig): jobs_studierende
- `name` (String): Jobs für Studierende und Absolventinnen
- `url` (String): https://www.fh-swf.de/de/karriere/jobs_fuer_studierende_und_absolventinnen/index.php
- `level` (Integer): 2
- `parent_section_id` (String): karriere

#### 1.6.4 Career Service
**Eigenschaften:**
- `section_id` (String, eindeutig): career_service
- `name` (String): Career Service
- `url` (String): https://www.fh-swf.de/de/karriere/career_service_1/career_service_1.php
- `level` (Integer): 2
- `parent_section_id` (String): karriere

#### 1.6.5 Karrieretag
**Eigenschaften:**
- `section_id` (String, eindeutig): karrieretag
- `name` (String): Karrieretag
- `url` (String): https://www.fh-swf.de/de/karriere/karrieretag/index.php
- `level` (Integer): 2
- `parent_section_id` (String): karriere

**Sous-sections:**
- Karrieretag Hagen

#### 1.6.6 Alumni
**Eigenschaften:**
- `section_id` (String, eindeutig): alumni
- `name` (String): Alumni
- `url` (String): https://www.fh-swf.de/de/karriere/alumni/ehemalige/index.php
- `level` (Integer): 2
- `parent_section_id` (String): karriere

**Sous-sections:**
- Fördervereine
- Ehemalige
- Alumni-Netzwerk für Promovierte

### 1.7 Sous-sections Über uns

#### 1.7.1 News & Events
**Eigenschaften:**
- `section_id` (String, eindeutig): news_events
- `name` (String): News & Events
- `url` (String): https://www.fh-swf.de/de/ueber_uns/events_3/index.php
- `level` (Integer): 2
- `parent_section_id` (String): ueber_uns

**Sous-sections:**
- Veranstaltungen & Events
  - intern_events
- News & Pressemitteilungen
- Storys von der Fachhochschule
  - Industrielle Messung: smart und ehrlich
- Forschung & Transfer im Fokus

#### 1.7.2 Portrait & Leitbild
**Eigenschaften:**
- `section_id` (String, eindeutig): portrait_leitbild
- `name` (String): Portrait & Leitbild
- `url` (String): https://www.fh-swf.de/de/ueber_uns/leitbild___vision/index.php
- `level` (Integer): 2
- `parent_section_id` (String): ueber_uns

**Sous-sections:**
- Hochschulentwicklungsplan
- Internationalisierung
- Chancengerechtigkeit und Diversität
  - Toleranzerklärung
  - Weiterbildungsangebote im Bereich Diversity
  - CampusDialoge

#### 1.7.3 Infos, Zahlen & Fakten
**Eigenschaften:**
- `section_id` (String, eindeutig): infos_zahlen_fakten
- `name` (String): Infos, Zahlen & Fakten
- `url` (String): https://www.fh-swf.de/de/ueber_uns/infos__zahlen___fakten/infos__zahlen___fakten_1.php
- `level` (Integer): 2
- `parent_section_id` (String): ueber_uns

**Sous-sections:**
- Historie
- Zahlenspiegel
- Mitgliedschaften
- Ehrensenatoren & Honorarprofessoren
- Auszeichnungen
  - Budde-Preis
  - DAAD-Preis
  - Dr. Kirchhoff-Preis
  - Förderpreis des UVWM
  - Soester Agrarpreis
  - Soester Innovationspreis
  - Soroptimist-Förderpreis

#### 1.7.4 Standorte
**Eigenschaften:**
- `section_id` (String, eindeutig): standorte
- `name` (String): Standorte
- `url` (String): https://www.fh-swf.de/de/ueber_uns/standorte_4/index.php
- `level` (Integer): 2
- `parent_section_id` (String): ueber_uns

**Standorte détaillés (Level 3):**

**Hagen:**
- Fachbereich Elektrotechnik und Informationstechnik
  - Evaluation Fachbereich E&I
  - Der Dekan im Interview
  - Fachschaft E&I
- Fachbereich Technische Betriebswirtschaft
  - Fachschaft TBW
  - Der Dekan im Interview
  - Evaluation Fachbereich TBW
  - Verbundstudium
    - Verbundstudiengänge Betriebswirtschaft/Wirtschaftsrecht
- Anfahrt, ÖPNV & Lageplan
- Evaluation Hagen
- Studierendencoaching Hagen

**Iserlohn:**
- FB Informatik und Naturwissenschaften
  - Termine (avec historique des semestres)
- FB Maschinenbau
  - Termine Semester
- Anfahrt, ÖPNV & Lageplan
- Qualitätsmanagement Iserlohn

**Lüdenscheid:**
- Anfahrt, ÖPNV & Lageplan
- Angeschlossene Fachbereiche

**Meschede:**
- FB Ingenieur- und Wirtschaftswissenschaften
  - Anerkennung von Prüfungsleistungen
  - Der Dekan im Interview
- Anfahrt, ÖPNV & Lageplan

**Soest:**
- FB Agrarwirtschaft
  - Versuchsgut Merklingsen
  - Susatia
  - Forschungsprojekte
  - Der Dekan im Interview
  - Evaluation
  - Forschungsnotizen
  - Sprechzeiten FB Agrarwirtschaft
  - Fachschaft Agrarwirtschaft
- FB Bildungs- und Gesellschaftswissenschaften
  - Fachschaft Bildungs- und Gesellschaftswissenschaften
- FB Elektrische Energietechnik
- FB Maschinenbau-Automatisierungstechnik
- Anfahrt, ÖPNV & Lageplan

#### 1.7.5 Organisation & Beschäftigte
**Eigenschaften:**
- `section_id` (String, eindeutig): organisation_beschaeftigte
- `name` (String): Organisation & Beschäftigte
- `url` (String): https://www.fh-swf.de/de/ueber_uns/beschaeftigte_1/index.php
- `level` (Integer): 2
- `parent_section_id` (String): ueber_uns

**Sous-sections:**
- Lehrende
- Leitung, Gremien, Beauftragte
  - Hochschulleitung
    - Rektor
    - Kanzler
    - Rektorat
    - Senat
    - Hochschulrat
    - FB-Konferenz
    - Kuratorium
    - Offenlegung von Mitgliedschaften und Funktionen
    - Hochschulwahlversammlung
  - Beauftragte und Vertretung
    - Gleichstellungsbeauftragte
    - Beauftragte für Studierende mit Behinderung oder chronischer Erkankung
    - Schwerbehindertenvertretung
    - Datenschutzbeauftragte*r
    - Personalrat der wissenschaftlich Beschäftigten – PRwiss
    - Personalrat für Mitarbeiter*innen in Technik und Verwaltung
    - Jugend- und Auszubildendenvetretung (JAV)
    - Stabsstelle für Arbeits-, Gesundheits- und Umweltschutz
    - Betriebliches Eingliederungsmanagement (BEM)
    - Betriebsärztl. Dienst
    - Stabsstelle Nachhaltigkeit
    - Gemeinsame Innenrevision
    - Qualitätsmanagement
    - Informationssicherheitsbeauftragte*r
  - Arbeitskreise, Ausschüsse und Kommissionen
    - Prüfungsausschuss
    - Qualitätsverbesserungskommission
    - Arbeitskreis Internationale Beziehungen
    - Ombudsperson und Untersuchungskommission
    - Ethik-Kommission
- Verwaltung
  - Dez. 1: Organisation und Personal
  - Dez. 2: Akademische und Studentische Angelegenheiten, Recht und Compliance
  - Dez. 3: Finanzmanagement
  - Dez. 4: International Office
  - Dez. 5: Hochschulkommunikation
  - Dez. 6: IT-Services
  - Dez. 7: Gebäudemanagement
  - Dez. 8: Digitale Entwicklung
    - Software
    - Support
  - Infos von A-Z für Beschäftigte
  - Prozessunterlagen Studium & Lehre
- Einrichtungen
- Fortbildung
- Blended Learning
- Gesundheitsportal
  - Personalbefragung
    - Querschnittsthemen mitgestalten
  - Themensemester Kopfschmerz
  - Themensemester Gesunder Schlaf
  - Firmenfitness
  - Themensemester Ergonomie
- Interne Kommunikation

#### 1.7.6 Presse
**Eigenschaften:**
- `section_id` (String, eindeutig): presse
- `name` (String): Presse
- `url` (String): https://www.fh-swf.de/de/ueber_uns/presse/presse_1.php
- `level` (Integer): 2
- `parent_section_id` (String): ueber_uns

#### 1.7.7 FH-Shop
**Eigenschaften:**
- `section_id` (String, eindeutig): fh_shop
- `name` (String): FH-Shop
- `url` (String): https://www.fh-swf.de/de/ueber_uns/fh_shop/fh_shop_1.php
- `level` (Integer): 2
- `parent_section_id` (String): ueber_uns

### 1.8 Footer Sections

#### 1.8.1 Footer Links
**Eigenschaften:**
- `section_id` (String, eindeutig): footer
- `name` (String): Footer
- `level` (Integer): 1
- `parent_section_id` (String): null

**Links:**
- Impressum
- Datenschutz
- Disclaimer
- Barrierefreiheit
- Leichte Sprache
- Sitemap
- Kontakt
- Cookie Einstellungen

## 2. Nœuds de Contenu (Content Nodes)

### 2.1 Page (Page Web)
**Eigenschaften:**
- `page_id` (String, eindeutig): Identifikationsnummer (basé sur URL)
- `url` (String): URL complète de la page
- `url_path` (String): Chemin de l'URL (sans domaine)
- `title` (String): Titre de la page (balise <title>)
- `meta_description` (Text): Meta description
- `meta_keywords` (Text): Meta keywords
- `zielgruppen` (Array): Liste des Zielgruppen (meta tag)
- `standorte` (Array): Liste des Standorte mentionnés (meta tag)
- `section_id` (String): ID de la section parente
- `content_type` (String): Type de contenu (standard, formular, dokument, etc.)
- `html_content` (Text): Contenu HTML complet
- `text_content` (Text): Texte extrait (sans HTML)
- `crawled_at` (Date): Date du crawl
- `last_modified` (Date): Dernière modification (si disponible)
- `language` (String): Langue (de, en)
- `breadcrumb` (Array): Fil d'Ariane (liste des sections parentes)

### 2.2 Dokument (Document)
**Eigenschaften:**
- `dokument_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Nom du document
- `url` (String): URL du document
- `typ` (String): PDF, Word, Excel, etc.
- `dateigroesse` (Integer): Taille en bytes
- `section_id` (String): Section parente
- `page_id` (String): Page qui référence ce document
- `download_count` (Integer): Nombre de téléchargements (si disponible)

### 2.3 Formular (Form)
**Eigenschaften:**
- `formular_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Nom du formulaire
- `url` (String): URL du formulaire
- `typ` (String): Bewerbung, Anfrage, etc.
- `section_id` (String): Section parente
- `page_id` (String): Page qui contient le formulaire

### 2.4 Veranstaltung (Event)
**Eigenschaften:**
- `veranstaltung_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Nom de l'événement
- `url` (String): URL de la page de l'événement
- `typ` (String): Info-Veranstaltung, Tag der offenen Tür, etc.
- `datum` (Date): Date de l'événement
- `section_id` (String): Section parente
- `page_id` (String): Page qui décrit l'événement

## 3. Beziehungen (Relationships)

### 3.1 Hiérarchie des Sections

- `HAT_UNTERABSCHNITT` (Section → Section)
  - Eigenschaften: `reihenfolge` (Integer), `level` (Integer)
  
- `GEHOERT_ZU` (Section → Section)
  - Eigenschaften: `level` (Integer)

### 3.2 Contenu

- `ENTHAELT` (Section → Page)
  - Eigenschaften: `hauptseite` (Boolean)
  
- `VERWEIST_AUF` (Page → Page)
  - Eigenschaften: `link_text` (String), `link_type` (String)
  
- `HAT_DOKUMENT` (Page → Dokument)
  - Eigenschaften: `typ` (String)
  
- `HAT_FORMULAR` (Page → Formular)
  - Eigenschaften: `typ` (String)
  
- `BESCHREIBT` (Page → Veranstaltung)
  - Eigenschaften: `vollstaendig` (Boolean)

### 3.3 Standorte

- `BEFINDET_SICH_IN` (Section → Standort)
  - Eigenschaften: `hauptstandort` (Boolean)
  
- `HAT_FACHBEREICH` (Standort → Fachbereich)
  - Eigenschaften: `hauptstandort` (Boolean)

### 3.4 Studiengänge

- `WIRD_ANGEBOTEN_AN` (Studiengang → Standort)
  - Eigenschaften: `hauptstandort` (Boolean)
  
- `GEHOERT_ZU` (Studiengang → Fachbereich)
  - Eigenschaften: `hauptfachbereich` (Boolean)

### 3.5 Navigation

- `NAECHSTE_SEITE` (Page → Page)
  - Eigenschaften: `navigation_type` (String) - next, previous, related
  
- `VERWANDTE_SEITE` (Page → Page)
  - Eigenschaften: `aehnlichkeit` (Float)

## 4. Métadonnées pour le Crawling

### 4.1 Informations de Crawl
- `crawl_priority` (Integer): Priorité de crawl (1-10)
- `crawl_frequency` (String): Fréquence de crawl (daily, weekly, monthly)
- `last_crawled` (Date)`: Dernier crawl
- `crawl_status` (String): success, failed, pending
- `http_status` (Integer): Code HTTP
- `redirect_url` (String): URL de redirection (si applicable)

### 4.2 SEO et Accessibilité
- `meta_robots` (String): Instructions pour robots
- `canonical_url` (String): URL canonique
- `hreflang` (Array): Langues alternatives
- `accessibility_score` (Float): Score d'accessibilité (si calculé)

### 4.3 Analytics
- `page_views` (Integer): Nombre de vues
- `bounce_rate` (Float): Taux de rebond
- `avg_time_on_page` (Float): Temps moyen sur la page

## 5. Indizes et Constraints

### 5.1 Eindeutige Constraints
- `section_id` muss eindeutig sein
- `page_id` muss eindeutig sein (basé sur URL)
- `url` muss eindeutig sein dans Page

### 5.2 Indizes
- Index sur `section_id` pour navigation rapide
- Index sur `url` pour recherche rapide
- Index sur `parent_section_id` pour hiérarchie
- Index sur `level` pour filtrage par niveau
- Volltextindex sur `title`, `text_content` pour recherche
- Index sur `zielgruppen` pour filtrage par public cible
- Index sur `standorte` pour filtrage géographique

## 6. Mapping avec l'Ontologie Générale

### 6.1 Correspondances
- `Section` → peut mapper vers `Fachbereich`, `Serviceeinrichtung`, etc.
- `Page` → peut contenir des informations sur `Studiengang`, `Veranstaltung`, etc.
- `Standort` → correspond à `Campus` dans l'ontologie générale
- `Fachbereich` → correspond directement

### 6.2 Enrichissement
Les pages peuvent être enrichies avec des entités de l'ontologie générale:
- Extraction de `Studiengang` depuis les pages de Studiengänge
- Extraction de `Veranstaltung` depuis les pages d'événements
- Extraction de `Kontaktperson` depuis les pages de contact
- Extraction de `Dokument` depuis les liens PDF

## 7. Utilisation pour le Chatbot

### 7.1 Navigation Contextuelle
- Utiliser la hiérarchie des sections pour suggérer des pages pertinentes
- Utiliser les relations `VERWANDTE_SEITE` pour recommandations

### 7.2 Recherche Sémantique
- Rechercher dans `text_content` avec contexte de section
- Filtrer par `zielgruppen` pour personnalisation
- Filtrer par `standorte` pour localisation

### 7.3 Intent Mapping
- Mapper les intents vers les sections appropriées
- Utiliser `section_id` pour routing intelligent

Cette ontologie reflète fidèlement la structure réelle du site web et peut être utilisée pour:
- Guider le crawling vers les sections importantes
- Organiser le contenu crawlé
- Améliorer la recherche et la navigation
- Personnaliser les réponses du chatbot selon la section

