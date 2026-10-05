import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

def build_chamber_rows(members, parties):
    rows = ""
    for i, m in enumerate(members, 1):
        pty = m['party']
        pty_color = parties.get(pty, {}).get('c', '#8a1526')
        avatar_html = f"<img src='{m['photo']}' width='34' height='34' style='border-radius:50%;object-fit:cover;vertical-align:middle;margin-right:8px;border:1px solid #ddd;'>" if m.get('photo') else ""
        
        rows += f"""
        <tr style="border-bottom: 1px solid #f0eee8;">
            <td style="padding: 9px 6px; font-weight: 800; font-size: 13px; color: #333; text-align: center; width: 28px;">
                {i}°
            </td>
            <td style="padding: 9px 8px; font-size: 13.5px; color: #1a1a1a;">
                {avatar_html}
                <strong style="vertical-align: middle;">{m['name']}</strong>
                <div style="font-size: 11px; color: #777; margin-top: 1px;">
                    <span style="color:{pty_color};font-weight:700;">● {pty}</span> &bull; {m.get('district', 'Nacional')}
                </div>
            </td>
            <td style="padding: 9px 8px; font-weight: 800; font-size: 14px; color: #8a1526; text-align: right;">
                {m['pts']} <span style="font-size: 10px; color: #888; font-weight: 500;">pts</span>
            </td>
            <td style="padding: 9px 8px; font-size: 11.5px; color: #666; text-align: right;">
                {m['count']} act.
            </td>
        </tr>
        """
    return rows

def build_podium_html(top3, parties, chamber_name, main_color):
    html = ""
    medals = ["🥇 1° Puesto", "🥈 2° Puesto", "🥉 3° Puesto"]
    medals_border = ["#eab308", "#94a3b8", "#b45309"]
    for i, m in enumerate(top3):
        pty = m['party']
        pty_color = parties.get(pty, {}).get('c', '#8a1526')
        avatar_img = m.get('photo') if m.get('photo') else f"https://api.dicebear.com/7.x/initials/svg?seed={m['name'][:2]}&backgroundColor={main_color.replace('#','')}&textColor=ffffff&radius=50"
        
        html += f"""
        <div style="flex: 1; min-width: 155px; background: #ffffff; border: 2px solid {medals_border[i]}; border-radius: 8px; padding: 12px 8px; text-align: center; margin: 4px;">
            <div style="font-size: 10.5px; font-weight: 800; text-transform: uppercase; color: {medals_border[i]}; margin-bottom: 5px;">
                {medals[i]}
            </div>
            <img src="{avatar_img}" width="54" height="54" style="border-radius: 50%; object-fit: cover; border: 2px solid {medals_border[i]}; margin-bottom: 6px;">
            <div style="font-size: 12px; font-weight: 800; color: #1a1a1a; line-height: 1.2; margin-bottom: 3px;">
                {m['name']}
            </div>
            <div style="font-size: 10.5px; color: {pty_color}; font-weight: 700; margin-bottom: 5px;">
                {pty} &bull; {chamber_name}
            </div>
            <div style="background: #faf7ee; border-radius: 5px; padding: 3px 6px; font-size: 14px; font-weight: 800; color: {main_color};">
                {m['pts']} <span style="font-size: 9.5px; font-weight: 600; color: #777;">PTS</span>
            </div>
        </div>
        """
    return html

def generate_newsletter_html(data):
    events = data.get('events_override', {})
    info_map = data.get('INFO_MAP', {})
    photo_map = data.get('PHOTO_MAP', {})
    parties = data.get('P', {})
    
    snms_set = {name: party for party, names in data.get('SNMS', {}).items() for name in names}
    dnms_set = {name: party for party, names in data.get('DNMS', {}).items() for name in names}
    
    # Process Senators
    senators = []
    for name, party in snms_set.items():
        evts = events.get(name, [])
        pts = sum(e.get('pts', 0) for e in evts)
        info = info_map.get(name, {})
        senators.append({
            'name': name,
            'pts': pts,
            'count': len(evts),
            'party': party,
            'district': info.get('district', 'Nacional'),
            'photo': photo_map.get(name, '')
        })
    senators.sort(key=lambda x: (x['pts'], x['count']), reverse=True)
    
    # Process Deputies
    deputies = []
    for name, party in dnms_set.items():
        evts = events.get(name, [])
        pts = sum(e.get('pts', 0) for e in evts)
        info = info_map.get(name, {})
        deputies.append({
            'name': name,
            'pts': pts,
            'count': len(evts),
            'party': party,
            'district': info.get('district', 'Nacional'),
            'photo': photo_map.get(name, '')
        })
    deputies.sort(key=lambda x: (x['pts'], x['count']), reverse=True)
    
    total_activities = sum(len(v) for v in events.values())
    senators_active = sum(1 for s in senators if s['count'] > 0)
    deputies_active = sum(1 for d in deputies if d['count'] > 0)
    
    today_str = datetime.now().strftime("%d de %B, %Y").replace(
        "January", "enero").replace("February", "febrero").replace("March", "marzo").replace(
        "April", "abril").replace("May", "mayo").replace("June", "junio").replace(
        "July", "julio").replace("August", "agosto").replace("September", "septiembre").replace(
        "October", "octubre").replace("November", "noviembre").replace("December", "diciembre")

    # Podium and Tables for each chamber
    sen_podium = build_podium_html(senators[:3], parties, "Senador", "#8a1526")
    sen_rows = build_chamber_rows(senators[:8], parties)
    
    dip_podium = build_podium_html(deputies[:3], parties, "Diputado", "#1a2b49")
    dip_rows = build_chamber_rows(deputies[:8], parties)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Newsletter Congreso Perú - Chambómetro Bicameral</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f6f5f1; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased;">

