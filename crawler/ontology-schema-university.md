# Ontologie für Universitäts-Wissensgraph

Diese Ontologie definiert alle Knotentypen, Eigenschaften und Beziehungen für einen umfassenden Wissensgraph einer Universität.

## 1. Knotentypen (Node Types)

### 1.1 Personen (Personen)

#### 1.1.1 Studierende (Student)
**Eigenschaften:**
- `student_id` (String, eindeutig): Matrikelnummer
- `vorname` (String): Vorname
- `nachname` (String): Nachname
- `geburtsdatum` (Date): Geburtsdatum
- `geschlecht` (String): männlich, weiblich, divers
- `nationalitaet` (String): Nationalität
- `email` (String): E-Mail-Adresse
- `telefon` (String): Telefonnummer
- `adresse` (String): Wohnadresse
- `postleitzahl` (String): PLZ
- `stadt` (String): Stadt
- `land` (String): Land
- `einschreibungsdatum` (Date): Datum der Einschreibung
- `exmatrikulationsdatum` (Date): Datum der Exmatrikulation (optional)
- `status` (String): aktiv, beurlaubt, exmatrikuliert, abgeschlossen
- `studienform` (String): Vollzeit, Teilzeit, Fernstudium
- `semesteranzahl` (Integer): Anzahl der Hochschulsemester
- `fachsemester` (Integer): Anzahl der Fachsemester
- `studienbeginn` (Date): Semester des Studienbeginns
- `studienende` (Date): Semester des Studienendes (optional)
- `notendurchschnitt` (Float): Aktueller Notendurchschnitt
- `ects_punkte` (Integer): Gesammelte ECTS-Punkte
- `studiengang_id` (String): Referenz zum Studiengang
- `fachbereich_id` (String): Referenz zum Fachbereich
- `hochschule_id` (String): Referenz zur Hochschule

#### 1.1.2 Jungstudierende (Young Student)
**Eigenschaften:** (erbt von Studierende)
- `schule` (String): Name der besuchten Schule
- `begabungsnachweis` (String): Nachweis besonderer Begabung
- `zulassungsdatum` (Date): Datum der Zulassung als Jungstudierender

#### 1.1.3 Zweithörer (Second Listener)
**Eigenschaften:** (erbt von Studierende)
- `herkunftshochschule` (String): Name der ursprünglichen Hochschule
- `zulassungsart` (String): kleiner Zweithörer, großer Zweithörer
- `zweithoererbeitrag_bezahlt` (Boolean): Status der Beitragszahlung

#### 1.1.4 Gasthörer (Guest Listener)
**Eigenschaften:**
- `gasthoerer_id` (String, eindeutig): Identifikationsnummer
- `vorname` (String): Vorname
- `nachname` (String): Nachname
- `email` (String): E-Mail-Adresse
- `zulassungsdatum` (Date): Datum der Zulassung
- `qualifikationsnachweis` (String): Qualifikationsnachweis (optional)

#### 1.1.5 Professor (Professor)
**Eigenschaften:**
- `professor_id` (String, eindeutig): Personalnummer
- `titel` (String): Prof. Dr., Prof., Dr., etc.
- `vorname` (String): Vorname
- `nachname` (String): Nachname
- `akademischer_grad` (String): Doktorgrad, Habilitation
- `fachgebiet` (String): Fachgebiet/Spezialisierung
- `email` (String): E-Mail-Adresse
- `telefon` (String): Telefonnummer
- `buero` (String): Büronummer
- `beschaeftigungsart` (String): Vollzeit, Teilzeit, Honorarprofessor
- `einstellungsdatum` (Date): Datum der Einstellung
- `ruhestand` (Boolean): Im Ruhestand
- `ruhestand_datum` (Date): Datum des Ruhestands (optional)
- `fachbereich_id` (String): Referenz zum Fachbereich
- `institut_id` (String): Referenz zum Institut (optional)
- `lehrstuhl` (String): Name des Lehrstuhls (optional)

#### 1.1.6 Dozent (Lecturer)
**Eigenschaften:**
- `dozent_id` (String, eindeutig): Personalnummer
- `titel` (String): Dr., M.A., etc.
- `vorname` (String): Vorname
- `nachname` (String): Nachname
- `akademischer_grad` (String): Akademischer Grad
- `fachgebiet` (String): Fachgebiet
- `email` (String): E-Mail-Adresse
- `telefon` (String): Telefonnummer
- `beschaeftigungsart` (String): Vollzeit, Teilzeit, Honorardozent
- `einstellungsdatum` (Date): Datum der Einstellung
- `fachbereich_id` (String): Referenz zum Fachbereich

#### 1.1.7 Wissenschaftlicher Mitarbeiter (Research Assistant)
**Eigenschaften:**
- `mitarbeiter_id` (String, eindeutig): Personalnummer
- `titel` (String): Dr., M.Sc., etc.
- `vorname` (String): Vorname
- `nachname` (String): Nachname
- `akademischer_grad` (String): Akademischer Grad
- `forschungsgebiet` (String): Forschungsgebiet
- `email` (String): E-Mail-Adresse
- `telefon` (String): Telefonnummer
- `beschaeftigungsart` (String): Vollzeit, Teilzeit, Doktorand
- `einstellungsdatum` (Date): Datum der Einstellung
- `projekt_id` (String): Referenz zum Forschungsprojekt (optional)
- `fachbereich_id` (String): Referenz zum Fachbereich

