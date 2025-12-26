# Ontologie für Öffentliche Universitäts-Informationen (Public University Information Ontology)

Diese Ontologie definiert alle Knotentypen, Eigenschaften und Beziehungen für öffentlich zugängliche Informationen einer Universität, die für einen öffentlichen Chatbot relevant sind.

## 1. Knotentypen (Node Types)

### 1.1 Institutionelle Informationen (Institutional Information)

#### 1.1.1 Hochschule (University - Public Profile)
**Eigenschaften:**
- `hochschule_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Vollständiger Name
- `kurzname` (String): Kurzname/Abkürzung
- `typ` (String): Universität, Fachhochschule, Hochschule
- `motto` (String): Motto der Hochschule
- `mission` (Text): Mission Statement
- `vision` (Text): Vision Statement
- `werte` (Text): Werte und Leitbild
- `geschichte` (Text): Geschichte der Hochschule
- `gruendungsjahr` (Integer): Gründungsjahr
- `rechtsform` (String): Rechtsform
- `traeger` (String): Träger (staatlich, privat, kirchlich)
- `anzahl_studierende` (Integer): Aktuelle Anzahl der Studierenden (öffentlich)
- `anzahl_mitarbeiter` (Integer): Anzahl der Mitarbeiter (öffentlich)
- `anzahl_professoren` (Integer): Anzahl der Professoren (öffentlich)
- `anzahl_studiengaenge` (Integer): Anzahl der Studiengänge
- `anzahl_fachbereiche` (Integer): Anzahl der Fachbereiche
- `website` (String): Hauptwebsite-URL
- `logo_url` (String): URL zum Logo
- `social_media` (JSON): Social Media Links (Facebook, Twitter, LinkedIn, Instagram, etc.)

#### 1.1.2 Standort (Location)
**Eigenschaften:**
- `standort_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name des Standorts
- `adresse` (String): Vollständige Adresse
- `postleitzahl` (String): PLZ
- `stadt` (String): Stadt
- `land` (String): Land
- `koordinaten_lat` (Float): Breitengrad
- `koordinaten_lng` (Float): Längengrad
- `telefon` (String): Haupttelefonnummer
- `email` (String): Haupt-E-Mail-Adresse
- `oeffnungszeiten` (Text): Öffnungszeiten
- `anfahrt_beschreibung` (Text): Beschreibung der Anfahrt
- `parkplaetze` (Text): Informationen zu Parkplätzen
- `oeffentliche_verkehrsmittel` (Text): ÖPNV-Verbindungen
- `hochschule_id` (String): Referenz zur Hochschule
- `bild_url` (String): URL zum Standortbild

#### 1.1.3 Campus (Campus - Public)
**Eigenschaften:**
- `campus_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name des Campus
- `adresse` (String): Adresse
- `postleitzahl` (String): PLZ
- `stadt` (String): Stadt
- `flaeche` (Float): Gesamtfläche in m² (öffentlich)
- `anzahl_gebaeude` (Integer): Anzahl der Gebäude
- `campusplan_url` (String): URL zum Campusplan
- `virtueller_rundgang_url` (String): URL zum virtuellen Rundgang (optional)
- `hochschule_id` (String): Referenz zur Hochschule
- `beschreibung` (Text): Beschreibung des Campus

#### 1.1.4 Gebäude (Building - Public)
**Eigenschaften:**
- `gebaeude_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name des Gebäudes
- `nummer` (String): Gebäudenummer
- `adresse` (String): Adresse
- `campus_id` (String): Referenz zum Campus
- `baujahr` (Integer): Baujahr (öffentlich)
- `nutzung` (Text): Hauptnutzung (öffentlich)
- `bild_url` (String): URL zum Gebäudebild
- `beschreibung` (Text): Beschreibung

### 1.2 Fachbereiche und Organisationen (Departments and Organizations - Public)

#### 1.2.1 Fachbereich (Department - Public Profile)
**Eigenschaften:**
- `fachbereich_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name des Fachbereichs
- `kurzname` (String): Kurzname/Abkürzung
- `beschreibung` (Text): Öffentliche Beschreibung
- `schwerpunkte` (Text): Forschungsschwerpunkte (öffentlich)
- `adresse` (String): Adresse
- `telefon` (String): Telefonnummer
- `email` (String): E-Mail-Adresse
- `website` (String): Website-URL
- `dekan_name` (String): Name des Dekans (öffentlich)
- `dekan_email` (String): E-Mail des Dekans (öffentlich)
- `hochschule_id` (String): Referenz zur Hochschule
- `anzahl_studierende` (Integer): Anzahl der Studierenden (öffentlich)
- `anzahl_studiengaenge` (Integer): Anzahl der Studiengänge
- `logo_url` (String): URL zum Logo

#### 1.2.2 Institut (Institute - Public)
**Eigenschaften:**
- `institut_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name des Instituts
- `kurzname` (String): Kurzname/Abkürzung
- `beschreibung` (Text): Öffentliche Beschreibung
- `forschungsgebiet` (Text): Hauptforschungsgebiet (öffentlich)
- `adresse` (String): Adresse
- `telefon` (String): Telefonnummer
- `email` (String): E-Mail-Adresse
- `website` (String): Website-URL
- `leiter_name` (String): Name des Leiters (öffentlich)
- `fachbereich_id` (String): Referenz zum Fachbereich
- `logo_url` (String): URL zum Logo

