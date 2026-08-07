import urllib.request
import re
import html
import json
import ssl
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(SCRIPT_DIR, "data.json")

def clean_text(text):
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def format_date(raw_date):
    months = {
        "ene": "01", "feb": "02", "mar": "03", "abr": "04", "may": "05", "jun": "06",
        "jul": "07", "ago": "08", "sep": "09", "oct": "10", "nov": "11", "dic": "12"
    }
    raw_date = raw_date.lower().strip()
    match = re.search(r'(\d+)\s+([a-z]{3})\s+(\d{4})', raw_date)
    if match:
        day = match.group(1).zfill(2)
        month_name = match.group(2)
        year = match.group(3)
        month = months.get(month_name[:3], "07")
        return f"{day}/{month}/{year}"
    return raw_date

def get_aliases(display_name):
    parts = display_name.split()
    aliases = [display_name]
    if len(parts) == 3:
        aliases.append(f"{parts[0]} {parts[1]}")
        aliases.append(f"{parts[1]} {parts[2]}")
    elif len(parts) == 4:
        aliases.append(f"{parts[0]} {parts[2]}")
        aliases.append(f"{parts[0]} {parts[1]} {parts[2]}")
        aliases.append(f"{parts[2]} {parts[3]}")
    elif len(parts) > 4:
        aliases.append(f"{parts[0]} {parts[-2]}")
        aliases.append(f"{parts[-2]} {parts[-1]}")
    return list(set(aliases))
def fetch_spley_bills(events_override, all_names):
    url = "https://api.congreso.gob.pe/spley-portal-service/proyecto-ley/lista-con-filtro"
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    payload = json.dumps({"perParId": 2026, "pagina": 1, "registros": 100}).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"},
        method="POST"
    )

    try:
        print("Fetching official bills from SPLEY API...")
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            proyectos = res.get("data", {}).get("proyectos", [])
            print(f"Successfully fetched {len(proyectos)} bills from SPLEY API.")

            for p in proyectos:
                num_pley = p.get('proyectoLey', 'Proyecto de Ley')
                titulo = clean_text(p.get('titulo', ''))
                autores_raw = p.get('autores', '') or ''
                fec = p.get('fecPresentacion', '')[:10]
                if fec:
                    parts = fec.split("-")
                    if len(parts) == 3:
                        fec = f"{parts[2]}/{parts[1]}/{parts[0]}"
                else:
                    fec = "05/08/2026"

                pley_url = f"https://wb2server.congreso.gob.pe/spley-portal/#/expediente/{p.get('perParId', 2026)}/{p.get('pleyNum', '')}"

                for leg_name in all_names:
                    aliases = get_aliases(leg_name)
                    if any(alias.lower() in autores_raw.lower() for alias in aliases):
                        if leg_name not in events_override:
                            events_override[leg_name] = []
                        
                        already_added = any(ev.get("a") == f"Proyecto de Ley {num_pley}: {titulo}" for ev in events_override[leg_name])
                        if not already_added:
                            events_override[leg_name].append({
                                "t": "📜",
                                "a": f"Proyecto de Ley {num_pley}: {titulo}",
                                "d": fec,
                                "tipo": "Proyecto de Ley",
                                "url": pley_url,
                                "pts": 5
                            })
                            print(f"Added bill event (+5 Pts) for: {leg_name} -> {num_pley}")
    except Exception as e:
        print(f"Error fetching SPLEY bills: {e}")

def main():
    if not os.path.exists(DATA_PATH):
        print(f"Error: {DATA_PATH} not found.")
        return

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Fetch Congress news page
    url = "https://comunicaciones.congreso.gob.pe/noticias/"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    )

    try:
        print(f"Fetching news from {url}...")
        with urllib.request.urlopen(req, timeout=20) as response:
            raw_bytes = response.read()
        html_content = raw_bytes.decode("utf-8", errors="replace")
        print("Successfully downloaded news page.")
    except Exception as e:
        print(f"Error fetching news: {e}")
        return

    # 2. Parse articles
    blocks = html_content.split('<div class="item-noticia')
    articles = []

    for block in blocks[1:]:
        title_match = re.search(r'<p class="titulo-20"><a href="([^"]+)">([^<]+)</a></p>', block)
        if not title_match:
            continue
        
        art_url = title_match.group(1).strip()
        title = clean_text(title_match.group(2))
        
        date_match = re.search(r'<span class="parrafo-clock"><i[^>]*></i>\s*(.*?)\s*</span>', block)
        raw_date = date_match.group(1).strip() if date_match else ""
        formatted_date = format_date(raw_date)
        
        summary_match = re.search(r'<div class="parrafo-16">(.*?)</div>', block, re.DOTALL)
        summary = ""
        if summary_match:
            summary = re.sub(r'<[^>]+>', '', summary_match.group(1)).strip()
            summary = clean_text(summary)
            
        articles.append({
            "title": title,
            "url": art_url,
            "date": formatted_date,
            "raw_date": raw_date,
            "summary": summary
        })

    print(f"Parsed {len(articles)} articles from home page.")

    # 3. Classify and link to senators/deputies
    senado_news = []
    diputados_news = []
    
    all_senators = []
    for party, names in data["SNMS"].items():
        all_senators.extend(names)
        
    all_deputies = []
    for party, names in data["DNMS"].items():
        all_deputies.extend(names)

    events_override = data.get("events_override", {})

    for art in articles:
        title_and_summary = f"{art['title']} {art['summary']}"
        
        mentioned_senators = []
        for sen in all_senators:
            aliases = get_aliases(sen)
            if any(alias.lower() in title_and_summary.lower() for alias in aliases):
                mentioned_senators.append(sen)
                
        mentioned_deputies = []
        for dep in all_deputies:
            aliases = get_aliases(dep)
            if any(alias.lower() in title_and_summary.lower() for alias in aliases):
                mentioned_deputies.append(dep)

        is_senate = len(mentioned_senators) > 0 or any(w in title_and_summary.lower() for w in ["senador", "senado", "cámara alta"])
        is_deputies = len(mentioned_deputies) > 0 or any(w in title_and_summary.lower() for w in ["diputado", "diputada", "cámara de diputados", "cámara baja"])
        
        if not is_senate and not is_deputies:
            is_senate = True
            is_deputies = True

        news_item = {
            "title": art["title"],
            "source": "Portal del Congreso",
            "date": art["raw_date"].split("|")[0].strip() if "|" in art["raw_date"] else art["raw_date"],
            "url": art["url"]
        }

        if is_senate:
            senado_news.append(news_item)
        if is_deputies:
            diputados_news.append(news_item)

        for leg_name in set(mentioned_senators + mentioned_deputies):
            if leg_name not in events_override:
                events_override[leg_name] = []
            
            already_added = any(ev.get("url") == art["url"] for ev in events_override[leg_name])
            if not already_added:
                events_override[leg_name].append({
                    "t": "📰",
                    "a": f"Mención en noticia oficial: {art['title']}",
                    "d": art["date"],
                    "tipo": "Noticia Oficial",
                    "url": art["url"],
                    "pts": 2
                })
                print(f"Added scoring event (+2 Pts) for: {leg_name}")

    # 4. Fetch official bills from SPLEY API
    fetch_spley_bills(events_override, all_senators + all_deputies)

    # 5. Save updated data
    data["senado_news"] = senado_news[:10]
    data["diputados_news"] = diputados_news[:10]
    data["events_override"] = events_override

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("Successfully updated data.json with crawled news, SPLEY bills, and scoring events.")

if __name__ == "__main__":
    main()