#### 1.1.8 Verwaltungspersonal (Administrative Staff)
**Eigenschaften:**
- `personal_id` (String, eindeutig): Personalnummer
- `vorname` (String): Vorname
- `nachname` (String): Nachname
- `position` (String): Position/Jobtitel
- `abteilung` (String): Verwaltungsabteilung
- `email` (String): E-Mail-Adresse
- `telefon` (String): Telefonnummer
- `beschaeftigungsart` (String): Vollzeit, Teilzeit
- `einstellungsdatum` (Date): Datum der Einstellung

#### 1.1.9 Dekan (Dean)
**Eigenschaften:** (erbt von Professor)
- `dekan_seit` (Date): Amtsantritt als Dekan
- `dekan_bis` (Date): Ende der Amtszeit (optional)
- `fachbereich_id` (String): Referenz zum Fachbereich

#### 1.1.10 Rektor (Rector)
**Eigenschaften:** (erbt von Professor)
- `rektor_seit` (Date): Amtsantritt als Rektor
- `rektor_bis` (Date): Ende der Amtszeit (optional)
- `hochschule_id` (String): Referenz zur Hochschule

#### 1.1.11 Prüfer (Examiner)
**Eigenschaften:** (kann Professor, Dozent oder externer Prüfer sein)
- `pruefer_id` (String, eindeutig): Identifikationsnummer
- `vorname` (String): Vorname
- `nachname` (String): Nachname
- `qualifikation` (String): Qualifikation als Prüfer
- `extern` (Boolean): Externer Prüfer
- `email` (String): E-Mail-Adresse

### 1.2 Organisationen (Organisationen)

#### 1.2.1 Hochschule (University)
**Eigenschaften:**
- `hochschule_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Vollständiger Name
- `kurzname` (String): Kurzname/Abkürzung
- `typ` (String): Universität, Fachhochschule, Hochschule
- `adresse` (String): Hauptadresse
- `postleitzahl` (String): PLZ
- `stadt` (String): Stadt
- `land` (String): Land
- `telefon` (String): Haupttelefonnummer
- `email` (String): Haupt-E-Mail-Adresse
- `website` (String): Website-URL
- `gruendungsjahr` (Integer): Gründungsjahr
- `rechtsform` (String): Rechtsform
- `traeger` (String): Träger (staatlich, privat, kirchlich)
- `anzahl_studierende` (Integer): Anzahl der Studierenden
- `anzahl_mitarbeiter` (Integer): Anzahl der Mitarbeiter
- `anzahl_professoren` (Integer): Anzahl der Professoren

#### 1.2.2 Fachbereich (Department/Faculty)
**Eigenschaften:**
- `fachbereich_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name des Fachbereichs
- `kurzname` (String): Kurzname/Abkürzung
- `adresse` (String): Adresse
- `telefon` (String): Telefonnummer
- `email` (String): E-Mail-Adresse
- `website` (String): Website-URL
- `dekan_id` (String): Referenz zum Dekan
- `hochschule_id` (String): Referenz zur Hochschule
- `anzahl_studierende` (Integer): Anzahl der Studierenden
- `anzahl_professoren` (Integer): Anzahl der Professoren

#### 1.2.3 Institut (Institute)
**Eigenschaften:**
- `institut_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name des Instituts
- `kurzname` (String): Kurzname/Abkürzung
- `adresse` (String): Adresse
- `telefon` (String): Telefonnummer
- `email` (String): E-Mail-Adresse
- `website` (String): Website-URL
- `leiter_id` (String): Referenz zum Institutsleiter
- `fachbereich_id` (String): Referenz zum Fachbereich
- `forschungsgebiet` (String): Hauptforschungsgebiet

#### 1.2.4 Lehrstuhl (Chair)
**Eigenschaften:**
- `lehrstuhl_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name des Lehrstuhls
- `inhaber_id` (String): Referenz zum Lehrstuhlinhaber (Professor)
- `fachbereich_id` (String): Referenz zum Fachbereich
- `forschungsgebiet` (String): Forschungsgebiet

#### 1.2.5 Verwaltungsabteilung (Administrative Department)
**Eigenschaften:**
- `abteilung_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name der Abteilung
- `aufgabe` (String): Hauptaufgabe
- `leiter_id` (String): Referenz zum Abteilungsleiter
- `hochschule_id` (String): Referenz zur Hochschule
- `telefon` (String): Telefonnummer
- `email` (String): E-Mail-Adresse

#### 1.2.6 Studierenden-Servicebüro (Student Services Office)
**Eigenschaften:**
- `servicebuer_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name des Servicebüros
- `adresse` (String): Adresse
- `telefon` (String): Telefonnummer
- `email` (String): E-Mail-Adresse
- `oeffnungszeiten` (String): Öffnungszeiten
- `hochschule_id` (String): Referenz zur Hochschule