#### 1.2.3 Serviceeinrichtung (Service Facility - Public)
**Eigenschaften:**
- `service_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name der Serviceeinrichtung
- `typ` (String): Bibliothek, Mensa, Studierenden-Servicebüro, Prüfungsamt, IT-Service, etc.
- `beschreibung` (Text): Beschreibung der Services
- `adresse` (String): Adresse
- `telefon` (String): Telefonnummer
- `email` (String): E-Mail-Adresse
- `website` (String): Website-URL
- `oeffnungszeiten` (Text): Öffnungszeiten
- `kontaktperson` (String): Ansprechpartner (öffentlich)
- `services` (Text): Liste der angebotenen Services
- `hochschule_id` (String): Referenz zur Hochschule
- `campus_id` (String): Referenz zum Campus (optional)

#### 1.2.4 Bibliothek (Library - Public)
**Eigenschaften:** (erbt von Serviceeinrichtung)
- `bibliothek_id` (String, eindeutig): Identifikationsnummer
- `anzahl_buecher` (Integer): Anzahl der Bücher (öffentlich)
- `anzahl_zeitschriften` (Integer): Anzahl der Zeitschriften (öffentlich)
- `anzahl_elektronische_medien` (Integer): Anzahl elektronischer Medien
- `anzahl_arbeitsplaetze` (Integer): Anzahl der Arbeitsplätze
- `ausleihe_online` (Boolean): Online-Ausleihe verfügbar
- `katalog_url` (String): URL zum Online-Katalog
- `regeln` (Text): Ausleihregeln (öffentlich)
- `events` (Text): Veranstaltungen (öffentlich)

#### 1.2.5 Mensa (Cafeteria - Public)
**Eigenschaften:** (erbt von Serviceeinrichtung)
- `mensa_id` (String, eindeutig): Identifikationsnummer
- `anzahl_plaetze` (Integer): Anzahl der Sitzplätze
- `speiseplan_url` (String): URL zum Speiseplan
- `preise` (Text): Preisinformationen (öffentlich)
- `zahlungsarten` (Text): Akzeptierte Zahlungsarten
- `allergene_info` (Text): Informationen zu Allergenen

### 1.3 Studiengänge (Study Programs - Public)

#### 1.3.1 Studiengang (Study Program - Public)
**Eigenschaften:**
- `studiengang_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Vollständiger Name
- `kurzname` (String): Kurzname/Abkürzung
- `abschluss` (String): Bachelor, Master, Diplom, Staatsexamen, Promotion
- `studienform` (String): Vollzeit, Teilzeit, Fernstudium, Dual
- `regelstudienzeit` (Integer): Regelstudienzeit in Semestern
- `ects_punkte` (Integer): Gesamt-ECTS-Punkte
- `sprache` (String): Unterrichtssprache (Deutsch, Englisch, etc.)
- `zulassungsbeschraenkt` (Boolean): Zulassungsbeschränkung (NC)
- `nc_wert_letztes_jahr` (Float): NC-Wert des letzten Jahres (öffentlich)
- `studienbeginn` (String): Wintersemester, Sommersemester, beides
- `fachbereich_id` (String): Referenz zum Fachbereich
- `beschreibung` (Text): Öffentliche Beschreibung des Studiengangs
- `inhalte` (Text): Studieninhalte (öffentlich)
- `aufbau` (Text): Studienaufbau/Struktur
- `berufsperspektiven` (Text): Berufsperspektiven
- `karrierebeispiele` (Text): Beispiele für Karrierewege
- `voraussetzungen` (Text): Zulassungsvoraussetzungen
- `bewerbungsfrist` (Text): Bewerbungsfristen
- `bewerbungsverfahren` (Text): Bewerbungsverfahren
- `kosten` (Text): Studiengebühren/Kosten (öffentlich)
- `stipendien` (Text): Verfügbare Stipendien
- `akkreditiert` (Boolean): Akkreditiert
- `akkreditierungsstelle` (String): Akkreditierungsstelle
- `website` (String): Studiengangs-Website
- `kontakt_email` (String): Kontakt-E-Mail
- `kontakt_telefon` (String): Kontakt-Telefon
- `modulhandbuch_url` (String): URL zum Modulhandbuch
- `pruefungsordnung_url` (String): URL zur Prüfungsordnung
- `studienverlaufsplan_url` (String): URL zum Studienverlaufsplan
- `anzahl_studierende` (Integer): Aktuelle Anzahl (öffentlich)
- `bild_url` (String): URL zum Studiengangsbild

#### 1.3.2 Studienrichtung (Study Track/Specialization - Public)
**Eigenschaften:**
- `richtung_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name der Studienrichtung
- `beschreibung` (Text): Beschreibung
- `studiengang_id` (String): Referenz zum Studiengang
- `schwerpunkte` (Text): Schwerpunkte

#### 1.3.3 Modul (Module - Public Overview)
**Eigenschaften:**
- `modul_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name des Moduls
- `modulnummer` (String): Modulnummer
- `ects_punkte` (Integer): ECTS-Punkte
- `semester` (Integer): Empfohlenes Semester
- `pflichtmodul` (Boolean): Pflicht- oder Wahlmodul
- `studiengang_id` (String): Referenz zum Studiengang
- `beschreibung` (Text): Öffentliche Modulbeschreibung
- `lernziele` (Text): Lernziele (öffentlich)
- `inhalte` (Text): Modulinhalte (öffentlich)

### 1.4 Zulassung und Bewerbung (Admission and Application - Public)

#### 1.4.1 Zulassungsvoraussetzung (Admission Requirement)
**Eigenschaften:**
- `voraussetzung_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name der Voraussetzung
- `typ` (String): Abitur, Fachabitur, Berufserfahrung, Sprachtest, etc.
- `beschreibung` (Text): Detaillierte Beschreibung
- `nachweis_erforderlich` (Boolean): Nachweis erforderlich
- `studiengang_id` (String): Referenz zum Studiengang (optional, wenn allgemein)

#### 1.4.2 Bewerbungsfrist (Application Deadline)
**Eigenschaften:**
- `frist_id` (String, eindeutig): Identifikationsnummer
- `studiengang_id` (String): Referenz zum Studiengang
- `semester` (String): Wintersemester, Sommersemester
- `jahr` (Integer): Jahr
- `frist_start` (Date): Start der Bewerbungsfrist
- `frist_ende` (Date): Ende der Bewerbungsfrist
- `typ` (String): Bewerbung, Einschreibung, Rückmeldung
- `beschreibung` (Text): Zusätzliche Informationen

#### 1.4.3 Bewerbungsverfahren (Application Process)
**Eigenschaften:**
- `verfahren_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name des Verfahrens
- `typ` (String): Online, Papier, über Hochschulstart, etc.
- `beschreibung` (Text): Schritt-für-Schritt Beschreibung
- `dokumente_erforderlich` (Text): Liste der erforderlichen Dokumente
- `kosten` (Float): Bearbeitungsgebühr (öffentlich)
- `studiengang_id` (String): Referenz zum Studiengang (optional)
- `website_url` (String): URL zum Bewerbungsportal

#### 1.4.4 Numerus Clausus (NC - Public Information)
**Eigenschaften:**
- `nc_id` (String, eindeutig): Identifikationsnummer
- `studiengang_id` (String): Referenz zum Studiengang
- `semester` (String): Wintersemester, Sommersemester
- `jahr` (Integer): Jahr
- `nc_wert` (Float): NC-Wert
- `verfuegbare_plaetze` (Integer): Verfügbare Plätze
- `bewerbungen` (Integer): Anzahl der Bewerbungen
- `nachrueckverfahren` (Boolean): Nachrückverfahren vorhanden

