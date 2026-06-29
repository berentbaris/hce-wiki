#!/usr/bin/env python3
"""
Generate index.html for CCE Wiki from Lua data files.
"""
import re
import html
import os

LUA_DIR = r"C:\wow_addon\ClassicClassesEnhanced"
OUT_FILE = r"C:\cce-wiki\index.html"

# ── Portrait filename mapping ──
PORTRAIT_MAP = {
    "Mountain King": "Mountain_king.jpg",
    "Sister of Steel": "Sistersteel.jpg",
    "Brewmaster": "brewmaster.jpg",
    "Runemaster": "Runemaster.jpg",
    "Berserker": "berserker.jpg",
    "Blademaster": "blademaster.jpg",
    "Brave": "brave.jpg",
    "Tinker": "tinker.jpg",
    "Prospector": "pros.jpg",
    "Buccaneer": "Buccaneer.jpg",
    "Warden": "warden.jpg",
    "Demon Hunter": "DH.jpg",
    "Dark Ranger": "dark_ranger.jpg",
    "Pyremaster": "Pyremaster.jpg",
    "Death Knight": "Death_Knight.jpg",
    "Necromancer": "Necromancer.jpg",
    "Graven One": "graven.jpg",
    "Druid of the Claw": "Claw.jpg",
    "Dragonsworn": "dragonsworn.jpg",
    "Ley Walker": "ley.jpg",
    "Plagueshifter": "Plagueshifter.jpg",
    "Savagekin": "savage.jpg",
    "Beastmaster": "Orcbeastmaster.jpg",
    "Mountaineer": "Mountaineer.jpg",
    "Elven Ranger": "ElvenRanger.jpg",
    "Wilderness Stalker": "Wildernessstalker.jpg",
    "Earthcaller": "Earthcaller.jpg",
    "Witch Doctor": "witch_doctor.jpg",
    "Spiritwalker": "spirit_walk.jpg",
    "Spirit Champion": "spirit_champ.jpg",
    "Scarlet Champion": "scarlet_champ.jpg",
    "Exemplar": "Exemplar.jpg",
    "Templar": "Templar.png",
    "Priestess of the Moon": "Moon.jpg",
    "Apothecary": "Apothecary.jpg",
    "Shadow Hunter": "shadow_hunter.jpg",
    "Lightslayer": "Lightslayer.jpg",
    "Bloodmage": "Bloodmage.jpg",
    "Techno-mage": "Techno-mage.jpg",
    "Spellblade": "Spellblade.jpg",
    "Hedge Wizard": "Hedgewizard.jpg",
    "Archmage of Kirin Tor": "kirin_tor.jpg",
    "Barbarian": "barbarian.jpg",
}

CLASS_ORDER = [
    ("WARRIOR", "Warrior", "#C69B6D", "&#9876;"),
    ("ROGUE", "Rogue", "#FFF468", "&#128481;"),
    ("WARLOCK", "Warlock", "#8788EE", "&#128302;"),
    ("DRUID", "Druid", "#FF7C0A", "&#127807;"),
    ("HUNTER", "Hunter", "#AAD372", "&#127993;"),
    ("SHAMAN", "Shaman", "#0070DD", "&#9889;"),
    ("PALADIN", "Paladin", "#F48CBA", "&#128737;"),
    ("PRIEST", "Priest", "#FFFFFF", "&#10024;"),
    ("MAGE", "Mage", "#3FC7EB", "&#10052;"),
]

CHAR_ORDER_BY_CLASS = {
    "WARRIOR": ["Mountain King", "Sister of Steel", "Brewmaster", "Runemaster", "Berserker", "Blademaster", "Brave", "Tinker"],
    "ROGUE": ["Barbarian", "Prospector", "Buccaneer", "Warden", "Demon Hunter"],
    "WARLOCK": ["Pyremaster", "Death Knight", "Necromancer"],
    "DRUID": ["Druid of the Claw", "Dragonsworn", "Ley Walker", "Plagueshifter", "Savagekin"],
    "HUNTER": ["Beastmaster", "Mountaineer", "Elven Ranger", "Wilderness Stalker"],
    "SHAMAN": ["Earthcaller", "Witch Doctor", "Spiritwalker", "Spirit Champion"],
    "PALADIN": ["Scarlet Champion", "Exemplar", "Templar"],
    "PRIEST": ["Priestess of the Moon", "Apothecary", "Shadow Hunter", "Lightslayer"],
    "MAGE": ["Bloodmage", "Techno-mage", "Spellblade", "Hedge Wizard", "Archmage of Kirin Tor"],
}

