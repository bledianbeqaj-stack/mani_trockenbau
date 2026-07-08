"""Tests für Eingabevalidierung und Zeitlogik."""

from datetime import date

from app import InputValidator


class TestValidation:
    """Tests für Benutzereingaben und buchbare Terminzeiten."""

    def test_name_must_not_contain_numbers(self) -> None:
        """Namen mit Zahlen werden abgelehnt."""
        assert InputValidator.validate_name("Max123") is not None
        assert InputValidator.validate_name("Max Mustermann") is None

    def test_email_must_be_lowercase_and_valid(self) -> None:
        """E-Mail muss klein geschrieben und formal gültig sein."""
        assert InputValidator.validate_email("MAX@example.de") is not None
        assert InputValidator.validate_email("max@example.de") is None

    def test_phone_is_optional_but_must_match_german_format(self) -> None:
        """Telefon ist freiwillig; leere Eingabe und bloßes +49 sind erlaubt."""
        assert InputValidator.validate_phone("") is None
        assert InputValidator.validate_phone("+49") is None
        assert InputValidator.validate_phone("+49123456789") is None
        assert InputValidator.validate_phone("+491234567890") is None
        assert InputValidator.validate_phone("+4912345678901") is None
        assert InputValidator.validate_phone("+49123456789012") is not None
        assert InputValidator.validate_phone("017612345678") is not None

    def test_time_slots_respect_opening_hours(self) -> None:
        """Mittagspause und Sonntag werden nicht als buchbare Zeiten geliefert."""
        monday = date(2026, 6, 22)
        sunday = date(2026, 6, 21)

        assert "07:00" in InputValidator.time_slots(monday)
        assert "12:00" not in InputValidator.time_slots(monday)
        assert InputValidator.time_slots(sunday) == []