### 1.5 Personen (People - Public Profiles)

#### 1.5.1 Professor (Professor - Public Profile)
**Eigenschaften:**
- `professor_id` (String, eindeutig): Identifikationsnummer
- `titel` (String): Prof. Dr., Prof., Dr., etc.
- `vorname` (String): Vorname
- `nachname` (String): Nachname
- `akademischer_grad` (String): Doktorgrad, Habilitation
- `fachgebiet` (String): Fachgebiet/Spezialisierung
- `forschungsgebiete` (Text): Forschungsgebiete (öffentlich)
- `email` (String): Öffentliche E-Mail-Adresse
- `telefon` (String): Telefonnummer (öffentlich)
- `buero` (String): Büronummer
- `sprechzeiten` (Text): Sprechzeiten (öffentlich)
- `fachbereich_id` (String): Referenz zum Fachbereich
- `institut_id` (String): Referenz zum Institut (optional)
- `website` (String): Persönliche Website (optional)
- `foto_url` (String): URL zum Foto (optional)
- `kurzbiografie` (Text): Kurzbiografie (öffentlich)

#### 1.5.2 Kontaktperson (Contact Person - Public)
**Eigenschaften:**
- `kontakt_id` (String, eindeutig): Identifikationsnummer
- `vorname` (String): Vorname
- `nachname` (String): Nachname
- `position` (String): Position/Jobtitel
- `abteilung` (String): Abteilung
- `email` (String): E-Mail-Adresse
- `telefon` (String): Telefonnummer
- `sprechzeiten` (Text): Sprechzeiten
- `zuständigkeit` (Text): Zuständigkeitsbereich
- `organisation_id` (String): Referenz zur Organisation

### 1.6 Veranstaltungen (Events - Public)

#### 1.6.1 Öffentliche Veranstaltung (Public Event)
**Eigenschaften:**
- `veranstaltung_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name der Veranstaltung
- `typ` (String): Tag der offenen Tür, Infoabend, Vortrag, Workshop, Konferenz, Messe, etc.
- `beschreibung` (Text): Beschreibung
- `datum_start` (Date): Startdatum
- `datum_ende` (Date): Enddatum
- `uhrzeit_start` (Time): Startzeit
- `uhrzeit_ende` (Time): Endzeit
- `ort` (String): Ort
- `adresse` (String): Adresse
- `raum_id` (String): Referenz zum Raum (optional)
- `organisator` (String): Organisator
- `kontakt_email` (String): Kontakt-E-Mail
- `kontakt_telefon` (String): Kontakt-Telefon
- `anmeldung_erforderlich` (Boolean): Anmeldung erforderlich
- `anmeldung_url` (String): URL zur Anmeldung
- `anmeldefrist` (Date): Anmeldefrist
- `max_teilnehmer` (Integer): Maximale Teilnehmerzahl
- `kosten` (Float): Teilnahmegebühr (0 wenn kostenlos)
- `oeffentlich` (Boolean): Öffentlich zugänglich
- `zielgruppe` (String): Zielgruppe (Studieninteressierte, Studierende, Öffentlichkeit, etc.)
- `bild_url` (String): URL zum Veranstaltungsbild
- `website_url` (String): Weitere Informationen

#### 1.6.2 Vortrag (Lecture/Talk - Public)
**Eigenschaften:** (erbt von Öffentliche Veranstaltung)
- `vortrag_id` (String, eindeutig): Identifikationsnummer
- `referent_name` (String): Name des Referenten
- `referent_affiliation` (String): Zugehörigkeit des Referenten
- `thema` (String): Thema des Vortrags
- `abstract` (Text): Abstract
- `dauer_minuten` (Integer): Dauer in Minuten
- `sprache` (String): Sprache des Vortrags

#### 1.6.3 Tag der offenen Tür (Open Day)
**Eigenschaften:** (erbt von Öffentliche Veranstaltung)
- `tag_id` (String, eindeutig): Identifikationsnummer
- `programm_url` (String): URL zum Programm
- `fuehrungen` (Boolean): Führungen verfügbar
- `beratung` (Boolean): Studienberatung verfügbar

### 1.7 Aktuelles und News (News and Current Information)

#### 1.7.1 News-Artikel (News Article)
**Eigenschaften:**
- `artikel_id` (String, eindeutig): Identifikationsnummer
- `titel` (String): Titel des Artikels
- `untertitel` (String): Untertitel
- `inhalt` (Text): Vollständiger Inhalt
- `zusammenfassung` (Text): Kurze Zusammenfassung
- `autor` (String): Autor
- `veroeffentlichungsdatum` (Date): Veröffentlichungsdatum
- `kategorie` (String): Kategorie (Forschung, Lehre, Veranstaltung, etc.)
- `schluesselwoerter` (Text): Schlagwörter
- `bild_url` (String): URL zum Titelbild
- `quelle_url` (String): URL zum Originalartikel
- `fachbereich_id` (String): Referenz zum Fachbereich (optional)
- `veranstaltung_id` (String): Referenz zur Veranstaltung (optional)

#### 1.7.2 Pressemitteilung (Press Release)
**Eigenschaften:** (erbt von News-Artikel)
- `pressemitteilung_id` (String, eindeutig): Identifikationsnummer
- `ansprechpartner` (String): Ansprechpartner für Presse
- `kontakt_email` (String): Pressekontakt-E-Mail
- `kontakt_telefon` (String): Pressekontakt-Telefon

### 1.8 Forschung (Research - Public Information)

#### 1.8.1 Forschungsprojekt (Research Project - Public)
**Eigenschaften:**
- `projekt_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name des Projekts
- `beschreibung` (Text): Öffentliche Projektbeschreibung
- `startdatum` (Date): Startdatum
- `enddatum` (Date): Enddatum (optional)
- `status` (String): geplant, laufend, abgeschlossen
- `foerdergeber` (String): Fördergeber (öffentlich)
- `foerderbetrag` (Float): Förderbetrag in Euro (öffentlich, optional)
- `projektleiter_name` (String): Name des Projektleiters (öffentlich)
- `fachbereich_id` (String): Referenz zum Fachbereich
- `institut_id` (String): Referenz zum Institut (optional)
- `schluesselwoerter` (Text): Schlagwörter
- `website_url` (String): Projektwebsite (optional)
- `beteiligte_partner` (Text): Beteiligte Partner (öffentlich)