#### 1.2.7 Bibliothek (Library)
**Eigenschaften:**
- `bibliothek_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name der Bibliothek
- `adresse` (String): Adresse
- `telefon` (String): Telefonnummer
- `email` (String): E-Mail-Adresse
- `website` (String): Website-URL
- `oeffnungszeiten` (String): Öffnungszeiten
- `anzahl_buecher` (Integer): Anzahl der Bücher
- `anzahl_zeitschriften` (Integer): Anzahl der Zeitschriften
- `hochschule_id` (String): Referenz zur Hochschule

#### 1.2.8 Mensa (Cafeteria)
**Eigenschaften:**
- `mensa_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name der Mensa
- `adresse` (String): Adresse
- `oeffnungszeiten` (String): Öffnungszeiten
- `anzahl_plaetze` (Integer): Anzahl der Sitzplätze
- `hochschule_id` (String): Referenz zur Hochschule

#### 1.2.9 Prüfungsamt (Examination Office)
**Eigenschaften:**
- `pruefungsamt_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name des Prüfungsamts
- `adresse` (String): Adresse
- `telefon` (String): Telefonnummer
- `email` (String): E-Mail-Adresse
- `fachbereich_id` (String): Referenz zum Fachbereich
- `oeffnungszeiten` (String): Öffnungszeiten

### 1.3 Studiengänge und Kurse (Study Programs and Courses)

#### 1.3.1 Studiengang (Study Program)
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
- `nc_wert` (Float): Numerus Clausus Wert (optional)
- `studienbeginn` (String): Wintersemester, Sommersemester, beides
- `fachbereich_id` (String): Referenz zum Fachbereich
- `akkreditiert` (Boolean): Akkreditiert
- `akkreditierungsdatum` (Date): Datum der Akkreditierung
- `akkreditierungsstelle` (String): Akkreditierungsstelle
- `beschreibung` (Text): Beschreibung des Studiengangs
- `berufsperspektiven` (Text): Berufsperspektiven
- `anzahl_studierende` (Integer): Aktuelle Anzahl der Studierenden

#### 1.3.2 Modul (Module)
**Eigenschaften:**
- `modul_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name des Moduls
- `kurzname` (String): Kurzname/Abkürzung
- `modulnummer` (String): Modulnummer
- `ects_punkte` (Integer): ECTS-Punkte
- `semester` (Integer): Empfohlenes Semester
- `pflichtmodul` (Boolean): Pflicht- oder Wahlmodul
- `studiengang_id` (String): Referenz zum Studiengang
- `verantwortlich_id` (String): Referenz zum verantwortlichen Professor
- `beschreibung` (Text): Modulbeschreibung
- `lernziele` (Text): Lernziele
- `voraussetzungen` (Text): Voraussetzungen

#### 1.3.3 Lehrveranstaltung (Course)
**Eigenschaften:**
- `lehrveranstaltung_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name der Lehrveranstaltung
- `typ` (String): Vorlesung, Seminar, Übung, Praktikum, Projekt, Kolloquium
- `semester` (String): Wintersemester 2024, Sommersemester 2025, etc.
- `wochentag` (String): Wochentag
- `uhrzeit_start` (Time): Startzeit
- `uhrzeit_ende` (Time): Endzeit
- `rhythmus` (String): wöchentlich, 14-tägig, Blockveranstaltung
- `sprache` (String): Unterrichtssprache
- `max_teilnehmer` (Integer): Maximale Teilnehmerzahl
- `aktuelle_teilnehmer` (Integer): Aktuelle Teilnehmerzahl
- `sws` (Integer): Semesterwochenstunden
- `ects_punkte` (Integer): ECTS-Punkte
- `modul_id` (String): Referenz zum Modul
- `dozent_id` (String): Referenz zum Dozenten
- `raum_id` (String): Referenz zum Raum
- `beschreibung` (Text): Beschreibung
- `anmeldung_erforderlich` (Boolean): Anmeldung erforderlich
- `anmeldefrist` (Date): Anmeldefrist (optional)

#### 1.3.4 Kursmaterial (Course Material)
**Eigenschaften:**
- `material_id` (String, eindeutig): Identifikationsnummer
- `titel` (String): Titel des Materials
- `typ` (String): Skript, Folien, Video, Audio, Buch, Artikel, Link
- `dateiname` (String): Dateiname
- `dateipfad` (String): Pfad zur Datei
- `dateigroesse` (Integer): Dateigröße in Bytes
- `mime_type` (String): MIME-Typ
- `hochgeladen_am` (Date): Upload-Datum
- `hochgeladen_von_id` (String): Referenz zur Person
- `lehrveranstaltung_id` (String): Referenz zur Lehrveranstaltung
- `oeffentlich` (Boolean): Öffentlich zugänglich

### 1.4 Prüfungen (Examinations)

#### 1.4.1 Prüfung (Examination)
**Eigenschaften:**
- `pruefung_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name der Prüfung
- `typ` (String): Klausur, mündliche Prüfung, Hausarbeit, Projekt, Präsentation, Portfolio
- `semester` (String): Semester
- `datum` (Date): Prüfungsdatum
- `uhrzeit_start` (Time): Startzeit
- `uhrzeit_ende` (Time): Endzeit
- `dauer_minuten` (Integer): Dauer in Minuten
- `raum_id` (String): Referenz zum Prüfungsraum
- `modul_id` (String): Referenz zum Modul
- `lehrveranstaltung_id` (String): Referenz zur Lehrveranstaltung
- `pruefer_id` (String): Referenz zum Prüfer
- `zweiter_pruefer_id` (String): Referenz zum zweiten Prüfer (optional)
- `max_punkte` (Integer): Maximale Punktzahl
- `bestanden_punkte` (Integer): Mindestpunktzahl zum Bestehen
- `anmeldung_erforderlich` (Boolean): Anmeldung erforderlich
- `anmeldefrist` (Date): Anmeldefrist
- `nachschreibetermin` (Date): Nachschreibetermin (optional)

