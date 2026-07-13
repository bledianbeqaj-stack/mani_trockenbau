"""Streamlit-App für Mani Trockenbau."""

import math
import re
import sqlite3
import subprocess
import sys
import streamlit.components.v1 as components
from dataclasses import dataclass
from datetime import date, time 
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "data" / "appointments.db"
WEBSITE_ASSETS = BASE_DIR / "assets" / "website"
COMPANY = {
    "name": "Mani Trockenbau",
    "address": "Bahnhofstr. 4, 74523 Schwäbisch Hall",
    "phone": "017632943726",
    "email": "manitrockenbau@gmail.com",
}

# Zentrale Preistabelle: alle Berechnungen nutzen dieselbe Datenbasis.
PRICES = {
    "Trockenbau": {
        "Trennwände": 55,
        "Abgehängte Decken": 62,
        "Dachausbau": 78,
        "Schallschutz": 72,
        "Brandschutz": 85,
        "Gipskartonarbeiten": 48,
    },
    "Malerarbeiten": {
        "Innenanstriche": 18,
        "Fassadenanstriche": 28,
        "Tapezierarbeiten": 24,
        "Spachtelarbeiten": 32,
        "Lackierarbeiten": 38,
    },
    "Fliesenarbeiten": {
        "Badezimmer": 68,
        "Küchen": 58,
        "Terrassen": 72,
        "Bodenfliesen": 54,
        "Wandfliesen": 59,
        "Reparaturen": 75,
    },
    "Dämmung": {
        "Innendämmung": 64,
        "Fassadendämmung": 96,
        "Dachbodendämmung": 42,
        "Kellerdeckendämmung": 46,
        "Energetische Sanierung": 110,
    },
}
SERVICE_TEXTS = {
    "Trockenbau": (
        "Flexible Lösungen für Innenausbau und Raumaufteilung. Dazu gehören saubere Wand- und Deckenkonstruktionen, "
        "Dachausbau sowie Lösungen für Schall- und Brandschutz. Der Fokus liegt auf stabiler Ausführung, klaren Kanten "
        "und einem Ergebnis, das später sauber weiterbearbeitet werden kann.",
        "trockenbau.jpeg",
    ),
    "Malerarbeiten": (
        "Malerarbeiten sorgen für moderne, saubere und langlebige Oberflächen. Innen- und Außenbereiche werden passend "
        "zum Projekt vorbereitet, gespachtelt und gestrichen. So entsteht ein stimmiges Gesamtbild, das optisch sauber "
        "wirkt und zum Gebäude passt.",
        "malerarbeit.jpg",
    ),
    "Fliesenarbeiten": (
        "Fliesenarbeiten verbinden robuste Materialien mit sauberer Optik. Besonders Bad, Küche, Boden und Wand profitieren "
        "von exakter Vorbereitung und geraden Fugen. Ziel ist eine pflegeleichte und hochwertige Oberfläche, die lange hält.",
        "fliesenarbeit.jpg",
    ),
    "Dämmung": (
        "Dämmarbeiten verbessern Energieeffizienz, Wohnkomfort und Gebäudeschutz. Innen, außen, Dachboden und Kellerdecke "
        "können je nach Projekt berücksichtigt werden. Dadurch lassen sich Wärmeverluste reduzieren und Räume angenehmer nutzen.",
        "daemmungarbeit.jpg",
    ),
}
OPEN_HOURS = {
    0: ((time(7), time(12)), (time(13), time(17))),
    1: ((time(7), time(12)), (time(13), time(17))),
    2: ((time(7), time(12)), (time(13), time(17))),
    3: ((time(7), time(12)), (time(13), time(17))),
    4: ((time(7), time(12)), (time(13), time(17))),
    5: ((time(7), time(15)),),
}


@dataclass
class Customer:
    """Speichert die Kontaktdaten eines Kunden."""

    name: str
    phone: str
    email: str


@dataclass
class ServiceSelection:
    """Speichert eine ausgewählte Leistung mit Unterkategorie und Fläche."""

    service: str
    sub_service: str
    sqm: float

@dataclass
class Appointment:
    """Speichert eine Terminanfrage."""

    customer: Customer
    day: date
    start_time: str
    sqm: float
    services: list[str]
    description: str