#### 1.8.2 Forschungsgebiet (Research Area - Public)
**Eigenschaften:**
- `gebiet_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name des Forschungsgebiets
- `beschreibung` (Text): Beschreibung
- `fachbereich_id` (String): Referenz zum Fachbereich
- `projekte_anzahl` (Integer): Anzahl der Projekte (öffentlich)

#### 1.8.3 Publikation (Publication - Public)
**Eigenschaften:**
- `publikation_id` (String, eindeutig): Identifikationsnummer
- `titel` (String): Titel der Publikation
- `typ` (String): Buch, Artikel, Konferenzbeitrag, etc.
- `jahr` (Integer): Erscheinungsjahr
- `verlag` (String): Verlag
- `zeitschrift` (String): Zeitschrift (optional)
- `isbn` (String): ISBN (optional)
- `issn` (String): ISSN (optional)
- `doi` (String): DOI (optional)
- `abstract` (Text): Abstract (öffentlich)
- `schluesselwoerter` (Text): Schlagwörter
- `sprache` (String): Sprache
- `pdf_url` (String): URL zum PDF (öffentlich, optional)
- `url` (String): URL (optional)
- `autoren` (Text): Liste der Autoren (öffentlich)
- `fachbereich_id` (String): Referenz zum Fachbereich (optional)

### 1.9 FAQ und Hilfe (FAQ and Help)

#### 1.9.1 FAQ-Eintrag (FAQ Entry)
**Eigenschaften:**
- `faq_id` (String, eindeutig): Identifikationsnummer
- `frage` (String): Häufig gestellte Frage
- `antwort` (Text): Antwort
- `kategorie` (String): Kategorie (Bewerbung, Einschreibung, Studium, etc.)
- `schluesselwoerter` (Text): Schlagwörter für Suche
- `relevanz` (Integer): Relevanz-Ranking
- `aufrufe` (Integer): Anzahl der Aufrufe
- `zuletzt_aktualisiert` (Date): Letztes Update

#### 1.9.2 Hilfeartikel (Help Article)
**Eigenschaften:**
- `artikel_id` (String, eindeutig): Identifikationsnummer
- `titel` (String): Titel des Artikels
- `inhalt` (Text): Vollständiger Inhalt
- `kategorie` (String): Kategorie
- `schluesselwoerter` (Text): Schlagwörter
- `schwierigkeit` (String): Einfach, Mittel, Schwer
- `dauer_minuten` (Integer): Geschätzte Lesezeit
- `zuletzt_aktualisiert` (Date): Letztes Update

#### 1.9.3 Anleitung (Guide/Tutorial)
**Eigenschaften:**
- `anleitung_id` (String, eindeutig): Identifikationsnummer
- `titel` (String): Titel der Anleitung
- `beschreibung` (Text): Beschreibung
- `schritte` (JSON): Schritt-für-Schritt Anleitung
- `kategorie` (String): Kategorie
- `video_url` (String): URL zum Video (optional)
- `pdf_url` (String): URL zum PDF (optional)

### 1.10 Formulare und Dokumente (Forms and Documents - Public)

#### 1.10.1 Öffentliches Formular (Public Form)
**Eigenschaften:**
- `formular_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name des Formulars
- `typ` (String): Bewerbung, Anfrage, Anmeldung, etc.
- `beschreibung` (Text): Beschreibung
- `version` (String): Version
- `pdf_url` (String): URL zum PDF-Formular
- `online_formular_url` (String): URL zum Online-Formular (optional)
- `ausfuellhilfe` (Text): Ausfüllhilfe
- `einreichung` (Text): Informationen zur Einreichung
- `kosten` (Float): Bearbeitungsgebühr (0 wenn kostenlos)
- `gueltig_ab` (Date): Gültig ab
- `gueltig_bis` (Date): Gültig bis (optional)

#### 1.10.2 Öffentliches Dokument (Public Document)
**Eigenschaften:**
- `dokument_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name des Dokuments
- `typ` (String): Satzung, Ordnung, Richtlinie, Broschüre, etc.
- `beschreibung` (Text): Beschreibung
- `version` (String): Version
- `pdf_url` (String): URL zum PDF
- `gueltig_ab` (Date): Gültig ab
- `gueltig_bis` (Date): Gültig bis (optional)
- `kategorie` (String): Kategorie

#### 1.10.3 Broschüre (Brochure - Public)
**Eigenschaften:** (erbt von Öffentliches Dokument)
- `broschuere_id` (String, eindeutig): Identifikationsnummer
- `thema` (String): Thema der Broschüre
- `zielgruppe` (String): Zielgruppe
- `sprache` (String): Sprache
- `seiten` (Integer): Anzahl der Seiten
- `bestellbar` (Boolean): Physisch bestellbar
- `bestell_url` (String): URL zur Bestellung (optional)

### 1.11 Kontakt und Beratung (Contact and Counseling)

#### 1.11.1 Studienberatung (Study Counseling)
**Eigenschaften:**
- `beratung_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name der Beratungsstelle
- `typ` (String): Allgemeine Studienberatung, Fachstudienberatung, etc.
- `beschreibung` (Text): Beschreibung der Services
- `adresse` (String): Adresse
- `telefon` (String): Telefonnummer
- `email` (String): E-Mail-Adresse
- `website` (String): Website-URL
- `sprechzeiten` (Text): Sprechzeiten
- `anmeldung_erforderlich` (Boolean): Anmeldung erforderlich
- `anmeldung_url` (String): URL zur Anmeldung
- `online_beratung` (Boolean): Online-Beratung verfügbar
- `hochschule_id` (String): Referenz zur Hochschule
- `fachbereich_id` (String): Referenz zum Fachbereich (optional)

#### 1.11.2 Kontaktformular (Contact Form)
**Eigenschaften:**
- `kontaktformular_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name des Kontaktformulars
- `thema` (String): Thema/Bereich
- `url` (String): URL zum Kontaktformular
- `beschreibung` (Text): Beschreibung
- `antwortzeit` (String): Erwartete Antwortzeit

### 1.12 Leben und Campus (Life and Campus)

#### 1.12.1 Studentenleben (Student Life)
**Eigenschaften:**
- `leben_id` (String, eindeutig): Identifikationsnummer
- `thema` (String): Thema (Wohnen, Freizeit, Sport, Kultur, etc.)
- `beschreibung` (Text): Beschreibung
- `links` (JSON): Relevante Links
- `bild_url` (String): URL zum Bild
- `campus_id` (String): Referenz zum Campus (optional)

#### 1.12.2 Studentenverein (Student Organization)
**Eigenschaften:**
- `verein_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name des Vereins
- `typ` (String): Fachschaft, Sportverein, Kulturverein, etc.
- `beschreibung` (Text): Beschreibung
- `kontakt_email` (String): Kontakt-E-Mail
- `website` (String): Website (optional)
- `social_media` (JSON): Social Media Links
- `fachbereich_id` (String): Referenz zum Fachbereich (optional)