<center>
<table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 640px; background-color: #ffffff; margin: 20px auto; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 18px rgba(0,0,0,0.06); border: 1px solid #e2ded5;">
    
    <!-- Enlace superior -->
    <tr>
        <td style="padding: 10px 20px; font-size: 11px; color: #888; text-align: right; background: #faf9f5; border-bottom: 1px solid #ebe8e0;">
            <a href="https://congreso-peru.vercel.app" style="color: #777; text-decoration: underline;" target="_blank">Ver en mi navegador</a>
        </td>
    </tr>

    <!-- HEADER ESTILO EL COMERCIO -->
    <tr>
        <td style="background: linear-gradient(135deg, #ffd000 0%, #f7b700 100%); padding: 22px 24px;">
            <table border="0" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                    <td style="vertical-align: middle;">
                        <div style="font-family: Georgia, 'Times New Roman', serif; font-size: 26px; font-weight: 900; color: #111111; letter-spacing: -0.5px; line-height: 1;">
                            El Comercio
                        </div>
                        <div style="font-family: Georgia, 'Times New Roman', serif; font-size: 19px; font-style: italic; font-weight: bold; color: #222222; margin-top: 4px;">
                            El Chambómetro Legislativo
                        </div>
                        <div style="font-size: 11px; font-weight: 700; color: #444; text-transform: uppercase; letter-spacing: 0.8px; margin-top: 6px;">
                            Edición Bicameral &bull; {today_str}
                        </div>
                    </td>
                    <td style="text-align: right; vertical-align: middle;" width="60">
                        <span style="font-size: 38px;">🇵🇪</span>
                    </td>
                </tr>
            </table>
        </td>
    </tr>

    <!-- EDITORIAL INTRO -->
    <tr>
        <td style="padding: 22px 24px 10px 24px; background-color: #ffffff;">
            <h1 style="font-family: Georgia, 'Times New Roman', serif; font-size: 21px; font-weight: 800; color: #111111; line-height: 1.3; margin: 0 0 12px 0;">
                El ranking del Congreso: ¿Quiénes lideran el Senado y la Cámara de Diputados?
            </h1>
            
            <p style="font-size: 14px; line-height: 1.6; color: #333333; margin: 0 0 14px 0;">
                El periodo 2026-2031 ya cuenta con <strong>{total_activities} actividades oficiales procesadas</strong> en la plataforma. A continuación, el reporte exclusivo discriminado por cada una de las dos cámaras del Parlamento.
            </p>

            <!-- METRICAS COMPARATIVAS -->
            <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background: #faf8f2; border: 1px solid #eae5d7; border-radius: 8px; margin-bottom: 22px;">
                <tr>
                    <td style="padding: 12px 8px; text-align: center; border-right: 1px solid #eae5d7; width: 33%;">
                        <div style="font-size: 19px; font-weight: 800; color: #8a1526;">{senators_active}/60</div>
                        <div style="font-size: 10px; font-weight: 700; color: #666; text-transform: uppercase;">Senadores Activos</div>
                    </td>
                    <td style="padding: 12px 8px; text-align: center; border-right: 1px solid #eae5d7; width: 33%;">
                        <div style="font-size: 19px; font-weight: 800; color: #1a2b49;">{deputies_active}/130</div>
                        <div style="font-size: 10px; font-weight: 700; color: #666; text-transform: uppercase;">Diputados Activos</div>
                    </td>
                    <td style="padding: 12px 8px; text-align: center; width: 33%;">
                        <div style="font-size: 19px; font-weight: 800; color: #c5a059;">{total_activities}</div>
                        <div style="font-size: 10px; font-weight: 700; color: #666; text-transform: uppercase;">Total Actividades</div>
                    </td>
                </tr>
            </table>

            <!-- ============================================== -->
            <!-- BLOQUE 1: CÁMARA DE SENADORES (ROJO / WINE)    -->
            <!-- ============================================== -->
            <div style="background: #fdf5f6; border-left: 5px solid #8a1526; border-radius: 6px; padding: 10px 14px; margin-bottom: 12px;">
                <table border="0" cellpadding="0" cellspacing="0" width="100%">
                    <tr>
                        <td>
                            <div style="font-size: 10.5px; font-weight: 800; color: #8a1526; text-transform: uppercase; letter-spacing: 0.6px;">
                                ALFOMBRA ROJA &bull; 60 ESCAÑOS
                            </div>
                            <div style="font-family: Georgia, 'Times New Roman', serif; font-size: 18px; font-weight: 800; color: #660f1c; margin-top: 2px;">
                                🎖️ Cámara de Senadores: Los más productivos
                            </div>
                        </td>
                    </tr>
                </table>
            </div>

            <!-- PODIO SENADO -->
            <div style="display: flex; flex-wrap: wrap; margin-bottom: 16px; justify-content: space-between;">
                {sen_podium}
            </div>

            <!-- TABLA SENADO -->
            <table border="0" cellpadding="0" cellspacing="0" width="100%" style="border-collapse: collapse; margin-bottom: 26px; border: 1px solid #eedcde; border-radius: 6px; overflow: hidden;">
                <thead>
                    <tr style="background: #8a1526; font-size: 11px; text-transform: uppercase; color: #ffffff;">
                        <th style="padding: 7px; text-align: center;">#</th>
                        <th style="padding: 7px; text-align: left;">Senador / Bancada</th>
                        <th style="padding: 7px; text-align: right;">Puntos</th>
                        <th style="padding: 7px; text-align: right;">Act.</th>
                    </tr>
                </thead>
                <tbody style="background: #fff;">
                    {sen_rows}
                </tbody>
            </table>

            <!-- ============================================== -->
            <!-- BLOQUE 2: CÁMARA DE DIPUTADOS (AZUL / ROYAL)   -->
            <!-- ============================================== -->
            <div style="background: #f4f7fc; border-left: 5px solid #1a2b49; border-radius: 6px; padding: 10px 14px; margin-bottom: 12px;">
                <table border="0" cellpadding="0" cellspacing="0" width="100%">
                    <tr>
                        <td>
                            <div style="font-size: 10.5px; font-weight: 800; color: #1a2b49; text-transform: uppercase; letter-spacing: 0.6px;">
                                ALFOMBRA AZUL &bull; 130 ESCAÑOS
                            </div>
                            <div style="font-family: Georgia, 'Times New Roman', serif; font-size: 18px; font-weight: 800; color: #121e33; margin-top: 2px;">
                                🏛️ Cámara de Diputados: Los más productivos
                            </div>
                        </td>
                    </tr>
                </table>
            </div>

            <!-- PODIO DIPUTADOS -->
            <div style="display: flex; flex-wrap: wrap; margin-bottom: 16px; justify-content: space-between;">
                {dip_podium}
            </div>

            <!-- TABLA DIPUTADOS -->
            <table border="0" cellpadding="0" cellspacing="0" width="100%" style="border-collapse: collapse; margin-bottom: 26px; border: 1px solid #dbe4f0; border-radius: 6px; overflow: hidden;">
                <thead>
                    <tr style="background: #1a2b49; font-size: 11px; text-transform: uppercase; color: #ffffff;">
                        <th style="padding: 7px; text-align: center;">#</th>
                        <th style="padding: 7px; text-align: left;">Diputado / Bancada</th>
                        <th style="padding: 7px; text-align: right;">Puntos</th>
                        <th style="padding: 7px; text-align: right;">Act.</th>
                    </tr>
                </thead>
                <tbody style="background: #fff;">
                    {dip_rows}
                </tbody>
            </table>

            <!-- SECCION LEY MEDIATICA (DEBATE NACIONAL) -->
            <div style="background: #fffdf7; border: 1.5px solid #fed7aa; border-left: 5px solid #ea580c; border-radius: 8px; padding: 14px 16px; margin-bottom: 24px;">
                <div style="font-size: 10.5px; font-weight: 800; color: #ea580c; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">
                    ⚖️ Ley Mediática del Momento &bull; Debate Nacional
                </div>
                <h3 style="font-family: Georgia, 'Times New Roman', serif; font-size: 16px; font-weight: 800; color: #111; margin: 0 0 8px 0;">
                    ¿Adiós al tope de tasas de interés de los bancos?
                </h3>
                <p style="font-size: 13px; color: #444; line-height: 1.5; margin: 0 0 10px 0;">
                    El pedido de facultades legislativas plantea derogar la <strong>Ley Antiusura (N° 31143)</strong> para que la banca fije tasas libres.
                </p>
                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="font-size: 12px;">
                    <tr>
                        <td style="width: 50%; vertical-align: top; padding-right: 6px;">
                            <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; padding: 8px;">
                                <strong style="color: #166534;">🟢 Poder Ejecutivo (Keiko Fujimori):</strong><br>
                                <span style="color: #14532d; font-size: 11.5px;">Afirma que el tope expulsó a 540 mil clientes al crédito informal y a la extorsión del "gota a gota".</span>
                            </div>
                        </td>
                        <td style="width: 50%; vertical-align: top; padding-left: 6px;">
                            <div style="background: #fef2f2; border: 1px solid #fecaca; border-radius: 6px; padding: 8px;">
                                <strong style="color: #991b1b;">🔴 Consumidores (Jaime Delgado):</strong><br>
                                <span style="color: #7f1d1d; font-size: 11.5px;">Advierte que sin topes las tarjetas de crédito volverán a cobrar más de 150% o 200% anual de interés.</span>
                            </div>
                        </td>
                    </tr>
                </table>
            </div>

            <!-- BOTON CTA -->
            <div style="text-align: center; margin: 24px 0 14px 0;">
                <a href="https://congreso-peru.vercel.app" target="_blank" style="display: inline-block; background: #8a1526; color: #ffffff; text-decoration: none; padding: 13px 26px; border-radius: 6px; font-size: 14px; font-weight: 700; box-shadow: 0 3px 10px rgba(138,21,38,0.25);">
                    🏛️ Explorar los Hemiciclos y Votar en Vivo &rarr;
                </a>
            </div>

        </td>
    </tr>

    <!-- FOOTER -->
    <tr>
        <td style="background-color: #1a1a1a; color: #aaaaaa; padding: 18px 24px; font-size: 11px; line-height: 1.6; text-align: center;">
            <p style="margin: 0 0 6px 0; color: #dddddd; font-weight: 700;">
                Congreso de la República del Perú &bull; Monitor Interactivo Bicameral 2026-2031
            </p>
            <p style="margin: 0 0 8px 0;">
                Este boletín se envía automáticamente con la recopilación de datos oficiales de las plataformas de Comunicaciones, SPLEY y SMOCIONES del Congreso.
            </p>
            <p style="margin: 0; color: #777;">
                <a href="https://congreso-peru.vercel.app" style="color: #ffd000; text-decoration: none;">Ver Mapa Completo</a> &bull; 
                <a href="https://github.com/maextro545-creator/congreso-peru" style="color: #ffd000; text-decoration: none;">Repositorio de Datos</a>
            </p>
        </td>
    </tr>

