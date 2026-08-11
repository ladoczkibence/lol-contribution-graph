import datetime
import math
from xml.sax.saxutils import escape

import assets
import stats

CELL = 10
GAP = 3
STEP = CELL + GAP

PANEL_W = 204
GX0 = 240
GY0 = 72
DAY_LABEL_X = 232
MONTH_Y = 64
FOOT_Y = 192
H = 235
RX = 8

THEMES = {
    "light": {
        "bg": "#ffffff",
        "panel": "#f6f8fa",
        "text": "#1f2328",
        "muted": "#59636e",
        "border": "#d1d9e0",
        "empty": "#ebedf0",
        "levels": ("#9be9a8", "#40c463", "#30a14e", "#216e39"),
        "flame": "#bf8700",
        "flame_inner": "#f2cc60",
        "glow_op": "0.06",
    },
    "dark": {
        "bg": "#0d1117",
        "panel": "#151b23",
        "text": "#e6edf3",
        "muted": "#9198a1",
        "border": "#3d444d",
        "empty": "#161b22",
        "levels": ("#0e4429", "#006d32", "#26a641", "#39d353"),
        "flame": "#d29922",
        "flame_inner": "#f0b72f",
        "glow_op": "0.13",
    },
}

TIER_COLORS = {
    "IRON": ("#6e5849", "#a89484"),
    "BRONZE": ("#8c5a2b", "#c98a4b"),
    "SILVER": ("#5c6b73", "#9fb0ba"),
    "GOLD": ("#9a6700", "#e3b341"),
    "PLATINUM": ("#0b7285", "#3dd6c5"),
    "EMERALD": ("#116d3c", "#34d07e"),
    "DIAMOND": ("#1f6feb", "#79c0ff"),
    "MASTER": ("#8250df", "#b794f6"),
    "GRANDMASTER": ("#cf222e", "#f85149"),
    "CHALLENGER": ("#bf8700", "#f2cc60"),
}
TIER_FALLBACK = ("#59636e", "#9198a1")

QUEUE_NAMES = {"solo": "Solo Queue", "flex": "Flex Queue"}
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

ROLE_ICONS = {
    "TOP": (
        ("path", "M21,14H14v7h7V14Zm5-3V26L11.014,26l-4,4H30V7.016Z", 0.45),
        ("polygon", "4 4 4.003 28.045 9 23 9 9 23 9 28.045 4.003 4 4", None),
    ),
    "JUNGLE": (
        ("path", "M25,3c-2.128,3.3-5.147,6.851-6.966,11.469A42.373,42.373,0,0,1,20,20"
                 "a27.7,27.7,0,0,1,1-3C21,12.023,22.856,8.277,25,3ZM13,20"
                 "c-1.488-4.487-4.76-6.966-9-9,3.868,3.136,4.422,7.52,5,12l3.743,3.312"
                 "C14.215,27.917,16.527,30.451,17,31c4.555-9.445-3.366-20.8-8-28"
                 "C11.67,9.573,13.717,13.342,13,20Zm8,5a15.271,15.271,0,0,1,0,2l4-4"
                 "c0.578-4.48,1.132-8.864,5-12C24.712,13.537,22.134,18.854,21,25Z", None),
    ),
    "MIDDLE": (
        ("path", "M30,12.968l-4.008,4L26,26H17l-4,4H30ZM16.979,8L21,4H4V20.977"
                 "L8,17,8,8h8.981Z", 0.45),
        ("polygon", "25 4 4 25 4 30 9 30 30 9 30 4 25 4", None),
    ),
    "BOTTOM": (
        ("path", "M13,20h7V13H13v7ZM4,4V26.984l3.955-4L8,8,22.986,8l4-4H4Z", 0.45),
        ("polygon", "29.997 5.955 25 11 25 25 11 25 5.955 29.997 30 30 29.997 5.955", None),
    ),
    "UTILITY": (
        ("path", "M26,13c3.535,0,8-4,8-4H23l-3,3,2,7,5-2-3-4h2ZM22,5L20.827,3H13.062"
                 "L12,5l5,6Zm-5,9-1-1L13,28l4,3,4-3L18,13ZM11,9H0s4.465,4,8,4h2"
                 "L7,17l5,2,2-7Z", None),
    ),
}
ROLE_NAMES = {"TOP": "Top", "JUNGLE": "Jungle", "MIDDLE": "Mid",
              "BOTTOM": "ADC", "UTILITY": "Support"}