TALENT_TREES = {
    "WARRIOR": {1: "Arms", 2: "Fury", 3: "Protection"},
    "ROGUE": {1: "Assassination", 2: "Combat", 3: "Subtlety"},
    "WARLOCK": {1: "Affliction", 2: "Demonology", 3: "Destruction"},
    "DRUID": {1: "Balance", 2: "Feral", 3: "Restoration"},
    "HUNTER": {1: "Beast Mastery", 2: "Marksmanship", 3: "Survival"},
    "SHAMAN": {1: "Elemental", 2: "Enhancement", 3: "Restoration"},
    "PALADIN": {1: "Holy", 2: "Protection", 3: "Retribution"},
    "PRIEST": {1: "Discipline", 2: "Holy", 3: "Shadow"},
    "MAGE": {1: "Arcane", 2: "Fire", 3: "Frost"},
}


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def extract_braced_block(text, start_pos):
    """From position right after opening {, find matching } using brace counting."""
    depth = 1
    pos = start_pos
    while pos < len(text) and depth > 0:
        ch = text[pos]
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
        elif ch == '"':
            # Skip string contents
            pos += 1
            while pos < len(text) and text[pos] != '"':
                if text[pos] == '\\':
                    pos += 1
                pos += 1
        elif ch == '-' and pos + 1 < len(text) and text[pos + 1] == '-':
            # Skip comment to end of line
            while pos < len(text) and text[pos] != '\n':
                pos += 1
        pos += 1
    return text[start_pos:pos - 1]


def parse_lore_data(text):
    lore = {}
    for m in re.finditer(r'\["([^"]+)"\]\s*=\s*"((?:[^"\\]|\\.)*)"', text):
        name = m.group(1)
        lore_text = m.group(2).replace('\\"', '"').replace("\\'", "'").replace("\\n", "\n")
        lore[name] = lore_text
    return lore


def parse_talent_requirements(text):
    talents = {}
    current_char = None
    for line in text.split("\n"):
        m = re.match(r'\s*\["([^"]+)"\]\s*=\s*\{', line)
        if m:
            current_char = m.group(1)
            talents[current_char] = []
            continue
        if current_char is not None:
            m = re.match(r'\s*R\("([^"]+)",\s*(\d+),\s*(\d+),\s*(\d+)(?:,\s*(\d+))?\)', line)
            if m:
                talents[current_char].append({
                    "name": m.group(1),
                    "tab": int(m.group(2)),
                    "rank": int(m.group(3)),
                    "level": int(m.group(4)),
                    "endLevel": int(m.group(5)) if m.group(5) else None,
                })
            if re.match(r'\s*\},?\s*$', line) and not re.match(r'\s*R\(', line):
                current_char = None
    return talents


def parse_q_from_text(text):
    """Extract Q() entries from a text block."""
    quests = []
    for qm in re.finditer(r'Q\("((?:[^"\\]|\\.)*)",\s*(\d+),\s*(\d+)\)', text):
        quests.append({
            "name": qm.group(1).replace("\\'", "'").replace('\\"', '"'),
            "level": int(qm.group(2)),
            "questID": int(qm.group(3)),
        })
    return quests