</table>
</center>

</body>
</html>"""
    return html

def send_email(subject, html_content, to_emails, smtp_host, smtp_port, smtp_user, smtp_pass):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"El Chambómetro <{smtp_user}>"
    msg['To'] = ", ".join(to_emails) if isinstance(to_emails, list) else to_emails
    
    part = MIMEText(html_content, 'html', 'utf-8')
    msg.attach(part)
    
    print(f"Connecting to SMTP {smtp_host}:{smtp_port}...")
    server = smtplib.SMTP(smtp_host, int(smtp_port))
    server.starttls()
    server.login(smtp_user, smtp_pass)
    server.sendmail(smtp_user, to_emails if isinstance(to_emails, list) else [to_emails], msg.as_string())
    server.quit()
    print("Email sent successfully!")

if __name__ == '__main__':
    with open('data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    html = generate_newsletter_html(data)
    
    with open('newsletter_preview.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Newsletter preview updated: newsletter_preview.html")
    
    smtp_user = os.environ.get('SMTP_USER')
    smtp_pass = os.environ.get('SMTP_PASSWORD')
    smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = os.environ.get('SMTP_PORT', 587)
    to_emails = os.environ.get('NEWSLETTER_TO')
    
    if smtp_user and smtp_pass and to_emails:
        subject = f"📰 El Chambómetro: Ranking Senado y Diputados ({datetime.now().strftime('%d/%m/%Y')})"
        recipients = [e.strip() for e in to_emails.split(',') if e.strip()]
        send_email(subject, html, recipients, smtp_host, smtp_port, smtp_user, smtp_pass)
    else:
        print("Note: Set SMTP_USER, SMTP_PASSWORD, NEWSLETTER_TO to send actual emails.")