FLAME_PATH = ("M5 0C5.4 2.1 7.3 3.4 8.4 5.2C9.1 6.3 9.5 7.4 9.5 8.6"
              "A4.5 4.5 0 0 1 0.5 8.6C0.5 6.9 1.4 5.5 2.4 4.3"
              "C2.6 5.3 3.1 6 3.9 6.4C3.6 4.2 4.1 1.9 5 0Z")
FLAME_INNER = ("M5 6.8C6.2 7.9 6.9 8.7 6.9 9.8A1.9 1.9 0 0 1 3.1 9.8"
               "C3.1 8.7 3.9 7.9 5 6.8Z")


def _fmt_day(d):
    return f"{MONTHS[d.month - 1]} {d.day}, {d.year}"


def _plural(n, word):
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def _role_icon(role, pal):
    shapes = []
    for kind, data, opacity in ROLE_ICONS[role]:
        op = f" opacity='{opacity}'" if opacity else ""
        if kind == "path":
            shapes.append(f"<path d='{data}' fill='{pal['muted']}' fill-rule='evenodd'{op}/>")
        else:
            shapes.append(f"<polygon points='{data}' fill='{pal['muted']}'{op}/>")
    name = ROLE_NAMES.get(role, role.title())
    return (
        f"<g transform='translate({PANEL_W - 31},19) scale(0.5)'>"
        f"<title>Most played role: {name}</title>{''.join(shapes)}</g>"
    )


def _panel(label, s, rank, profile, role, days, pal, tier):
    px = 18
    out = []

    icon_path = assets.profile_icon(profile["iconId"]) if profile else None
    if icon_path:
        out.append(
            f"<image x='{px}' y='16' width='40' height='40' clip-path='url(#icon)' "
            f"preserveAspectRatio='xMidYMid slice' href='{assets.data_uri(icon_path)}'/>"
        )
        out.append(
            f"<rect x='{px - 0.5}' y='15.5' width='41' height='41' rx='8.5' "
            f"fill='none' stroke='{pal['border']}'/>"
        )
        name_x = px + 50
    else:
        name_x = px
    out.append(f"<text x='{name_x}' y='34' class='name'>{escape(label)}</text>")
    if profile and profile.get("level"):
        out.append(f"<text x='{name_x}' y='49' class='cap'>LEVEL {profile['level']}</text>")
    if role in ROLE_ICONS:
        out.append(_role_icon(role, pal))

    if rank:
        emblem_path = assets.emblem(rank["tier"])
        queue = QUEUE_NAMES.get(rank["queue"], rank["queue"]).upper()
        if emblem_path:
            out.append(
                "<image x='10' y='56' width='58' height='58' "
                f"preserveAspectRatio='xMidYMid meet' href='{assets.data_uri(emblem_path)}'/>"
            )
            rank_x = 72
        else:
            out.append(f"<rect x='{px}' y='64' width='3' height='28' rx='1.5' fill='{tier}'/>")
            rank_x = px + 11
        out.append(
            f"<text x='{rank_x}' y='82' class='rank' fill='{tier}'>"
            f"{escape(rank['tier'].upper())} {escape(rank['division'])}</text>"
        )
        out.append(f"<text x='{rank_x}' y='97' class='cap'>{rank['lp']} LP · {escape(queue)}</text>")

        wins, losses = rank["wins"], rank["losses"]
        wr = wins / (wins + losses) if wins + losses else 0.0
        cx, cy, r, sw = 44, 140, 19, 6
        circ = 2 * math.pi * r
        dash = max(0.0, wr * circ - sw)
        out.append(
            f"<circle cx='{cx}' cy='{cy}' r='{r}' fill='none' stroke='{pal['border']}' "
            f"stroke-opacity='0.55' stroke-width='{sw}'/>"
        )
        out.append(
            f"<circle cx='{cx}' cy='{cy}' r='{r}' fill='none' stroke='{tier}' "
            f"stroke-width='{sw}' stroke-linecap='round' "
            f"stroke-dasharray='{dash:.2f} {circ - dash:.2f}' "
            f"transform='rotate(-90 {cx} {cy})'/>"
        )
        out.append(
            f"<text x='{cx}' y='{cy + 4}' text-anchor='middle' class='pct'>"
            f"{round(wr * 100)}%</text>"
        )
        out.append("<text x='78' y='134' class='cap'>WIN RATE</text>")
        out.append(f"<text x='78' y='150' class='wl'>{wins}W · {losses}L</text>")
        hero_y, cap_y, streak_y = 193, 207, 225
    else:
        out.append(f"<rect x='{px}' y='64' width='3' height='28' rx='1.5' fill='{tier}'/>")
        out.append(f"<text x='{px + 11}' y='76' class='rank' fill='{tier}'>UNRANKED</text>")
        out.append(f"<text x='{px + 11}' y='91' class='cap'>NO RANKED DATA</text>")
        hero_y, cap_y, streak_y = 165, 179, 197

    out.append(f"<text x='{px}' y='{hero_y}' class='hero'>{s['total']:,}</text>")
    out.append(f"<text x='{px}' y='{cap_y}' class='cap'>GAMES · LAST {days} DAYS</text>")
    out.append(
        f"<g transform='translate({px},{streak_y - 11}) scale(0.95)'>"
        f"<path d='{FLAME_PATH}' fill='{pal['flame']}'/>"
        f"<path d='{FLAME_INNER}' fill='{pal['flame_inner']}'/></g>"
    )
    out.append(
        f"<text x='{px + 15}' y='{streak_y}' class='streak'>"
        f"{s['current_streak']} day streak"
        f"<tspan class='streakb'>  ·  Best {s['longest_streak']}</tspan></text>"
    )
    return "".join(out)