#### 1.4.2 Prüfungsleistung (Examination Result)
**Eigenschaften:**
- `leistung_id` (String, eindeutig): Identifikationsnummer
- `student_id` (String): Referenz zum Studierenden
- `pruefung_id` (String): Referenz zur Prüfung
- `punkte` (Integer): Erreichte Punktzahl
- `note` (Float): Note (1.0-5.0)
- `bestanden` (Boolean): Bestanden/Nicht bestanden
- `datum` (Date): Datum der Prüfung
- `bewertet_am` (Date): Datum der Bewertung
- `bewertet_von_id` (String): Referenz zum Prüfer
- `kommentar` (Text): Kommentar des Prüfers (optional)
- `wiederholung` (Boolean): Wiederholungsprüfung
- `versuch` (Integer): Versuch (1, 2, 3, etc.)

#### 1.4.3 Prüfungsordnung (Examination Regulation)
**Eigenschaften:**
- `pruefungsordnung_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name der Prüfungsordnung
- `version` (String): Version
- `gueltig_ab` (Date): Gültig ab
- `gueltig_bis` (Date): Gültig bis (optional)
- `studiengang_id` (String): Referenz zum Studiengang
- `pdf_dokument` (String): Pfad zum PDF-Dokument
- `beschreibung` (Text): Beschreibung

### 1.5 Räume und Gebäude (Rooms and Buildings)

#### 1.5.1 Gebäude (Building)
**Eigenschaften:**
- `gebaeude_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name des Gebäudes
- `nummer` (String): Gebäudenummer
- `adresse` (String): Adresse
- `postleitzahl` (String): PLZ
- `stadt` (String): Stadt
- `stockwerke` (Integer): Anzahl der Stockwerke
- `baujahr` (Integer): Baujahr
- `nutzflaeche` (Float): Nutzfläche in m²
- `hochschule_id` (String): Referenz zur Hochschule
- `campus_id` (String): Referenz zum Campus (optional)

#### 1.5.2 Raum (Room)
**Eigenschaften:**
- `raum_id` (String, eindeutig): Identifikationsnummer
- `nummer` (String): Raumnummer
- `name` (String): Raumname (optional)
- `typ` (String): Hörsaal, Seminarraum, Labor, Büro, Bibliothek, Mensa, Verwaltung
- `flaeche` (Float): Fläche in m²
- `kapazitaet` (Integer): Maximale Kapazität
- `stockwerk` (Integer): Stockwerk
- `gebaeude_id` (String): Referenz zum Gebäude
- `ausstattung` (Text): Ausstattung (Beamer, Whiteboard, etc.)
- `rollstuhlgerecht` (Boolean): Rollstuhlgerecht
- `verfuegbar` (Boolean): Verfügbar für Buchungen

#### 1.5.3 Labor (Laboratory)
**Eigenschaften:** (erbt von Raum)
- `labor_id` (String, eindeutig): Identifikationsnummer
- `spezialisierung` (String): Art des Labors (Chemie, Physik, Informatik, etc.)
- `geraete` (Text): Liste der Geräte
- `sicherheitsstufe` (String): Sicherheitsstufe
- `betreuer_id` (String): Referenz zum Laborbetreuer

#### 1.5.4 Campus (Campus)
**Eigenschaften:**
- `campus_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name des Campus
- `adresse` (String): Adresse
- `postleitzahl` (String): PLZ
- `stadt` (String): Stadt
- `flaeche` (Float): Gesamtfläche in m²
- `hochschule_id` (String): Referenz zur Hochschule

### 1.6 Dokumente (Documents)

#### 1.6.1 Publikation (Publication)
**Eigenschaften:**
- `publikation_id` (String, eindeutig): Identifikationsnummer
- `titel` (String): Titel der Publikation
- `typ` (String): Buch, Artikel, Konferenzbeitrag, Dissertation, Habilitation, Bericht
- `jahr` (Integer): Erscheinungsjahr
- `verlag` (String): Verlag
- `zeitschrift` (String): Zeitschrift (optional)
- `isbn` (String): ISBN (optional)
- `issn` (String): ISSN (optional)
- `doi` (String): DOI (optional)
- `abstract` (Text): Abstract
- `schluesselwoerter` (Text): Schlagwörter
- `sprache` (String): Sprache
- `pdf_dokument` (String): Pfad zum PDF
- `url` (String): URL (optional)

#### 1.6.2 Autor (Author)
**Eigenschaften:**
- `autor_id` (String, eindeutig): Identifikationsnummer
- `person_id` (String): Referenz zur Person
- `publikation_id` (String): Referenz zur Publikation
- `reihenfolge` (Integer): Reihenfolge der Autoren
- `hauptautor` (Boolean): Hauptautor/Korrespondenzautor

#### 1.6.3 Abschlussarbeit (Thesis)
**Eigenschaften:**
- `arbeit_id` (String, eindeutig): Identifikationsnummer
- `titel` (String): Titel der Arbeit
- `typ` (String): Bachelorarbeit, Masterarbeit, Diplomarbeit, Dissertation, Habilitation
- `student_id` (String): Referenz zum Studierenden
- `betreuer_id` (String): Referenz zum Betreuer
- `zweiter_betreuer_id` (String): Referenz zum zweiten Betreuer (optional)
- `abgabedatum` (Date): Abgabedatum
- `verteidigungsdatum` (Date): Verteidigungsdatum (optional)
- `note` (Float): Note
- `bestanden` (Boolean): Bestanden
- `pdf_dokument` (String): Pfad zum PDF
- `abstract` (Text): Abstract
- `schluesselwoerter` (Text): Schlagwörter

#### 1.6.4 Formular (Form)
**Eigenschaften:**
- `formular_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name des Formulars
- `typ` (String): Einschreibung, Exmatrikulation, Beurlaubung, etc.
- `version` (String): Version
- `pdf_dokument` (String): Pfad zum PDF
- `online_verfuegbar` (Boolean): Online verfügbar
- `url` (String): URL (optional)