#### 1.12.3 Wohnheim (Student Dormitory)
**Eigenschaften:**
- `wohnheim_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name des Wohnheims
- `adresse` (String): Adresse
- `anzahl_zimmer` (Integer): Anzahl der Zimmer
- `kosten_pro_monat` (Float): Kosten pro Monat (öffentlich)
- `ausstattung` (Text): Ausstattung
- `kontakt` (String): Kontaktinformationen
- `website` (String): Website (optional)
- `verwaltet_von` (String): Verwaltet von (Studentenwerk, etc.)

### 1.13 Karriere und Jobs (Career and Jobs)

#### 1.13.1 Stellenausschreibung (Job Posting - Public)
**Eigenschaften:**
- `stelle_id` (String, eindeutig): Identifikationsnummer
- `titel` (String): Stellenbezeichnung
- `typ` (String): Wissenschaftlich, Verwaltung, Technisch, etc.
- `beschreibung` (Text): Stellenbeschreibung
- `anforderungen` (Text): Anforderungen
- `befristet` (Boolean): Befristet
- `befristung_bis` (Date): Befristung bis (optional)
- `stunden_pro_woche` (Integer): Stunden pro Woche
- `entgeltgruppe` (String): Entgeltgruppe (öffentlich, optional)
- `bewerbungsfrist` (Date): Bewerbungsfrist
- `kontakt_email` (String): Kontakt-E-Mail
- `bewerbung_url` (String): URL zur Bewerbung
- `veroeffentlichungsdatum` (Date): Veröffentlichungsdatum

#### 1.13.2 Karrieremöglichkeit (Career Opportunity)
**Eigenschaften:**
- `karriere_id` (String, eindeutig): Identifikationsnummer
- `titel` (String): Titel
- `beschreibung` (Text): Beschreibung
- `typ` (String): Promotion, Habilitation, Postdoc, etc.
- `fachbereich_id` (String): Referenz zum Fachbereich (optional)
- `kontakt` (String): Kontaktinformationen

### 1.14 Finanzen (Finance - Public)

#### 1.14.1 Semesterbeitrag (Semester Fee - Public)
**Eigenschaften:**
- `beitrag_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name des Beitrags (z.B. "Semesterbeitrag Wintersemester 2024/25")
- `betrag` (Float): Gesamtbetrag in Euro
- `semester` (String): Wintersemester, Sommersemester
- `jahr` (Integer): Jahr
- `gueltig_ab` (Date): Gültig ab
- `gueltig_bis` (Date): Gültig bis
- `zahlungsfrist` (Date): Zahlungsfrist
- `beschreibung` (Text): Beschreibung des Beitrags
- `bestandteile` (JSON): Aufschlüsselung der Bestandteile
  - `studierendenwerk` (Float): Beitrag für Studentenwerk
  - `semesterticket` (Float): Semesterticket
  - `verwaltung` (Float): Verwaltungsgebühr
  - `asta` (Float): AStA-Beitrag
  - `andere` (Float): Sonstige Beiträge
- `reduktion_moeglich` (Boolean): Reduktion möglich
- `befreiung_moeglich` (Boolean): Befreiung möglich
- `befreiungsgruende` (Text): Gründe für Befreiung
- `zahlungsmethoden` (Text): Akzeptierte Zahlungsmethoden
- `kontakt_email` (String): Kontakt-E-Mail für Fragen
- `kontakt_telefon` (String): Kontakt-Telefon
- `website_url` (String): URL zu weiteren Informationen

#### 1.14.2 Studiengebühr (Tuition Fee - Public)
**Eigenschaften:**
- `gebuehr_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name der Gebühr
- `betrag` (Float): Betrag in Euro
- `studienform` (String): Vollzeit, Teilzeit, Fernstudium
- `studiengang_id` (String): Referenz zum Studiengang (optional, wenn studiengangsspezifisch)
- `semester` (String): Wintersemester, Sommersemester
- `jahr` (Integer): Jahr
- `gueltig_ab` (Date): Gültig ab
- `gueltig_bis` (Date): Gültig bis
- `zahlungsfrist` (Date): Zahlungsfrist
- `beschreibung` (Text): Beschreibung
- `reduktion_moeglich` (Boolean): Reduktion möglich
- `befreiung_moeglich` (Boolean): Befreiung möglich
- `stundung_moeglich` (Boolean): Stundung möglich
- `zahlungsmethoden` (Text): Akzeptierte Zahlungsmethoden
- `ratenzahlung` (Boolean): Ratenzahlung möglich
- `ratenanzahl` (Integer): Anzahl der Raten (optional)
- `kontakt_email` (String): Kontakt-E-Mail
- `kontakt_telefon` (String): Kontakt-Telefon

#### 1.14.3 Gebührenordnung (Fee Regulation - Public)
**Eigenschaften:**
- `ordnung_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name der Gebührenordnung
- `version` (String): Version
- `gueltig_ab` (Date): Gültig ab
- `gueltig_bis` (Date): Gültig bis (optional)
- `beschreibung` (Text): Beschreibung
- `pdf_url` (String): URL zum PDF-Dokument
- `website_url` (String): URL zu weiteren Informationen
- `aenderungen` (Text): Wichtige Änderungen
- `kontakt_email` (String): Kontakt-E-Mail für Fragen