def _grid(counts, start, today, tracked_since, weeks, grid_start, peak, s, pal):
    out = []
    for w in range(weeks):
        for r in range(7):
            d = grid_start + datetime.timedelta(days=w * 7 + r)
            if d.day == 1 and start <= d <= today:
                out.append(
                    f"<text x='{GX0 + w * STEP}' y='{MONTH_Y}' class='small'>"
                    f"{MONTHS[d.month - 1]}</text>"
                )
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(
            f"<text x='{DAY_LABEL_X}' y='{GY0 + row * STEP + CELL - 2}' "
            f"text-anchor='end' class='small'>{name}</text>"
        )

    for w in range(weeks):
        for row in range(7):
            d = grid_start + datetime.timedelta(days=w * 7 + row)
            if d < start or d > today:
                continue
            x, y = GX0 + w * STEP, GY0 + row * STEP
            if tracked_since is not None and d < tracked_since:
                fill, extra = pal["empty"], " opacity='0.35'"
                tip = f"No data for {_fmt_day(d)}"
            else:
                n = counts.get(d.isoformat(), 0)
                if n == 0:
                    fill, extra = pal["empty"], ""
                    tip = f"No games on {_fmt_day(d)}"
                else:
                    fill, extra = pal["levels"][min(4, max(1, math.ceil(n * 4 / peak))) - 1], ""
                    tip = f"{_plural(n, 'game')} on {_fmt_day(d)}"
            out.append(
                f"<rect x='{x}' y='{y}' width='{CELL}' height='{CELL}' rx='2' "
                f"fill='{fill}'{extra}><title>{escape(tip)}</title></rect>"
            )

    info = f"Tracked since {_fmt_day(tracked_since or start)}"
    info += f"  ·  {_plural(s['active_days'], 'active day')}"
    if s["peak_day"] is not None:
        info += f"  ·  Peak {_plural(s['peak'], 'game')} on {_fmt_day(s['peak_day'])}"
    out.append(f"<text x='{GX0}' y='{FOOT_Y}' class='small'>{escape(info)}</text>")

    grid_right = GX0 + weeks * STEP - GAP
    sw_x0 = grid_right - 30 - 5 * STEP + GAP
    sw_y = FOOT_Y - CELL + 1
    out.append(
        f"<text x='{sw_x0 - 7}' y='{FOOT_Y}' text-anchor='end' class='small'>Less</text>"
    )
    for i, color in enumerate((pal["empty"],) + tuple(pal["levels"])):
        out.append(
            f"<rect x='{sw_x0 + i * STEP}' y='{sw_y}' width='{CELL}' height='{CELL}' "
            f"rx='2' fill='{color}'/>"
        )
    out.append(f"<text x='{grid_right}' y='{FOOT_Y}' text-anchor='end' class='small'>More</text>")
    return "".join(out)