#### 1.6.5 Satzung (Statute)
**Eigenschaften:**
- `satzung_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name der Satzung
- `typ` (String): Einschreibungsordnung, Prüfungsordnung, Gebührenordnung, etc.
- `version` (String): Version
- `gueltig_ab` (Date): Gültig ab
- `gueltig_bis` (Date): Gültig bis (optional)
- `pdf_dokument` (String): Pfad zum PDF
- `beschreibung` (Text): Beschreibung

#### 1.6.6 Modulhandbuch (Module Handbook)
**Eigenschaften:**
- `modulhandbuch_id` (String, eindeutig): Identifikationsnummer
- `studiengang_id` (String): Referenz zum Studiengang
- `version` (String): Version
- `semester` (String): Gültig für Semester
- `pdf_dokument` (String): Pfad zum PDF
- `gueltig_ab` (Date): Gültig ab

### 1.7 Veranstaltungen und Events (Events)

#### 1.7.1 Veranstaltung (Event)
**Eigenschaften:**
- `veranstaltung_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name der Veranstaltung
- `typ` (String): Konferenz, Workshop, Vortrag, Tagung, Messe, Feier
- `datum_start` (Date): Startdatum
- `datum_ende` (Date): Enddatum
- `uhrzeit_start` (Time): Startzeit
- `uhrzeit_ende` (Time): Endzeit
- `ort` (String): Ort
- `raum_id` (String): Referenz zum Raum (optional)
- `beschreibung` (Text): Beschreibung
- `oeffentlich` (Boolean): Öffentlich zugänglich
- `anmeldung_erforderlich` (Boolean): Anmeldung erforderlich
- `max_teilnehmer` (Integer): Maximale Teilnehmerzahl
- `organisator_id` (String): Referenz zum Organisator

#### 1.7.2 Vortrag (Lecture/Talk)
**Eigenschaften:** (erbt von Veranstaltung)
- `vortrag_id` (String, eindeutig): Identifikationsnummer
- `referent_id` (String): Referenz zum Referenten
- `thema` (String): Thema des Vortrags
- `dauer_minuten` (Integer): Dauer in Minuten

#### 1.7.3 Konferenz (Conference)
**Eigenschaften:** (erbt von Veranstaltung)
- `konferenz_id` (String, eindeutig): Identifikationsnummer
- `thema` (String): Hauptthema
- `sprache` (String): Konferenzsprache
- `teilnahmegebuehr` (Float): Teilnahmegebühr
- `website` (String): Konferenzwebsite

### 1.8 Forschungsprojekte (Research Projects)

#### 1.8.1 Forschungsprojekt (Research Project)
**Eigenschaften:**
- `projekt_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name des Projekts
- `beschreibung` (Text): Projektbeschreibung
- `startdatum` (Date): Startdatum
- `enddatum` (Date): Enddatum (optional)
- `status` (String): geplant, laufend, abgeschlossen, eingestellt
- `foerdergeber` (String): Fördergeber
- `foerderbetrag` (Float): Förderbetrag in Euro
- `projektleiter_id` (String): Referenz zum Projektleiter
- `fachbereich_id` (String): Referenz zum Fachbereich
- `schluesselwoerter` (Text): Schlagwörter

#### 1.8.2 Projektmitarbeiter (Project Member)
**Eigenschaften:**
- `mitarbeiter_id` (String): Referenz zur Person
- `projekt_id` (String): Referenz zum Projekt
- `rolle` (String): Projektleiter, Mitarbeiter, Doktorand, etc.
- `beteiligung_von` (Date): Beteiligung von
- `beteiligung_bis` (Date): Beteiligung bis (optional)
- `stunden_pro_woche` (Float): Stunden pro Woche

### 1.9 Semester und Zeiträume (Semesters and Time Periods)

#### 1.9.1 Semester (Semester)
**Eigenschaften:**
- `semester_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Wintersemester 2024/25, Sommersemester 2025, etc.
- `typ` (String): Wintersemester, Sommersemester
- `jahr` (Integer): Jahr
- `startdatum` (Date): Semesterstart
- `enddatum` (Date): Semesterende
- `vorlesungsbeginn` (Date): Vorlesungsbeginn
- `vorlesungsende` (Date): Vorlesungsende
- `rueckmeldefrist_start` (Date): Start der Rückmeldefrist
- `rueckmeldefrist_ende` (Date): Ende der Rückmeldefrist
- `pruefungszeitraum_start` (Date): Start des Prüfungszeitraums
- `pruefungszeitraum_ende` (Date): Ende des Prüfungszeitraums
- `semesterferien_start` (Date): Start der Semesterferien
- `semesterferien_ende` (Date): Ende der Semesterferien