def parse_character_data(text):
    # Parse challenge descriptions
    challenge_descs = {}
    cd_start = text.find("CCE.ChallengeDescriptions")
    if cd_start >= 0:
        brace = text.find("{", cd_start)
        cd_block = extract_braced_block(text, brace + 1)
        for m in re.finditer(r'\["([^"]+)"\]\s*=\s*"((?:[^"\\]|\\.)*)"', cd_block):
            challenge_descs[m.group(1)] = m.group(2).replace('\\"', '"').replace("\\'", "'")

    characters = {}
    chars_start = text.find("CCE.Characters = {")
    if chars_start < 0:
        return characters, challenge_descs

    chars_brace = text.find("{", chars_start)
    chars_text = text[chars_brace + 1:]

    # Find character blocks
    char_pattern = re.compile(r'\["([^"]+)"\]\s*=\s*\{')
    # Filter to only character names (not challenge descriptions which were already parsed)
    char_matches = []
    for m in char_pattern.finditer(chars_text):
        name = m.group(1)
        # Must have a class field nearby
        block_start = m.end()
        peek = chars_text[block_start:block_start + 200]
        if 'class' in peek and ('WARRIOR' in peek or 'ROGUE' in peek or 'WARLOCK' in peek or
                                'DRUID' in peek or 'HUNTER' in peek or 'SHAMAN' in peek or
                                'PALADIN' in peek or 'PRIEST' in peek or 'MAGE' in peek):
            char_matches.append((name, block_start))

    for i, (name, start) in enumerate(char_matches):
        block = extract_braced_block(chars_text, start)
        char = parse_single_char(name, block)
        if char:
            characters[name] = char

    return characters, challenge_descs


def parse_single_char(name, block):
    char = {"name": name}

    # Simple string fields
    for field in ["class", "spec", "race", "gender", "questTheme", "gameplay"]:
        m = re.search(rf'^\s*{field}\s*=\s*"([^"]*)"', block, re.MULTILINE)
        if m:
            char[field] = m.group(1)

    # Boolean selfFound
    m = re.search(r'^\s*selfFound\s*=\s*(true|false)', block, re.MULTILINE)
    if m:
        char["selfFound"] = m.group(1) == "true"

    # selfFoundByFaction
    m = re.search(r'selfFoundByFaction\s*=\s*\{', block)
    if m:
        sf_block = extract_braced_block(block, m.end())
        alliance_m = re.search(r'Alliance\s*=\s*(true|false)', sf_block)
        horde_m = re.search(r'Horde\s*=\s*(true|false)', sf_block)
        if alliance_m and horde_m:
            a = alliance_m.group(1) == "true"
            h = horde_m.group(1) == "true"
            if a and not h:
                char["selfFound"] = "Alliance only"
            elif not a and h:
                char["selfFound"] = "Horde only"
            elif a and h:
                char["selfFound"] = True
            else:
                char["selfFound"] = False

    # Professions
    char["professions"] = []
    m = re.search(r'^\s*professions\s*=\s*\{([^}]*)\}', block, re.MULTILINE)
    if m:
        char["professions"] = re.findall(r'"([^"]+)"', m.group(1))

    # Recommended profession
    m = re.search(r'recommendedProfession\s*=\s*\{', block)
    if m:
        rp_block = extract_braced_block(block, m.end())
        nm = re.search(r'name\s*=\s*"([^"]*)"', rp_block)
        rm = re.search(r'reason\s*=\s*"((?:[^"\\]|\\.)*)"', rp_block)
        if nm and rm:
            char["recommendedProfession"] = {
                "name": nm.group(1),
                "reason": rm.group(2) if rm.lastindex >= 2 else rm.group(1),
            }
            char["recommendedProfession"]["reason"] = rm.group(1).replace('\\"', '"').replace("\\'", "'")

    # Equipment
    char["equipment"] = parse_e_field(block, "equipment")

    # Challenges
    char["challenges"] = parse_e_field(block, "challenges")

    # Optional challenges
    char["optionalChallenges"] = parse_e_field(block, "optionalChallenges")

    # Simple quests
    char["quests"] = parse_q_field(block, "quests")

    # questsByFaction
    m = re.search(r'questsByFaction\s*=\s*\{', block)
    if m:
        faction_block = extract_braced_block(block, m.end())
        char["questsByFaction"] = {}
        for faction in ["Alliance", "Horde"]:
            fm = re.search(rf'{faction}\s*=\s*\{{', faction_block)
            if fm:
                fb = extract_braced_block(faction_block, fm.end())
                # Check for default/homebound inside
                dm = re.search(r'default\s*=\s*\{', fb)
                if dm:
                    db = extract_braced_block(fb, dm.end())
                    char["questsByFaction"][faction] = parse_q_from_text(db)
                else:
                    char["questsByFaction"][faction] = parse_q_from_text(fb)

    # questsByHomebound
    m = re.search(r'questsByHomebound\s*=\s*\{', block)
    if m:
        hb_block = extract_braced_block(block, m.end())
        dm = re.search(r'default\s*=\s*\{', hb_block)
        if dm:
            db = extract_braced_block(hb_block, dm.end())
            quests = parse_q_from_text(db)
            if quests:
                char["quests"] = quests

    # questGroups
    m = re.search(r'questGroups\s*=\s*\{', block)
    if m:
        qg_block = extract_braced_block(block, m.end())
        groups = []
        for gm in re.finditer(r'\{\s*theme\s*=\s*"([^"]+)",\s*count\s*=\s*(\d+)\s*\}', qg_block):
            groups.append({"theme": gm.group(1), "count": int(gm.group(2))})
        if groups:
            char["questGroups"] = groups

    # Companion
    m = re.search(r'^\s*companion\s*=\s*E\("([^"]+)",\s*(\d+)\)', block, re.MULTILINE)
    if m:
        char["companion"] = {"desc": m.group(1), "level": int(m.group(2))}

    # Hunter pet
    m = re.search(r'^\s*pet\s*=\s*E\("([^"]+)",\s*(\d+)\)', block, re.MULTILINE)
    if m:
        char["pet"] = {"desc": m.group(1), "level": int(m.group(2))}

    # Mount
    m = re.search(r'^\s*mount\s*=\s*E\("([^"]+)",\s*(\d+)\)', block, re.MULTILINE)
    if m:
        char["mount"] = {"desc": m.group(1), "level": int(m.group(2))}

    return char