def render(label, counts, *, today, days=365, tracked_since=None, theme="light",
           rank=None, profile=None, role=None):
    pal = THEMES[theme]
    tier_key = rank["tier"].upper() if rank else None
    tier = TIER_COLORS.get(tier_key, TIER_FALLBACK)[theme == "dark"]

    start = today - datetime.timedelta(days=days - 1)
    grid_start = start - datetime.timedelta(days=(start.weekday() + 1) % 7)
    weeks = (today - grid_start).days // 7 + 1
    width = GX0 + weeks * STEP - GAP + 14

    s = stats.compute(counts, max(start, tracked_since or start), today)
    peak = s["peak"] or 1

    aria = f"{label}: {_plural(s['total'], 'game')} in the last {days} days"
    style = (
        "text{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,"
        "Arial,sans-serif;font-size:12px;fill:%(text)s}"
        ".small{font-size:9px;fill:%(muted)s}"
        ".name{font-size:15px;font-weight:600}"
        ".rank{font-size:13px;font-weight:700;letter-spacing:0.3px}"
        ".cap{font-size:8.5px;font-weight:600;letter-spacing:1px;fill:%(muted)s}"
        ".pct{font-size:11px;font-weight:700}"
        ".wl{font-size:11.5px;font-weight:600}"
        ".hero{font-size:26px;font-weight:800;letter-spacing:-0.5px}"
        ".streak{font-size:11.5px;font-weight:600}"
        ".streakb{font-size:10.5px;font-weight:400;fill:%(muted)s}"
    ) % pal

    out = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{H}' "
        f"viewBox='0 0 {width} {H}' role='img' "
        f"aria-label='{escape(aria, {chr(39): '&apos;'})}'>",
        f"<style>{style}</style>",
        "<defs>"
        f"<clipPath id='card'><rect width='{width}' height='{H}' rx='{RX}'/></clipPath>"
        "<clipPath id='icon'><rect x='18' y='16' width='40' height='40' rx='8'/></clipPath>"
        "<linearGradient id='strip' x1='0' y1='0' x2='1' y2='0'>"
        f"<stop offset='0' stop-color='{tier}'/>"
        f"<stop offset='0.25' stop-color='{tier}'/>"
        f"<stop offset='1' stop-color='{tier}' stop-opacity='0'/>"
        "</linearGradient>"
        "<radialGradient id='glow' cx='0.30' cy='0.15' r='0.7'>"
        f"<stop offset='0' stop-color='{tier}' stop-opacity='{pal['glow_op']}'/>"
        f"<stop offset='1' stop-color='{tier}' stop-opacity='0'/>"
        "</radialGradient>"
        "</defs>",
        "<g clip-path='url(#card)'>",
        f"<rect width='{width}' height='{H}' fill='{pal['bg']}'/>",
        f"<rect width='{PANEL_W}' height='{H}' fill='{pal['panel']}'/>",
        f"<rect width='{PANEL_W}' height='{H}' fill='url(#glow)'/>",
        f"<rect width='{width}' height='3' fill='url(#strip)'/>",
        f"<line x1='{PANEL_W}.5' y1='3' x2='{PANEL_W}.5' y2='{H}' stroke='{pal['border']}'/>",
        _panel(label, s, rank, profile, role, days, pal, tier),
        _grid(counts, start, today, tracked_since, weeks, grid_start, peak, s, pal),
        "</g>",
        f"<rect x='0.5' y='0.5' width='{width - 1}' height='{H - 1}' rx='{RX - 0.5}' "
        f"fill='none' stroke='{pal['border']}'/>",
        "</svg>",
    ]
    return "".join(out) + "\n"