### 1.10 Finanzen (Finance)

#### 1.10.1 Gebühr (Fee)
**Eigenschaften:**
- `gebuehr_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name der Gebühr
- `typ` (String): Semesterbeitrag, Studiengebühr, Prüfungsgebühr, Zweithörerbeitrag, etc.
- `betrag` (Float): Betrag in Euro
- `zahlungsfrist` (Date): Zahlungsfrist
- `wiederkehrend` (Boolean): Wiederkehrende Gebühr
- `semester_id` (String): Referenz zum Semester (optional)

#### 1.10.2 Zahlung (Payment)
**Eigenschaften:**
- `zahlung_id` (String, eindeutig): Identifikationsnummer
- `student_id` (String): Referenz zum Studierenden
- `gebuehr_id` (String): Referenz zur Gebühr
- `betrag` (Float): Gezahlter Betrag
- `zahlungsdatum` (Date): Zahlungsdatum
- `zahlungsart` (String): Überweisung, Lastschrift, Bar, etc.
- `status` (String): ausstehend, bezahlt, überfällig, storniert
- `referenznummer` (String): Referenznummer

#### 1.10.3 Stipendium (Scholarship)
**Eigenschaften:**
- `stipendium_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name des Stipendiums
- `geber` (String): Stipendiengeber
- `betrag_monatlich` (Float): Monatlicher Betrag
- `laufzeit_monate` (Integer): Laufzeit in Monaten
- `student_id` (String): Referenz zum Studierenden
- `startdatum` (Date): Startdatum
- `enddatum` (Date): Enddatum

### 1.11 IT und Systeme (IT and Systems)

#### 1.11.1 IT-System (IT System)
**Eigenschaften:**
- `system_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name des Systems
- `typ` (String): LMS, ERP, Bibliothekssystem, Prüfungssystem, etc.
- `beschreibung` (Text): Beschreibung
- `url` (String): URL
- `status` (String): aktiv, inaktiv, Wartung
- `verantwortlich_id` (String): Referenz zur verantwortlichen Person

#### 1.11.2 Benutzerkonto (User Account)
**Eigenschaften:**
- `konto_id` (String, eindeutig): Identifikationsnummer
- `benutzername` (String): Benutzername
- `person_id` (String): Referenz zur Person
- `email` (String): E-Mail-Adresse
- `aktiv` (Boolean): Konto aktiv
- `erstellt_am` (Date): Erstellungsdatum
- `letzter_login` (Date): Letzter Login
- `rolle` (String): Student, Professor, Mitarbeiter, Admin

### 1.12 Kooperationen (Cooperations)

#### 1.12.1 Partnerorganisation (Partner Organization)
**Eigenschaften:**
- `partner_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name der Organisation
- `typ` (String): Unternehmen, andere Hochschule, Forschungseinrichtung, etc.
- `adresse` (String): Adresse
- `telefon` (String): Telefonnummer
- `email` (String): E-Mail-Adresse
- `website` (String): Website
- `kooperationsart` (String): Forschung, Lehre, Praktikum, Duales Studium

#### 1.12.2 Kooperationsvereinbarung (Cooperation Agreement)
**Eigenschaften:**
- `vereinbarung_id` (String, eindeutig): Identifikationsnummer
- `partner_id` (String): Referenz zur Partnerorganisation
- `hochschule_id` (String): Referenz zur Hochschule
- `typ` (String): Forschungskooperation, Austauschprogramm, Praktikumsvereinbarung, etc.
- `startdatum` (Date): Startdatum
- `enddatum` (Date): Enddatum (optional)
- `beschreibung` (Text): Beschreibung
- `dokument` (String): Pfad zum Vertragsdokument

### 1.13 Praktika (Internships)

#### 1.13.1 Praktikum (Internship)
**Eigenschaften:**
- `praktikum_id` (String, eindeutig): Identifikationsnummer
- `student_id` (String): Referenz zum Studierenden
- `unternehmen_id` (String): Referenz zum Unternehmen
- `typ` (String): Pflichtpraktikum, freiwilliges Praktikum, Praxissemester, Auslandspraktikum
- `startdatum` (Date): Startdatum
- `enddatum` (Date): Enddatum
- `dauer_wochen` (Integer): Dauer in Wochen
- `stunden_pro_woche` (Integer): Stunden pro Woche
- `vergütet` (Boolean): Vergütet
- `vergütung` (Float): Vergütung in Euro (optional)
- `betreuer_unternehmen` (String): Betreuer im Unternehmen
- `betreuer_hochschule_id` (String): Betreuer an der Hochschule
- `status` (String): geplant, laufend, abgeschlossen, abgebrochen
- `bewertung` (Text): Bewertung (optional)
- `note` (Float): Note (optional)

### 1.14 Auslandsaufenthalte (Study Abroad)

