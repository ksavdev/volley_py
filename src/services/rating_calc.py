from decimal import Decimal, ROUND_HALF_UP

def new_average(old_avg: float, count: int, new_score: int) -> float:
    """Простейший пересчёт среднего рейтинга."""
    total = Decimal(old_avg) * count + Decimal(new_score)
    return float((total / (count + 1)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
