"""Tests für Terminbuchung und Doppelbuchungsschutz."""

from datetime import date
from pathlib import Path
import sqlite3

import pytest

from app import Appointment, BookingManager, Customer


class TestBooking:
    """Tests für das Speichern und Blockieren von Terminbuchungen."""

    def make_appointment(self, day: date, start_time: str = "09:00") -> Appointment:
        """Erstellt eine gültige Terminanfrage für Tests."""
        customer = Customer("Max Mustermann", "+491234567890", "max@example.de")

        return Appointment(
            customer=customer,
            day=day,
            start_time=start_time,
            sqm=20.0,
            services=["Trockenbau"],
            description="Testprojekt mit Trockenbauarbeiten",
        )

    def test_booking_is_saved_and_time_is_booked(self, tmp_path: Path) -> None:
        """Nach dem Speichern wird die Uhrzeit als belegt erkannt."""
        manager = BookingManager(tmp_path / "appointments.db")
        selected_day = date(2026, 6, 22)

        manager.save(self.make_appointment(selected_day))

        assert "09:00" in manager.booked_times(selected_day)

    def test_same_time_cannot_be_booked_twice(self, tmp_path: Path) -> None:
        """SQLite verhindert eine doppelte Buchung derselben Uhrzeit."""
        manager = BookingManager(tmp_path / "appointments.db")
        selected_day = date(2026, 6, 22)

        manager.save(self.make_appointment(selected_day))

        with pytest.raises(sqlite3.IntegrityError):
            manager.save(self.make_appointment(selected_day))