def parse_e_field(block, field_name):
    """Parse E() entries from a named field using brace counting."""
    entries = []
    m = re.search(rf'^\s*{field_name}\s*=\s*\{{', block, re.MULTILINE)
    if not m:
        return entries
    field_text = extract_braced_block(block, m.end())
    for em in re.finditer(r'E\("((?:[^"\\]|\\.)*)",\s*(\d+)(?:,\s*(\d+))?\)', field_text):
        entry = {
            "desc": em.group(1).replace("\\'", "'").replace('\\"', '"'),
            "level": int(em.group(2)),
        }
        if em.group(3):
            entry["endLevel"] = int(em.group(3))
        entries.append(entry)
    return entries


def parse_q_field(block, field_name):
    """Parse Q() entries from a simple quests field using brace counting."""
    entries = []
    # Only match top-level quests = { ... }, not questsByFaction etc.
    m = re.search(rf'^\s*{field_name}\s*=\s*\{{', block, re.MULTILINE)
    if not m:
        return entries
    # Make sure it's not questsByFaction or questsByHomebound
    line_start = block.rfind('\n', 0, m.start()) + 1
    line = block[line_start:m.end()]
    if 'questsBy' in line:
        return entries
    field_text = extract_braced_block(block, m.end())
    return parse_q_from_text(field_text)


# ── HTML helpers ──

def esc(s):
    return html.escape(str(s), quote=True)

def make_slug(name):
    return name.lower().replace(" ", "-").replace("'", "")

def make_initials(name):
    parts = name.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return name[:2].upper()

def make_wiki_url(name):
    return "https://warcraft.wiki.gg/wiki/" + name.replace(" ", "_")

def render_level(entry):
    level = entry.get("level", 1)
    end = entry.get("endLevel")
    if end:
        return f"Lv {level}&ndash;{end}"
    return f"Lv {level}"