#### 1.14.4 Gebührenbestandteil (Fee Component - Public)
**Eigenschaften:**
- `bestandteil_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name des Bestandteils (z.B. "Studentenwerk", "Semesterticket", etc.)
- `beschreibung` (Text): Beschreibung des Bestandteils
- `betrag` (Float): Betrag in Euro
- `pflicht` (Boolean): Pflichtbestandteil
- `wahlweise` (Boolean): Wahlweise
- `semester` (String): Wintersemester, Sommersemester
- `jahr` (Integer): Jahr
- `website_url` (String): URL zu weiteren Informationen
- `kontakt` (String): Kontaktinformationen

#### 1.14.5 Stipendium (Scholarship - Public)
**Eigenschaften:**
- `stipendium_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name des Stipendiums
- `geber` (String): Stipendiengeber (Hochschule, Stiftung, Unternehmen, etc.)
- `typ` (String): Leistungsstipendium, Bedarfsstipendium, Studienabschlussstipendium, etc.
- `beschreibung` (Text): Beschreibung
- `betrag_monatlich` (Float): Monatlicher Betrag in Euro
- `betrag_gesamt` (Float): Gesamtbetrag (optional)
- `laufzeit_monate` (Integer): Laufzeit in Monaten
- `verlaengerbar` (Boolean): Verlängerbar
- `voraussetzungen` (Text): Voraussetzungen
- `notendurchschnitt` (Float): Erforderlicher Notendurchschnitt (optional)
- `einkommensgrenze` (Float): Einkommensgrenze (optional)
- `studiengang_spezifisch` (Boolean): Studiengangsspezifisch
- `studiengang_id` (String): Referenz zum Studiengang (optional)
- `fachbereich_id` (String): Referenz zum Fachbereich (optional)
- `bewerbungsfrist` (Date): Bewerbungsfrist
- `bewerbungsverfahren` (Text): Bewerbungsverfahren
- `dokumente_erforderlich` (Text): Erforderliche Dokumente
- `kontakt_email` (String): Kontakt-E-Mail
- `kontakt_telefon` (String): Kontakt-Telefon
- `website_url` (String): URL zu weiteren Informationen
- `bewerbung_url` (String): URL zur Bewerbung
- `anzahl_verfuegbar` (Integer): Anzahl verfügbarer Stipendien (optional)

#### 1.14.6 Finanzierungsmöglichkeit (Financing Option - Public)
**Eigenschaften:**
- `finanzierung_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name der Finanzierungsmöglichkeit
- `typ` (String): BAföG, KfW-Studienkredit, Bildungskredit, Stipendium, etc.
- `beschreibung` (Text): Beschreibung
- `voraussetzungen` (Text): Voraussetzungen
- `betrag_max` (Float): Maximaler Betrag (optional)
- `zins` (Float): Zinssatz (optional)
- `rueckzahlung` (Text): Informationen zur Rückzahlung
- `laufzeit` (Text): Laufzeit
- `kontakt_email` (String): Kontakt-E-Mail
- `kontakt_telefon` (String): Kontakt-Telefon
- `website_url` (String): URL zu weiteren Informationen
- `antrag_url` (String): URL zum Antrag
- `beratung_verfuegbar` (Boolean): Beratung verfügbar

#### 1.14.7 Zahlungsmethode (Payment Method - Public)
**Eigenschaften:**
- `zahlungsmethode_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name der Zahlungsmethode (Überweisung, Lastschrift, Kreditkarte, etc.)
- `beschreibung` (Text): Beschreibung
- `verfuegbar_fuer` (Text): Verfügbar für (Semesterbeitrag, Studiengebühr, etc.)
- `gebuehren` (Float): Zusätzliche Gebühren (0 wenn kostenlos)
- `bearbeitungszeit` (String): Bearbeitungszeit
- `anleitung_url` (String): URL zur Anleitung
- `kontakt` (String): Kontakt bei Problemen

#### 1.14.8 Rückerstattung (Refund - Public Information)
**Eigenschaften:**
- `rueckerstattung_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name der Rückerstattungsregelung
- `typ` (String): Semesterbeitrag, Studiengebühr, etc.
- `beschreibung` (Text): Beschreibung der Rückerstattungsregelung
- `voraussetzungen` (Text): Voraussetzungen für Rückerstattung
- `frist` (Date): Frist für Antrag
- `prozentsatz` (Float): Prozentsatz der Rückerstattung (0-100)
- `antrag_erforderlich` (Boolean): Antrag erforderlich
- `antrag_formular_url` (String): URL zum Antragsformular
- `kontakt_email` (String): Kontakt-E-Mail
- `kontakt_telefon` (String): Kontakt-Telefon
- `bearbeitungszeit` (String): Bearbeitungszeit

#### 1.14.9 Finanzberatung (Financial Counseling - Public)
**Eigenschaften:**
- `beratung_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name der Beratungsstelle
- `beschreibung` (Text): Beschreibung der Services
- `adresse` (String): Adresse
- `telefon` (String): Telefonnummer
- `email` (String): E-Mail-Adresse
- `website` (String): Website-URL
- `sprechzeiten` (Text): Sprechzeiten
- `anmeldung_erforderlich` (Boolean): Anmeldung erforderlich
- `anmeldung_url` (String): URL zur Anmeldung
- `online_beratung` (Boolean): Online-Beratung verfügbar
- `themen` (Text): Beratungsthemen (BAföG, Stipendien, Studienkredit, etc.)
- `hochschule_id` (String): Referenz zur Hochschule

#### 1.14.10 Kostenübersicht (Cost Overview - Public)
**Eigenschaften:**
- `uebersicht_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name der Übersicht (z.B. "Kostenübersicht Wintersemester 2024/25")
- `semester` (String): Wintersemester, Sommersemester
- `jahr` (Integer): Jahr
- `studiengang_id` (String): Referenz zum Studiengang (optional)
- `gesamtkosten` (Float): Gesamtkosten pro Semester
- `aufschlüsselung` (JSON): Detaillierte Aufschlüsselung
  - `semesterbeitrag` (Float)
  - `studiengebuehr` (Float)
  - `materialkosten` (Float)
  - `lebenshaltungskosten` (Float)
  - `andere` (Float)
- `hinweise` (Text): Wichtige Hinweise
- `aktualisiert_am` (Date): Letztes Update
- `pdf_url` (String): URL zum PDF-Dokument

### 1.15 Partner und Kooperationen (Partners and Cooperations)

#### 1.14.1 Partnerorganisation (Partner Organization - Public)
**Eigenschaften:**
- `partner_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name der Organisation
- `typ` (String): Unternehmen, andere Hochschule, Forschungseinrichtung, etc.
- `beschreibung` (Text): Beschreibung der Partnerschaft
- `kooperationsart` (String): Forschung, Lehre, Praktikum, Duales Studium
- `logo_url` (String): URL zum Logo
- `website` (String): Website
- `seit` (Date): Partnerschaft seit

