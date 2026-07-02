"""Tests für die Preisberechnung."""

from app import PriceTable, ServiceSelection


class TestPriceCalculation:
    """Tests für Pauschalpreis und Stundenabrechnung."""

    def test_fixed_price_uses_square_metre_prices(self) -> None:
        """Pauschalpreis wird aus Quadratmetern und Einheitspreis berechnet."""
        table = PriceTable()
        selections = [ServiceSelection("Trockenbau", "Trennwände", 10.0)]

        assert table.estimate_fixed(selections) == 550.0

    def test_hourly_price_can_be_cheaper_for_small_work(self) -> None:
        """Bei kleinen Arbeiten kann Stundenabrechnung günstiger sein."""
        table = PriceTable()
        selections = [ServiceSelection("Malerarbeiten", "Innenanstriche", 10.0)]

        fixed = table.estimate_fixed(selections)
        hourly, hours, rate = table.estimate_hourly(selections)

        assert fixed == 180.0
        assert hourly <= fixed
        assert hours >= 1
        assert rate == 65

    def test_hourly_price_gets_expensive_for_large_work(self) -> None:
        """Bei großen Arbeiten wird die Stundenabrechnung teurer."""
        table = PriceTable()
        selections = [ServiceSelection("Dämmung", "Energetische Sanierung", 100.0)]

        fixed = table.estimate_fixed(selections)
        hourly, _, _ = table.estimate_hourly(selections)

        assert fixed == 11000.0
        assert hourly > fixed