def render_character(char, color, lore, talents, challenge_descs, wow_class):
    name = char["name"]
    slug = make_slug(name)
    initials = make_initials(name)
    portrait = PORTRAIT_MAP.get(name)
    wiki_url = make_wiki_url(name)

    sf = char.get("selfFound", True)
    if sf is True:
        sf_display = "Yes"
    elif sf is False:
        sf_display = "No"
    else:
        sf_display = str(sf)

    meta_parts = [f'<span class="ml">Spec:</span> {esc(char.get("spec", ""))}']
    race = char.get("race", "Any race")
    meta_parts.append(f'<span class="ml">Race:</span> {esc(race) if race != "Any race" else "Any"}')
    gender = char.get("gender", "Any gender")
    if gender != "Any gender":
        meta_parts.append(f'<span class="ml">Gender:</span> {esc(gender)}')
    meta_parts.append(f'<span class="ml">Self-Found:</span> {esc(sf_display)}')
    meta_line = " &middot; ".join(meta_parts)
    meta_line += f' &middot; <a href="{esc(wiki_url)}" target="_blank" rel="noopener" style="color:{color};font-weight:600;font-size:.82rem" title="Warcraft Wiki">&#128214; Wiki</a>'

    if portrait:
        avatar_html = f'<img src="portraits/{esc(portrait)}" alt="{esc(name)}" class="avatar-img">'
        fb_style = f'background:{color}22;border-color:{color};display:none'
    else:
        avatar_html = ''
        fb_style = f'background:{color}22;border-color:{color}'
    avatar_section = f'<div class="avatar-wrap">{avatar_html}<div class="avatar-fb" style="{fb_style}"><span style="color:{color}">{initials}</span></div></div>'

    body_parts = []

    # Lore
    lore_text = lore.get(name, "")
    if lore_text:
        sentences = lore_text.split(". ")
        summary = ". ".join(sentences[:3])
        if not summary.endswith("."):
            summary += "."
        body_parts.append(f'<div class="lore"><p>{esc(summary)}</p></div>')

    # Professions
    if char.get("professions"):
        items = "".join(f"<li>{esc(p)}</li>" for p in char["professions"])
        body_parts.append(f'<div class="rs"><h4>Professions (Required)</h4><ul>{items}</ul></div>')

    # Recommended profession
    rec = char.get("recommendedProfession")
    if rec:
        body_parts.append(f'<div class="rs"><h4>Recommended Profession</h4><p><strong>{esc(rec["name"])}</strong> &mdash; {esc(rec["reason"])}</p></div>')

    # Challenge rules
    if char.get("challenges"):
        rows = ""
        for c in char["challenges"]:
            desc_text = challenge_descs.get(c["desc"], c["desc"])
            rows += f'<tr><td><strong>{esc(c["desc"])}</strong></td><td>{render_level(c)}</td><td>{esc(desc_text)}</td></tr>'
        body_parts.append(f'<div class="rs"><h4>Challenge Rules</h4><table class="rt"><tr><th>Challenge</th><th>Level</th><th>Description</th></tr>{rows}</table></div>')

    # Equipment
    if char.get("equipment"):
        rows = ""
        for e in char["equipment"]:
            rows += f'<tr><td>{esc(e["desc"])}</td><td>{render_level(e)}</td></tr>'
        body_parts.append(f'<div class="rs"><h4>Equipment Requirements</h4><table class="rt"><tr><th>Requirement</th><th>Level</th></tr>{rows}</table></div>')

    # Talents
    char_talents = talents.get(name, [])
    if char_talents:
        trees = TALENT_TREES.get(wow_class, {})
        rows = ""
        for t in char_talents:
            tree_name = trees.get(t["tab"], f"Tree {t['tab']}")
            rows += f'<tr><td>{esc(t["name"])}</td><td>{esc(tree_name)}</td><td>{t["rank"]}</td><td>Lv {t["level"]}</td></tr>'
        body_parts.append(f'<div class="rs"><h4>Talent Requirements</h4><table class="rt"><tr><th>Talent</th><th>Tree</th><th>Rank</th><th>By Level</th></tr>{rows}</table></div>')

    # Quests
    quests = char.get("quests", [])
    quest_theme = char.get("questTheme", "")
    quest_groups = char.get("questGroups")
    has_faction_quests = bool(char.get("questsByFaction"))

    if has_faction_quests and not quests:
        # Pure faction-based quests (Brewmaster, Spellblade, Necromancer, etc.)
        for faction in ["Alliance", "Horde"]:
            fq = char["questsByFaction"].get(faction, [])
            if fq:
                rows = "".join(f'<tr><td>{esc(q["name"])}</td><td>Lv {q["level"]}</td></tr>' for q in fq)
                suffix = " (A)" if faction == "Alliance" else " (H)"
                theme = f'{quest_theme}{suffix}' if quest_theme else faction
                body_parts.append(f'<div class="rs"><h4>Quest Milestones <span class="qt">({esc(theme)})</span></h4><table class="rt"><tr><th>Quest</th><th>By Level</th></tr>{rows}</table></div>')
    elif quests and quest_groups:
        # Multi-group quests (Shadow Hunter, Graven One)
        rows = ""
        offset = 0
        for qg in quest_groups:
            theme = qg["theme"]
            count = qg["count"]
            group_quests = quests[offset:offset + count]
            if group_quests:
                rows += f'<tr><td colspan="2" style="color:var(--dim);font-style:italic;border-bottom:1px solid var(--brd);padding-top:8px"><strong>{esc(theme)}</strong></td></tr>'
                rows += "".join(f'<tr><td>{esc(q["name"])}</td><td>Lv {q["level"]}</td></tr>' for q in group_quests)
            offset += count
        body_parts.append(f'<div class="rs"><h4>Quest Milestones</h4><table class="rt"><tr><th>Quest</th><th>By Level</th></tr>{rows}</table></div>')
    elif quests:
        rows = "".join(f'<tr><td>{esc(q["name"])}</td><td>Lv {q["level"]}</td></tr>' for q in quests)
        theme_html = f' <span class="qt">({esc(quest_theme)})</span>' if quest_theme else ""
        body_parts.append(f'<div class="rs"><h4>Quest Milestones{theme_html}</h4><table class="rt"><tr><th>Quest</th><th>By Level</th></tr>{rows}</table></div>')

    # Companion / Pet / Mount
    cpm_items = []
    if char.get("companion"):
        c = char["companion"]
        cpm_items.append(f'<li><strong>Companion:</strong> {esc(c["desc"])} (Lv {c["level"]})</li>')
    if char.get("pet"):
        p = char["pet"]
        cpm_items.append(f'<li><strong>Hunter Pet:</strong> {esc(p["desc"])} (Lv {p["level"]})</li>')
    if char.get("mount"):
        mt = char["mount"]
        cpm_items.append(f'<li><strong>Mount:</strong> {esc(mt["desc"])} (Lv {mt["level"]})</li>')
    if cpm_items:
        body_parts.append(f'<div class="rs"><h4>Companion / Pet / Mount</h4><ul>{"".join(cpm_items)}</ul></div>')

    body_html = "".join(body_parts)

    return f"""
    <div class="cc" id="{slug}">
      <div class="ch" style="border-left:4px solid {color}" onclick="this.parentElement.classList.toggle('ex')">
        <div class="chc">
          {avatar_section}
          <div class="ctb">
            <h3 style="color:{color}">{esc(name)}</h3>
            <div class="meta">{meta_line}</div>
          </div>
        </div>
        <span class="ei">&#9660;</span>
      </div>
      <div class="cb">{body_html}</div>
    </div>
"""