#### 1.14.2 Austauschprogramm (Exchange Program - Public)
**Eigenschaften:**
- `programm_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name des Programms (z.B. Erasmus+, etc.)
- `typ` (String): Erasmus+, DAAD, etc.
- `beschreibung` (Text): Beschreibung
- `partnerlaender` (Text): Partnerländer
- `voraussetzungen` (Text): Voraussetzungen
- `bewerbungsfrist` (Date): Bewerbungsfrist
- `kontakt_email` (String): Kontakt-E-Mail
- `website` (String): Website

## 2. Beziehungen (Relationships)

### 2.1 Institutionelle Beziehungen

- `HAT_STANDORT` (Hochschule → Standort)
  - Eigenschaften: `hauptstandort` (Boolean)
  
- `HAT_CAMPUS` (Hochschule → Campus)
  - Eigenschaften: `hauptcampus` (Boolean)
  
- `BEFINDET_SICH_AUF` (Gebäude → Campus)
  - Eigenschaften: `seit` (Date)
  
- `GEHOERT_ZU` (Fachbereich → Hochschule)
  - Eigenschaften: `seit` (Date)
  
- `IST_TEIL_VON` (Institut → Fachbereich)
  - Eigenschaften: `seit` (Date)

### 2.2 Studienbezogene Beziehungen

- `BIETET_AN` (Fachbereich → Studiengang)
  - Eigenschaften: `seit` (Date)
  
- `HAT_MODUL` (Studiengang → Modul)
  - Eigenschaften: `pflichtmodul` (Boolean), `semester` (Integer)
  
- `HAT_RICHTUNG` (Studiengang → Studienrichtung)
  - Eigenschaften: `wahlpflicht` (Boolean)
  
- `ERFORDERT` (Studiengang → Zulassungsvoraussetzung)
  - Eigenschaften: `obligatorisch` (Boolean)
  
- `HAT_BEWERBUNGSFRIST` (Studiengang → Bewerbungsfrist)
  - Eigenschaften: `semester` (String)
  
- `HAT_NC` (Studiengang → Numerus Clausus)
  - Eigenschaften: `semester` (String), `jahr` (Integer)

### 2.3 Personenbeziehungen

- `ARBEITET_IN` (Professor → Fachbereich)
  - Eigenschaften: `seit` (Date), `funktion` (String)
  
- `LEITET` (Professor → Institut)
  - Eigenschaften: `seit` (Date)
  
- `IST_KONTAKTPERSON_FUER` (Kontaktperson → Organisation)
  - Eigenschaften: `zuständigkeit` (String)

### 2.4 Veranstaltungsbeziehungen

- `ORGANISIERT` (Fachbereich → Öffentliche Veranstaltung)
  - Eigenschaften: `rolle` (String)
  
- `FINDET_STATT_IM` (Öffentliche Veranstaltung → Raum)
  - Eigenschaften: `datum` (Date), `uhrzeit` (Time)
  
- `RICHTET_SICH_AN` (Öffentliche Veranstaltung → Zielgruppe)
  - Eigenschaften: `prioritaet` (String)

### 2.5 Forschungsbeziehungen

- `FORSCHT_IN` (Fachbereich → Forschungsgebiet)
  - Eigenschaften: `schwerpunkt` (Boolean)
  
- `DURCHFUEHRT` (Fachbereich → Forschungsprojekt)
  - Eigenschaften: `beteiligung` (String)
  
- `PUBLIZIERT` (Fachbereich → Publikation)
  - Eigenschaften: `jahr` (Integer)

### 2.6 Servicebeziehungen

- `BIETET_SERVICE` (Hochschule → Serviceeinrichtung)
  - Eigenschaften: `standort` (String)
  
- `IST_VERFÜGBAR_AN` (Serviceeinrichtung → Campus)
  - Eigenschaften: `oeffnungszeiten` (Text)

### 2.7 Dokumentenbeziehungen

- `GEHOERT_ZU` (Formular → Kategorie)
  - Eigenschaften: `version` (String)
  
- `REGELT` (Dokument → Prozess)
  - Eigenschaften: `gueltig_ab` (Date), `gueltig_bis` (Date)
  
- `IST_RELEVANT_FUER` (FAQ-Eintrag → Thema)
  - Eigenschaften: `relevanz` (Integer)

### 2.8 Kontaktbeziehungen

- `BIETET_BERATUNG` (Fachbereich → Studienberatung)
  - Eigenschaften: `typ` (String)
  
- `IST_ANSPRECHPARTNER_FUER` (Kontaktperson → Thema)
  - Eigenschaften: `zuständigkeit` (String)

### 2.9 Partnerbeziehungen

- `KOOPERIERT_MIT` (Hochschule → Partnerorganisation)
  - Eigenschaften: `art` (String), `seit` (Date)
  
- `BIETET_PROGRAMM` (Hochschule → Austauschprogramm)
  - Eigenschaften: `aktiv` (Boolean)

### 2.10 Finanzbeziehungen

- `ERHEBT` (Hochschule → Semesterbeitrag)
  - Eigenschaften: `semester` (String), `jahr` (Integer)
  
- `BESTEHT_AUS` (Semesterbeitrag → Gebührenbestandteil)
  - Eigenschaften: `betrag` (Float), `pflicht` (Boolean)
  
- `HAT_GEBUEHR` (Studiengang → Studiengebühr)
  - Eigenschaften: `semester` (String), `jahr` (Integer)
  
- `REGELT` (Gebührenordnung → Semesterbeitrag)
  - Eigenschaften: `version` (String), `gueltig_ab` (Date)
  
- `REGELT_GEBUEHR` (Gebührenordnung → Studiengebühr)
  - Eigenschaften: `version` (String), `gueltig_ab` (Date)
  
- `BIETET_STIPENDIUM` (Hochschule → Stipendium)
  - Eigenschaften: `aktiv` (Boolean), `anzahl_verfuegbar` (Integer)
  
- `IST_VERFUEGBAR_FUER` (Stipendium → Studiengang)
  - Eigenschaften: `prioritaet` (String)
  
- `IST_VERFUEGBAR_FUER_FB` (Stipendium → Fachbereich)
  - Eigenschaften: `prioritaet` (String)
  
- `BIETET_FINANZIERUNG` (Hochschule → Finanzierungsmöglichkeit)
  - Eigenschaften: `empfohlen` (Boolean)
  
- `AKZEPTIERT` (Semesterbeitrag → Zahlungsmethode)
  - Eigenschaften: `gebuehren` (Float)
  
- `AKZEPTIERT_GEBUEHR` (Studiengebühr → Zahlungsmethode)
  - Eigenschaften: `gebuehren` (Float)
  
- `HAT_RUECKERSTATTUNG` (Semesterbeitrag → Rückerstattung)
  - Eigenschaften: `prozentsatz` (Float), `frist` (Date)
  
- `HAT_RUECKERSTATTUNG_GEBUEHR` (Studiengebühr → Rückerstattung)
  - Eigenschaften: `prozentsatz` (Float), `frist` (Date)
  
- `BIETET_BERATUNG` (Hochschule → Finanzberatung)
  - Eigenschaften: `kostenlos` (Boolean)
  
- `BERATET_ZU` (Finanzberatung → Finanzierungsmöglichkeit)
  - Eigenschaften: `schwerpunkt` (Boolean)
  
- `BERATET_STIPENDIEN` (Finanzberatung → Stipendium)
  - Eigenschaften: `schwerpunkt` (Boolean)
  
- `HAT_KOSTENUEBERSICHT` (Hochschule → Kostenübersicht)
  - Eigenschaften: `semester` (String), `jahr` (Integer)
  
- `HAT_KOSTENUEBERSICHT_STG` (Studiengang → Kostenübersicht)
  - Eigenschaften: `semester` (String), `jahr` (Integer)
  
- `ENTHAELT` (Kostenübersicht → Semesterbeitrag)
  - Eigenschaften: `betrag` (Float)
  
- `ENTHAELT_GEBUEHR` (Kostenübersicht → Studiengebühr)
  - Eigenschaften: `betrag` (Float)
  
- `VERWEIST_AUF` (Semesterbeitrag → Gebührenordnung)
  - Eigenschaften: `relevanz` (String)
  
- `VERWEIST_AUF_GEBUEHR` (Studiengebühr → Gebührenordnung)
  - Eigenschaften: `relevanz` (String)

### 2.11 News-Beziehungen

- `BEZIEHT_SICH_AUF` (News-Artikel → Thema)
  - Eigenschaften: `relevanz` (String)
  
- `GEHOERT_ZU` (News-Artikel → Kategorie)
  - Eigenschaften: `prioritaet` (Integer)
  
- `VERKNÜPFT_MIT` (News-Artikel → Veranstaltung)
  - Eigenschaften: `typ` (String)

## 3. Indizes und Suche

### 3.1 Volltextsuche
- Volltextindex auf `name`, `beschreibung`, `inhalt` in allen relevanten Knoten
- Volltextindex auf `frage`, `antwort` in FAQ-Einträgen
- Volltextindex auf `titel`, `abstract` in Publikationen

### 3.2 Spezielle Indizes
- Index auf `kategorie` für Filterung
- Index auf `schluesselwoerter` für Tag-basierte Suche
- Index auf `datum` für zeitliche Filterung
- Index auf `typ` für Typ-Filterung
- Index auf `status` für Status-Filterung

### 3.3 Eindeutige Constraints
- `hochschule_id` muss eindeutig sein
- `studiengang_id` muss eindeutig sein
- `veranstaltung_id` muss eindeutig sein
- `artikel_id` muss eindeutig sein
- `faq_id` muss eindeutig sein
- `beitrag_id` muss eindeutig sein
- `gebuehr_id` muss eindeutig sein
- `stipendium_id` muss eindeutig sein
- `finanzierung_id` muss eindeutig sein

## 4. Chatbot-spezifische Eigenschaften

### 4.1 Intent-Mapping
Jeder Knotentyp kann mit Chatbot-Intents verknüpft werden:
- `intent_kategorien` (JSON): Liste der zugeordneten Intents
- `antwort_template` (Text): Template für Chatbot-Antworten
- `relevanz_score` (Float): Relevanz-Score für Suche

### 4.2 FAQ-Optimierung
- `frage_varianten` (JSON): Verschiedene Formulierungen der Frage
- `kontext` (Text): Kontext für besseres Verständnis
- `verwandte_fragen` (Array): IDs verwandter Fragen

### 4.3 Mehrsprachigkeit
- `name_de`, `name_en` für alle Namen
- `beschreibung_de`, `beschreibung_en` für Beschreibungen
- `sprache` Feld für Sprachauswahl

## 5. Metadaten

### 5.1 Content-Management
- `erstellt_am` (Date): Erstellungsdatum
- `geaendert_am` (Date): Letztes Änderungsdatum
- `veroeffentlicht_am` (Date): Veröffentlichungsdatum
- `autor` (String): Autor/Verantwortlicher
- `version` (Integer): Versionsnummer

### 5.2 SEO und Sichtbarkeit
- `meta_titel` (String): Meta-Titel für SEO
- `meta_beschreibung` (Text): Meta-Beschreibung für SEO
- `meta_schluesselwoerter` (Text): Meta-Schlüsselwörter
- `url_slug` (String): URL-Slug
- `sichtbar` (Boolean): Öffentlich sichtbar

### 5.3 Analytics
- `aufrufe` (Integer): Anzahl der Aufrufe
- `letzter_aufruf` (Date): Letzter Aufruf
- `durchschnittliche_verweilzeit` (Float): Durchschnittliche Verweilzeit
- `bounce_rate` (Float): Bounce Rate

## 6. Validierungsregeln

- URLs müssen valide sein
- E-Mail-Adressen müssen valide sein
- Datumsfelder müssen gültige Daten sein
- Telefonnummern müssen valide formatiert sein
- Koordinaten müssen im gültigen Bereich sein
- Beträge müssen nicht-negativ sein

## 7. Erweiterte Konzepte für Chatbot

### 7.1 Konversationskontext
- `kontext_knoten` (Array): Verwandte Knoten für Kontext
- `naechste_fragen` (Array): Empfohlene Folgefragen
- `verwandte_themen` (Array): Verwandte Themen

### 7.2 Antwort-Generierung
- `antwort_kurz` (Text): Kurze Antwort (1-2 Sätze)
- `antwort_mittel` (Text): Mittlere Antwort (Absatz)
- `antwort_lang` (Text): Ausführliche Antwort
- `zusammenfassung` (Text): Zusammenfassung für Quick-Info

### 7.3 Personalisierung
- `zielgruppe` (String): Zielgruppe (Studieninteressierte, Studierende, Eltern, etc.)
- `sprachniveau` (String): Sprachniveau (einfach, mittel, fortgeschritten)
- `interesse_gebiet` (String): Interessensgebiet

Diese Ontologie ist speziell für öffentliche Informationen optimiert und unterstützt einen Chatbot, der Besuchern der Universitätswebsite hilft, schnell und präzise Antworten auf ihre Fragen zu finden.