class PriceTable:
    """Berechnet unverbindliche Preisorientierungen."""

    def estimate_fixed(self, selections: list[ServiceSelection]) -> float:
        """Berechnet den Pauschalpreis über alle gewählten Unterkategorien."""
        return sum(
            PRICES[item.service][item.sub_service] * item.sqm
            for item in selections
        )

    def estimate_hourly(self, selections: list[ServiceSelection]) -> tuple[float, int, int]:
        """Schätzt Stunden so, dass kleine Arbeiten günstiger und große teurer werden."""
        fixed = self.estimate_fixed(selections)
        rate = 65

        # Kleine Arbeiten profitieren von Stundenabrechnung; große Projekte werden aufwendiger.
        if fixed <= 400:
            factor = 0.55
        elif fixed <= 1200:
            factor = 0.85
        else:
            factor = 1.20
        hours = max(1, math.ceil(fixed / rate * factor))
        return hours * rate, hours, rate


class BookingManager:
    """Prüft und speichert Termine mit SQLite."""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(exist_ok=True)
        self._create_table()

# SQL-Befehl: Erstellt die Tabelle für Terminbuchungen in der SQLite-Datenbank.
    def _create_table(self) -> None:
        """Erstellt die Termin-Tabelle, falls sie noch nicht existiert."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    day TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    name TEXT NOT NULL,
                    phone TEXT,
                    email TEXT NOT NULL,
                    sqm REAL NOT NULL,
                    services TEXT NOT NULL,
                    description TEXT NOT NULL,
                    UNIQUE(day, start_time)
                )
                """
            )

    def booked_times(self, selected_day: date) -> set[str]:
        """Liest alle bereits belegten Uhrzeiten für einen Tag aus."""
        with sqlite3.connect(self.db_path) as conn:
            # SQL-Abfrage: Holt alle bereits belegten Uhrzeiten für den gewählten Tag.
            rows = conn.execute(
                "SELECT start_time FROM appointments WHERE day = ?",
                (selected_day.isoformat(),),
            ).fetchall()
        return {row[0] for row in rows}

    def save(self, appointment: Appointment) -> None:
        """Speichert eine Terminanfrage und nutzt SQLite für Doppelbuchungsschutz."""
        with sqlite3.connect(self.db_path) as conn:
            # SQL-Befehl: Speichert eine neue Terminanfrage in der Datenbank.
            conn.execute(
                """
                INSERT INTO appointments (day, start_time, name, phone, email, sqm, services, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    appointment.day.isoformat(),
                    appointment.start_time,
                    appointment.customer.name,
                    appointment.customer.phone,
                    appointment.customer.email,
                    appointment.sqm,
                    ", ".join(appointment.services),
                    appointment.description,
                ),
            )


class InputValidator:
    """Prüft Benutzereingaben und erzeugt gültige Terminzeiten."""

    @staticmethod
    def validate_name(name: str) -> str | None:
        """Prüft, ob der Name vorhanden ist und keine Zahlen enthält."""
        if not name.strip():
            return "Name ist ein Pflichtfeld."
        if any(char.isdigit() for char in name):
            return "Der Name darf keine Zahlen enthalten."
        return None

    @staticmethod
    def validate_phone(phone: str) -> str | None:
        """Prüft die freiwillige deutsche Telefonnummer."""
        phone = phone.strip()
        if phone in ("", "+49"):
            return None
        if not re.fullmatch(r"\+49\d{9,11}", phone):
            return "Telefonnummer muss mit +49 beginnen und danach 9 bis 11 Zahlen haben."
        return None

    @staticmethod
    def validate_email(email: str) -> str | None:
        """Prüft, ob eine gültige kleingeschriebene E-Mail-Adresse eingegeben wurde."""
        if not email.strip():
            return "E-Mail ist ein Pflichtfeld."
        if email != email.lower():
            return "Die E-Mail-Adresse muss klein geschrieben sein."
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            return "Bitte eine gültige E-Mail-Adresse eingeben."
        return None

    @staticmethod
    def time_slots(selected_day: date) -> list[str]:
        """Erzeugt buchbare Stunden abhängig vom Wochentag und der Mittagspause."""
        slots = []
        for start, end in OPEN_HOURS.get(selected_day.weekday(), ()):
            slots.extend(f"{hour:02d}:00" for hour in range(start.hour, end.hour))
        return slots


class PageRenderer:
    """Baut die Streamlit-Oberfläche der Anwendung auf."""

    def __init__(self, manager: BookingManager) -> None:
        self.manager = manager
        self.validator = InputValidator()
 
    def apply_styles(self) -> None:
        """Fügt eigenes CSS für Layout, Terminslots und Spieltext ein."""
        # CSS: Gestaltet Layout, Termin-Slots und Spieltext.
        st.markdown(
            """  
            <style>
            .block-container{max-width:1150px;padding-top:2rem;} h1{font-size:3.2rem!important;}
            .slot-row{margin:12px 0 20px 0}
            .slot-free,.slot-booked{display:inline-block;padding:7px 12px;margin:4px;border-radius:9px;font-weight:600}
            .slot-free{background:#dff6e4;border:1px solid #1b7f32;color:#135c25}
            .slot-booked{background:#ffe0e0;border:1px solid #b71c1c;color:#8a1111}
            .game-text{font-size:1.35rem;font-weight:600;line-height:1.55;margin:1rem 0 1.3rem 0;}
            </style>
            """,
            unsafe_allow_html=True,
        )

    def slot_calendar(self, selected_day: date) -> None:
        """Zeigt verfügbare und belegte Uhrzeiten farblich an."""
        booked = self.manager.booked_times(selected_day)
        chips = []

        for slot in self.validator.time_slots(selected_day):
            css = "slot-booked" if slot in booked else "slot-free"
            # HTML: Erzeugt farbige Zeit-Chips für freie und belegte Termine.
            chips.append(f"<span class='{css}'>{slot}</span>") #HTML

        st.markdown(
            "<div class='slot-row'>" + "".join(chips) + "</div>", #HTML
            unsafe_allow_html=True,
        )

    def show_header(self) -> None:
        """Zeigt Logo, Überschrift und Einstiegssatz."""
        left, right = st.columns([3, 1])

        with left:
            st.title(COMPANY["name"])
            st.subheader("„Alles was Ihr Zuhause braucht – aus einer Hand.\"")
            st.write(
                "Digitale Angebotsorientierung, Terminanfrage und "
                "Bauarbeiter-Runner als Python-Projekt."
            )

        with right:
            logo = WEBSITE_ASSETS / "logo.jpg"
            if logo.exists():
                st.image(str(logo), use_container_width=True)

    def show_price_calculator(self) -> None:
        """Zeigt den Angebotsrechner mit Pauschal- und Stundenberechnung."""
        st.header("Unverbindliche Preisabschätzung")

        services = st.multiselect("Leistung(en)*", list(PRICES), default=["Trockenbau"])
        price_type = st.radio(
            "Preisart*",
            ["Pauschalpreis", "Stundenabrechnung"],
            horizontal=True,
        )
        selections: list[ServiceSelection] = []

        for service in services:
            subs = st.multiselect(
                f"Unterkategorie(n) für {service}*",
                list(PRICES[service]),
                key=f"subs_{service}",
            )

            for sub in subs:
                sqm = st.number_input(
                    f"m² für {service} – {sub}",
                    min_value=1.0,
                    value=20.0,
                    key=f"sqm_{service}_{sub}",
                )
                selections.append(ServiceSelection(service, sub, sqm))

        if st.button("Preis berechnen", type="primary"):
            if not selections:
                st.error("Bitte mindestens eine Unterkategorie auswählen.")
                return

            table = PriceTable()

            if price_type == "Pauschalpreis":
                total = table.estimate_fixed(selections)
                st.success(f"Unverbindliche Orientierung: ca. {total:,.2f} €")
            else:
                total, hours, rate = table.estimate_hourly(selections)
                st.success(
                    f"Unverbindliche Orientierung: ca. {total:,.2f} € "
                    f"bei ungefähr {hours} Stunden à {rate} €."
                )
                st.caption(
                    "Bei kleinen Arbeiten kann Stundenabrechnung günstiger sein; "
                    "bei größeren Projekten wird sie durch mehr Arbeitszeit meistens teurer."
                )

            st.info(
                "Ein genaueres Angebot erhalten Sie erst nach persönlicher Absprache "
                "oder Besichtigung. Diese Berechnung dient nur zur Orientierung."
            )

    def show_booking(self) -> None:
        """Zeigt Terminformular, Eingabeprüfung und Speicherung."""
        st.header("Termin anfragen")

        today = date.today()
        selected_day = st.date_input("Wunschdatum*", value=today, min_value=today, format="DD.MM.YYYY")

        if selected_day.weekday() == 6:
            st.error("Sonntags sind keine Termine möglich. Bitte einen anderen Tag wählen.")
            return

        self.slot_calendar(selected_day)

        booked = self.manager.booked_times(selected_day)
        free_slots = [
            slot for slot in self.validator.time_slots(selected_day)
            if slot not in booked
        ]

        if not free_slots:
            st.warning("Für diesen Tag sind keine Termine mehr frei.")
            return

        with st.form("booking_form"):
            start_time = st.selectbox("Freie Uhrzeit*", free_slots)
            name = st.text_input("Name*")
            phone = st.text_input("Telefonnummer", value="+49")
            email = st.text_input("E-Mail*")
            sqm = st.number_input("Qm*", min_value=1.0, value=20.0)
            services = st.multiselect("Leistung*", list(PRICES))
            description = st.text_area("Projektbeschreibung*")
            submitted = st.form_submit_button("Termin buchen")

        if submitted:
            errors = [
                self.validator.validate_name(name),
                self.validator.validate_phone(phone),
                self.validator.validate_email(email),
            ]

            if not services:
                errors.append("Bitte mindestens eine Leistung auswählen.")

            if not description.strip():
                errors.append("Projektbeschreibung ist ein Pflichtfeld.")

            real_errors = [error for error in errors if error]

            if real_errors:
                for error in real_errors:
                    st.error(error)
                return

            phone_clean = "" if phone.strip() == "+49" else phone.strip()

            appointment = Appointment(
                customer=Customer(name.strip(), phone_clean, email.strip()),
                day=selected_day,
                start_time=start_time,
                sqm=sqm,
                services=services,
                description=description.strip(),
            )

            try:
                self.manager.save(appointment)
                st.session_state["appointment_booked"] = True
                st.success(
                    "Termin wurde erfolgreich gebucht. Bitte ein paar Sekunden warten – "
                    "du wirst zum Spielbereich geführt."
                ) 
                # JavaScript: Scrollt nach erfolgreicher Terminbuchung automatisch zum Spielbereich.
                components.html(
                    """
                    <script>
                    setTimeout(function(){
                        const el = window.parent.document.getElementById('game-anchor');
                        if (el) { el.scrollIntoView({behavior: 'smooth', block: 'start'}); }
                    }, 900);
                    </script>
                    """,
                    height=0,
                )
            except sqlite3.IntegrityError:
                st.error("Dieser Termin wurde gerade gebucht. Bitte andere Uhrzeit wählen.")

    def show_services(self) -> None:
        """Zeigt die vier Leistungsbereiche mit Bild und Kurztext."""
        st.header("Unsere Leistungen")

        for index, (name, (text, image_name)) in enumerate(SERVICE_TEXTS.items()):
            col_a, col_b = st.columns([1, 1])
            text_col, image_col = (col_a, col_b) if index % 2 == 0 else (col_b, col_a)

            with text_col:
                st.subheader(name)
                st.write(text)

            with image_col:
                image = WEBSITE_ASSETS / image_name
                if image.exists():
                    st.image(str(image), use_container_width=True)

            st.divider()

    def show_game_section(self) -> None:
        """Zeigt den Spielbereich erst nach erfolgreicher Terminbuchung."""
        st.markdown("<div id='game-anchor'></div>", unsafe_allow_html=True)
        st.header("Bauarbeiter Runner")

        if not st.session_state.get("appointment_booked", False):
            st.write("Bitte zuerst ein Termin buchen.")
            return

        st.markdown(
            "<div class='game-text'>„Termin gebucht – Stress abgegeben! 🎉 "
            "Während wir die schwere Arbeit übernehmen, lehn dich einfach zurück "
            "und lass unseren Bauarbeiter für dich rennen! 👷‍♂🏃\"</div>",
            unsafe_allow_html=True,
        )

        if st.button("Mini-Game starten"):
            subprocess.Popen([sys.executable, str(BASE_DIR / "game.py")], cwd=str(BASE_DIR))
            st.success("Mini-Game wird gestartet. Bitte ein paar Sekunden warten.")

    def show_contact(self) -> None:
        """Zeigt Kontaktdaten und Öffnungszeiten."""
        st.header("Kontakt und Öffnungszeiten")
        st.write(f"🏠 **Adresse:** {COMPANY['address']}")
        st.write(f"📞 **Telefon:** {COMPANY['phone']}")
        st.write(f"✉️ **E-Mail:** {COMPANY['email']}")
        st.write("📅 **Öffnungszeiten:**")
        st.write("Montag bis Freitag: 07:00 - 12:00 und 13:00 - 17:00")
        st.write("Samstag: 07:00 - 15:00")
        st.write("Sonntag: geschlossen")

    def render(self) -> None:
        """Rendert alle Bereiche der einseitigen Streamlit-Anwendung."""
        self.apply_styles()
        self.show_header()
        st.divider()
        self.show_price_calculator()
        st.divider()
        self.show_booking()
        st.divider()
        self.show_services()
        self.show_game_section()
        st.divider()
        self.show_contact()


def main() -> None:
    """Startet die Streamlit-Anwendung."""
    st.set_page_config(
        page_title="Mani Trockenbau",
        page_icon="🏗️",
        layout="wide",
    )

    manager = BookingManager()
    renderer = PageRenderer(manager)
    renderer.render()


if __name__ == "__main__":
    main()