def generate_html(characters, lore, talents, challenge_descs):
    total_chars = sum(len(CHAR_ORDER_BY_CLASS.get(c, [])) for c, _, _, _ in CLASS_ORDER)

    nav_links = "\n".join(
        f'<a href="#{cn.lower()}" class="nc" style="color:{co}">{ic} {cn}</a>'
        for _, cn, co, ic in CLASS_ORDER
    )

    sections = []
    for class_key, class_name, color, icon in CLASS_ORDER:
        char_names = CHAR_ORDER_BY_CLASS.get(class_key, [])
        cards = []
        for cn in char_names:
            char = characters.get(cn)
            if char:
                cards.append(render_character(char, color, lore, talents, challenge_descs, class_key))
            else:
                print(f"WARNING: Character '{cn}' not found in data")
        sections.append(f'<div class="cs" id="{class_name.lower()}"><h2 style="color:{color}">{icon} {class_name}</h2>\n{"".join(cards)}</div>')

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Classic Classes Enhanced — Wiki</title>
<style>
:root{{--bg:#1a1a2e;--bg2:#16213e;--bg3:#0f3460;--text:#e0e0e0;--dim:#999;--gold:#ffd700;--brd:#2a2a4a}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--text);line-height:1.6}}
a{{color:var(--gold);text-decoration:none}}a:hover{{text-decoration:underline}}
.hero{{text-align:center;padding:60px 20px 40px;background:linear-gradient(180deg,var(--bg3),var(--bg));border-bottom:1px solid var(--brd)}}
.hero h1{{font-size:2.5rem;color:var(--gold);margin-bottom:12px;text-shadow:0 0 20px rgba(255,215,0,.3)}}
.hero .sub{{font-size:1.15rem;color:var(--dim);max-width:700px;margin:0 auto 24px}}
.badge{{display:inline-block;background:var(--bg3);border:1px solid var(--gold);color:var(--gold);padding:6px 16px;border-radius:20px;font-size:.9rem;margin:4px}}
.about{{max-width:900px;margin:40px auto;padding:0 20px}}
.ag{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:16px;margin-top:20px}}
.ac{{background:var(--bg2);border:1px solid var(--brd);border-radius:8px;padding:20px}}
.ac h3{{color:var(--gold);font-size:1rem;margin-bottom:8px}}.ac p{{font-size:.9rem;color:var(--dim)}}
.cn{{display:flex;flex-wrap:wrap;justify-content:center;gap:8px;padding:20px;max-width:900px;margin:0 auto;position:sticky;top:0;background:var(--bg);z-index:100;border-bottom:1px solid var(--brd)}}
.nc{{padding:8px 14px;background:var(--bg2);border:1px solid var(--brd);border-radius:6px;font-size:.85rem;font-weight:600;transition:background .2s}}.nc:hover{{background:var(--bg3);text-decoration:none}}
.sb{{max-width:900px;margin:20px auto;padding:0 20px}}
.sb input{{width:100%;padding:12px 16px;background:var(--bg2);border:1px solid var(--brd);border-radius:8px;color:var(--text);font-size:1rem;outline:none}}
.sb input:focus{{border-color:var(--gold)}}.sb input::placeholder{{color:var(--dim)}}
.cs{{max-width:900px;margin:40px auto 0;padding:0 20px}}
.cs h2{{font-size:1.6rem;padding-bottom:12px;border-bottom:1px solid var(--brd);margin-bottom:16px}}
.cc{{background:var(--bg2);border:1px solid var(--brd);border-radius:8px;margin-bottom:12px;overflow:hidden;transition:border-color .2s}}.cc:hover{{border-color:#444}}
.ch{{display:flex;align-items:center;justify-content:space-between;padding:16px 20px;cursor:pointer;user-select:none}}
.chc{{display:flex;align-items:center;gap:16px;flex:1;min-width:0}}
.avatar-wrap{{width:52px;height:52px;flex-shrink:0;position:relative}}
.avatar-img{{width:52px;height:52px;border-radius:10px;object-fit:cover}}
.avatar-fb{{width:52px;height:52px;border-radius:10px;display:flex;align-items:center;justify-content:center;border:2px solid}}
.avatar-fb span{{font-size:1.1rem;font-weight:800;letter-spacing:1px}}
.ctb h3{{font-size:1.15rem;margin-bottom:2px}}.meta{{font-size:.82rem;color:var(--dim)}}.ml{{color:var(--text);font-weight:600}}
.ei{{font-size:.8rem;color:var(--dim);transition:transform .2s;flex-shrink:0;margin-left:12px}}
.cc.ex .ei{{transform:rotate(180deg)}}
.cb{{display:none;padding:0 20px 20px}}.cc.ex .cb{{display:block}}
.lore{{background:rgba(255,215,0,.05);border-left:3px solid var(--gold);padding:12px 16px;margin-bottom:16px;border-radius:0 6px 6px 0}}
.lore p{{font-style:italic;font-size:.9rem;color:var(--dim)}}
.rs{{margin-bottom:16px}}.rs h4{{color:var(--gold);font-size:.9rem;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px}}
.rs ul{{list-style:none;padding:0}}.rs ul li{{padding:4px 0;font-size:.9rem;border-bottom:1px solid rgba(255,255,255,.05)}}.rs ul li:last-child{{border-bottom:none}}
.qt{{font-weight:normal;color:var(--dim);font-size:.85rem}}
.rt{{width:100%;border-collapse:collapse;font-size:.88rem}}
.rt th{{text-align:left;color:var(--dim);font-weight:600;padding:6px 8px;border-bottom:1px solid var(--brd);font-size:.8rem;text-transform:uppercase;letter-spacing:.3px}}
.rt td{{padding:6px 8px;border-bottom:1px solid rgba(255,255,255,.04)}}.rt tr:last-child td{{border-bottom:none}}
footer{{text-align:center;padding:40px 20px;color:var(--dim);font-size:.85rem;border-top:1px solid var(--brd);margin-top:60px}}
@media(max-width:600px){{.hero h1{{font-size:1.8rem}}.ch{{padding:12px 14px}}.avatar-wrap,.avatar-img,.avatar-fb{{width:40px;height:40px}}.avatar-fb span{{font-size:.9rem}}.ctb h3{{font-size:1rem}}.rt{{font-size:.82rem}}}}
</style>
</head>
<body>
<div class="hero">
  <h1>Classic Classes Enhanced</h1>
  <p class="sub">{total_chars} lore-based character archetypes for WoW Classic. Pick an enhanced class and the addon tracks your challenge rules, gear restrictions, quest milestones, and talent requirements as you level.</p>
  <span class="badge">v0.8.6</span>
  <span class="badge">WoW Classic Era</span>
  <span class="badge">{total_chars} Enhanced Classes</span>
</div>
<div class="about"><div class="ag">
  <div class="ac"><h3>Real-Time Tracking</h3><p>The addon monitors equipment, talents, quests, challenges, and more in real time. Violations are flagged instantly with alerts.</p></div>
  <div class="ac"><h3>Requirements Panel</h3><p>A persistent, draggable checklist: green checkmarks for met rules, red crosses for violations, grey for level-locked requirements. Access via <code>/cce panel</code>.</p></div>
  <div class="ac"><h3>Auto-Detection</h3><p>Your enhanced class is determined by race, gender, and class. The addon detects it on login. Use <code>/cce pick</code> to choose manually.</p></div>
  <div class="ac"><h3>Installation</h3><p>Drop the <code>ClassicClassesEnhanced</code> folder into your <code>Interface/AddOns</code> directory. Works with Classic Era (Interface 11507).</p></div>
</div></div>
<nav class="cn">{nav_links}</nav>
<div class="sb"><input type="text" id="si" placeholder="Search classes, challenges, talents..." oninput="fc()"></div>
{chr(10).join(sections)}
<footer>
  <p>Classic Classes Enhanced by <strong>Beba</strong></p>
  <p><a href="https://buymeacoffee.com/berentbaris">Buy Me a Coffee</a></p>
</footer>
<script>
function fc(){{const q=document.getElementById('si').value.toLowerCase();document.querySelectorAll('.cc').forEach(c=>{{c.style.display=c.textContent.toLowerCase().includes(q)?'':'none'}});document.querySelectorAll('.cs').forEach(s=>{{const v=[...s.querySelectorAll('.cc')].filter(c=>c.style.display!=='none');s.style.display=v.length===0?'none':''}})}}
if(window.location.hash){{const el=document.querySelector(window.location.hash);if(el&&el.classList.contains('cc')){{el.classList.add('ex');setTimeout(()=>el.scrollIntoView({{behavior:'smooth',block:'start'}}),100)}}}}

</script></body>
</html>'''


def main():
    char_lua = read_file(os.path.join(LUA_DIR, "CharacterData.lua"))
    lore_lua = read_file(os.path.join(LUA_DIR, "LoreData.lua"))
    talent_lua = read_file(os.path.join(LUA_DIR, "TalentRequirements.lua"))

    lore = parse_lore_data(lore_lua)
    talents = parse_talent_requirements(talent_lua)
    characters, challenge_descs = parse_character_data(char_lua)

    print(f"Parsed {len(characters)} characters")
    print(f"Parsed {len(lore)} lore entries")
    print(f"Parsed {len(talents)} talent requirement entries")
    print(f"Challenge descriptions: {len(challenge_descs)}")

    for class_key, class_name, _, _ in CLASS_ORDER:
        char_names = CHAR_ORDER_BY_CLASS.get(class_key, [])
        found = [n for n in char_names if n in characters]
        missing = [n for n in char_names if n not in characters]
        print(f"  {class_name}: {len(found)} found" + (f", MISSING: {missing}" if missing else ""))

    # Detail check
    for cn in ["Brewmaster", "Spellblade", "Shadow Hunter", "Graven One", "Necromancer"]:
        c = characters.get(cn, {})
        q = c.get("quests", [])
        qf = c.get("questsByFaction", {})
        qg = c.get("questGroups")
        print(f"  {cn}: quests={len(q)}, questsByFaction={'A:'+str(len(qf.get('Alliance',[])))+'|H:'+str(len(qf.get('Horde',[]))) if qf else 'none'}, questGroups={qg}")

    html_output = generate_html(characters, lore, talents, challenge_descs)

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_output)

    print(f"\nWrote {len(html_output)} bytes to {OUT_FILE}")


if __name__ == "__main__":
    main()