#### 1.14.1 Auslandssemester (Study Abroad Semester)
**Eigenschaften:**
- `auslandssemester_id` (String, eindeutig): Identifikationsnummer
- `student_id` (String): Referenz zum Studierenden
- `partnerhochschule_id` (String): Referenz zur Partnerhochschule
- `land` (String): Land
- `stadt` (String): Stadt
- `semester` (String): Semester
- `startdatum` (Date): Startdatum
- `enddatum` (Date): Enddatum
- `stipendium_id` (String): Referenz zum Stipendium (optional)
- `status` (String): geplant, laufend, abgeschlossen
- `anerkannte_kurse` (Text): Liste der anerkannten Kurse

#### 1.14.2 Austauschprogramm (Exchange Program)
**Eigenschaften:**
- `programm_id` (String, eindeutig): Identifikationsnummer
- `name` (String): Name des Programms (z.B. Erasmus+, etc.)
- `typ` (String): Erasmus+, DAAD, etc.
- `partnerhochschule_id` (String): Referenz zur Partnerhochschule
- `max_teilnehmer` (Integer): Maximale Teilnehmerzahl
- `bewerbungsfrist` (Date): Bewerbungsfrist
- `beschreibung` (Text): Beschreibung

## 2. Beziehungen (Relationships)

### 2.1 Personenbeziehungen

- `IST_EINGESCHRIEBEN_IN` (Studierende → Studiengang)
  - Eigenschaften: `seit` (Date), `status` (String)
  
- `GEHOERT_ZU` (Person → Fachbereich)
  - Eigenschaften: `rolle` (String), `seit` (Date)
  
- `IST_DOZENT_VON` (Dozent → Lehrveranstaltung)
  - Eigenschaften: `rolle` (String) - Hauptdozent, Co-Dozent
  
- `BETREUT` (Professor → Abschlussarbeit)
  - Eigenschaften: `art` (String) - Erstbetreuer, Zweitbetreuer
  
- `PRUEFT` (Prüfer → Prüfung)
  - Eigenschaften: `rolle` (String) - Erstprüfer, Zweitprüfer
  
- `HAT_ABGELEGT` (Studierende → Prüfung)
  - Eigenschaften: `datum` (Date), `note` (Float), `bestanden` (Boolean)
  
- `NIMMT_TEIL_AN` (Person → Lehrveranstaltung)
  - Eigenschaften: `rolle` (String) - Teilnehmer, Tutor
  
- `ARBEITET_IN` (Person → Verwaltungsabteilung)
  - Eigenschaften: `position` (String), `seit` (Date)
  
- `LEITET` (Person → Organisation)
  - Eigenschaften: `funktion` (String), `seit` (Date), `bis` (Date)

### 2.2 Organisationsbeziehungen

- `GEHOERT_ZU` (Fachbereich → Hochschule)
  - Eigenschaften: `seit` (Date)
  
- `IST_TEIL_VON` (Institut → Fachbereich)
  - Eigenschaften: `seit` (Date)
  
- `BEFINDET_SICH_IN` (Raum → Gebäude)
  - Eigenschaften: `stockwerk` (Integer)
  
- `GEHOERT_ZU` (Gebäude → Campus)
  - Eigenschaften: `seit` (Date)
  
- `VERWALTET` (Verwaltungsabteilung → Ressource)
  - Eigenschaften: `verantwortlich_seit` (Date)

### 2.3 Studienbeziehungen

- `UMFASST` (Studiengang → Modul)
  - Eigenschaften: `pflichtmodul` (Boolean), `semester` (Integer)
  
- `ENTHAELT` (Modul → Lehrveranstaltung)
  - Eigenschaften: `typ` (String)
  
- `ERFORDERT` (Modul → Modul)
  - Eigenschaften: `art` (String) - Voraussetzung, Empfehlung
  
- `WIRD_ANGEBOTEN_IN` (Lehrveranstaltung → Semester)
  - Eigenschaften: `semester` (String)
  
- `FINDET_STATT_IN` (Lehrveranstaltung → Raum)
  - Eigenschaften: `wochentag` (String), `uhrzeit` (Time)
  
- `HAT_MATERIAL` (Lehrveranstaltung → Kursmaterial)
  - Eigenschaften: `typ` (String), `verfuegbar_ab` (Date)

### 2.4 Prüfungsbeziehungen

- `GEHOERT_ZU` (Prüfung → Modul)
  - Eigenschaften: `gewichtung` (Float)
  
- `WIRD_DURCHGEFUEHRT_IN` (Prüfung → Raum)
  - Eigenschaften: `datum` (Date), `uhrzeit` (Time)
  
- `REGELT` (Prüfungsordnung → Studiengang)
  - Eigenschaften: `version` (String), `gueltig_ab` (Date)
  
- `BEWERTET` (Prüfer → Prüfungsleistung)
  - Eigenschaften: `datum` (Date), `kommentar` (Text)

### 2.5 Forschungsbeziehungen

- `LEITET` (Person → Forschungsprojekt)
  - Eigenschaften: `seit` (Date)
  
- `ARBEITET_AN` (Person → Forschungsprojekt)
  - Eigenschaften: `rolle` (String), `stunden_pro_woche` (Float)
  
- `PUBLIZIERT_IN` (Person → Publikation)
  - Eigenschaften: `reihenfolge` (Integer), `hauptautor` (Boolean)
  
