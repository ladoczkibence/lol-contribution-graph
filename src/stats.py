import datetime


def compute(counts, start, today):
    window = {}
    for iso, n in counts.items():
        d = datetime.date.fromisoformat(iso)
        if start <= d <= today:
            window[d] = n

    longest = run = 0
    day = start
    while day <= today:
        run = run + 1 if window.get(day) else 0
        longest = max(longest, run)
        day += datetime.timedelta(days=1)

    current = 0
    day = today if window.get(today) else today - datetime.timedelta(days=1)
    while day >= start and window.get(day):
        current += 1
        day -= datetime.timedelta(days=1)

    peak_day, peak = None, 0
    for day, n in sorted(window.items()):
        if n > peak:
            peak_day, peak = day, n

    return {
        "total": sum(window.values()),
        "active_days": len(window),
        "current_streak": current,
        "longest_streak": longest,
        "peak": peak,
        "peak_day": peak_day,
    }