- `ENTSTANDEN_AUS` (Publikation → Forschungsprojekt)
  - Eigenschaften: `art` (String)

### 2.6 Dokumentenbeziehungen

- `GEHOERT_ZU` (Abschlussarbeit → Studiengang)
  - Eigenschaften: `typ` (String)
  
- `WURDE_ERSTELLT_VON` (Dokument → Person)
  - Eigenschaften: `datum` (Date), `rolle` (String)
  
- `REGELT` (Satzung → Prozess)
  - Eigenschaften: `version` (String), `gueltig_ab` (Date)

### 2.7 Veranstaltungsbeziehungen

- `ORGANISIERT` (Person → Veranstaltung)
  - Eigenschaften: `rolle` (String)
  
- `NIMMT_TEIL_AN` (Person → Veranstaltung)
  - Eigenschaften: `rolle` (String) - Teilnehmer, Referent
  
- `FINDET_STATT_IN` (Veranstaltung → Raum)
  - Eigenschaften: `datum` (Date), `uhrzeit` (Time)

### 2.8 Kooperationsbeziehungen

- `KOOPERIERT_MIT` (Hochschule → Partnerorganisation)
  - Eigenschaften: `art` (String), `seit` (Date), `vertrag_id` (String)
  
- `PRAKTIKUM_BEI` (Studierende → Unternehmen)
  - Eigenschaften: `startdatum` (Date), `enddatum` (Date), `status` (String)

### 2.9 Finanzbeziehungen

- `SCHULDET` (Studierende → Gebühr)
  - Eigenschaften: `betrag` (Float), `faellig_am` (Date), `status` (String)
  
- `ZAHLT` (Studierende → Zahlung)
  - Eigenschaften: `datum` (Date), `betrag` (Float), `referenznummer` (String)
  
- `ERHAELT` (Studierende → Stipendium)
  - Eigenschaften: `startdatum` (Date), `enddatum` (Date), `betrag` (Float)

### 2.10 IT-Beziehungen

- `HAT_KONTO` (Person → Benutzerkonto)
  - Eigenschaften: `erstellt_am` (Date), `aktiv` (Boolean)
  
- `NUTZT` (Person → IT-System)
  - Eigenschaften: `rolle` (String), `seit` (Date)

### 2.11 Zeitbeziehungen

- `LAEUFT_IN` (Lehrveranstaltung → Semester)
  - Eigenschaften: `semester` (String)
  
- `IST_FAELLIG_IN` (Gebühr → Semester)
  - Eigenschaften: `semester` (String)
  
- `STARTET_IN` (Forschungsprojekt → Semester)
  - Eigenschaften: `semester` (String)

## 3. Indizes und Constraints

### 3.1 Eindeutige Constraints
- `student_id` muss eindeutig sein
- `professor_id` muss eindeutig sein
- `studiengang_id` muss eindeutig sein
- `modul_id` muss eindeutig sein
- `pruefung_id` muss eindeutig sein
- `raum_id` muss eindeutig sein
- `publikation_id` muss eindeutig sein

### 3.2 Indizes für Performance
- Index auf `student_id` in Studierende
- Index auf `email` in allen Personentypen
- Index auf `studiengang_id` in Studierende
- Index auf `fachbereich_id` in allen relevanten Knoten
- Index auf `semester` in Semester-bezogenen Knoten
- Index auf `datum` in zeitbezogenen Knoten
- Volltextindex auf `name`, `beschreibung` in relevanten Knoten

## 4. Metadaten und Verwaltung

### 4.1 Audit-Felder (für alle Knoten)
- `erstellt_am` (Date): Erstellungsdatum
- `erstellt_von` (String): Erstellt von (User ID)
- `geaendert_am` (Date): Letztes Änderungsdatum
- `geaendert_von` (String): Geändert von (User ID)
- `version` (Integer): Versionsnummer
- `geloescht` (Boolean): Soft Delete Flag
- `geloescht_am` (Date): Löschdatum (optional)

### 4.2 Validierungsregeln
- E-Mail-Adressen müssen valide sein
- Datumsfelder müssen gültige Daten sein
- Noten müssen im Bereich 1.0-5.0 liegen
- ECTS-Punkte müssen positiv sein
- Beträge müssen nicht-negativ sein
- Telefonnummern müssen valide formatiert sein

## 5. Erweiterte Konzepte

### 5.1 Hierarchien
- Hochschule → Campus → Gebäude → Raum
- Hochschule → Fachbereich → Institut → Lehrstuhl
- Studiengang → Modul → Lehrveranstaltung
- Prüfungsordnung → Prüfung → Prüfungsleistung

### 5.2 Zeitliche Aspekte
- Alle zeitbezogenen Beziehungen haben `von` und `bis` Datumsfelder
- Historische Daten werden durch Versionierung erhalten
- Soft Deletes für Audit-Zwecke

### 5.3 Mehrsprachigkeit
- Unterstützung für deutsche und englische Begriffe
- `name_de`, `name_en` Felder wo relevant
- `beschreibung_de`, `beschreibung_en` Felder

Diese Ontologie bildet die Grundlage für einen umfassenden Wissensgraph einer Universität und kann je nach spezifischen Anforderungen erweitert werden.

