import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

def generate_newsletter_html(data):
    events = data.get('events_override', {})
    info_map = data.get('INFO_MAP', {})
    photo_map = data.get('PHOTO_MAP', {})
    parties = data.get('P', {})
    
    # Calculate scores
    members_data = []
    for name, evts in events.items():
        pts = sum(e.get('pts', 0) for e in evts)
        info = info_map.get(name, {})
        photo = photo_map.get(name, '')
        members_data.append({
            'name': name,
            'pts': pts,
            'count': len(evts),
            'party': info.get('party', ''),
            'district': info.get('district', 'Nacional'),
            'type': info.get('type', 'd'),
            'photo': photo
        })
    
    members_data.sort(key=lambda x: (x['pts'], x['count']), reverse=True)
    
    top3 = members_data[:3]
    top10 = members_data[:10]
    total_activities = sum(len(v) for v in events.values())
    total_active_members = len(events)
    
    today_str = datetime.now().strftime("%d de %B, %Y").replace(
        "January", "enero").replace("February", "febrero").replace("March", "marzo").replace(
        "April", "abril").replace("May", "mayo").replace("June", "junio").replace(
        "July", "julio").replace("August", "agosto").replace("September", "septiembre").replace(
        "October", "octubre").replace("November", "noviembre").replace("December", "diciembre")

    # Generate Top 10 Table Rows
    top10_rows = ""
    for i, m in enumerate(top10, 1):
        pty = m['party']
        pty_color = parties.get(pty, {}).get('c', '#8a1526')
        chamber_badge = "Senado" if m['type'] == 's' else "Diputados"
        badge_bg = "#8a1526" if m['type'] == 's' else "#1a2b49"
        
        avatar_html = f"<img src='{m['photo']}' width='36' height='36' style='border-radius:50%;object-fit:cover;vertical-align:middle;margin-right:8px;border:1px solid #ddd;'>" if m['photo'] else ""
        
        top10_rows += f"""
        <tr style="border-bottom: 1px solid #f0eee8;">
            <td style="padding: 10px 8px; font-weight: 800; font-size: 14px; color: #2c2c28; text-align: center; width: 30px;">
                {i}°
            </td>
            <td style="padding: 10px 8px; font-size: 14px; color: #1a1a1a;">
                {avatar_html}
                <strong style="vertical-align: middle;">{m['name']}</strong>
                <div style="font-size: 11px; color: #777; margin-top: 2px;">
                    <span style="display:inline-block;padding:1px 6px;border-radius:3px;background:{badge_bg};color:#fff;font-size:10px;font-weight:700;">{chamber_badge}</span>
                    <span style="color:{pty_color};font-weight:700;margin-left:4px;">● {pty}</span> &bull; {m['district']}
                </div>
            </td>
            <td style="padding: 10px 8px; font-weight: 800; font-size: 15px; color: #8a1526; text-align: right;">
                {m['pts']} <span style="font-size: 10px; color: #888; font-weight: 500;">pts</span>
            </td>
            <td style="padding: 10px 8px; font-size: 12px; color: #666; text-align: right;">
                {m['count']} act.
            </td>
        </tr>
        """

    # Podium cards HTML
    podium_html = ""
    medals = ["🥇 1° Lugar", "🥈 2° Lugar", "🥉 3° Lugar"]
    border_colors = ["#eab308", "#94a3b8", "#b45309"]
    for i, m in enumerate(top3):
        pty = m['party']
        pty_color = parties.get(pty, {}).get('c', '#8a1526')
        chamber_badge = "Senador" if m['type'] == 's' else "Diputado"
        avatar_img = m['photo'] if m['photo'] else f"https://api.dicebear.com/7.x/initials/svg?seed={m['name'][:2]}&backgroundColor=8a1526&textColor=ffffff&radius=50"
        
        podium_html += f"""
        <div style="flex: 1; min-width: 170px; background: #ffffff; border: 2px solid {border_colors[i]}; border-radius: 10px; padding: 14px 10px; text-align: center; margin: 5px;">
            <div style="font-size: 11px; font-weight: 800; text-transform: uppercase; color: {border_colors[i]}; margin-bottom: 6px;">
                {medals[i]}
            </div>
            <img src="{avatar_img}" width="60" height="60" style="border-radius: 50%; object-fit: cover; border: 2px solid {border_colors[i]}; margin-bottom: 8px;">
            <div style="font-size: 13px; font-weight: 800; color: #1a1a1a; line-height: 1.2; margin-bottom: 4px;">
                {m['name']}
            </div>
            <div style="font-size: 11px; color: {pty_color}; font-weight: 700; margin-bottom: 6px;">
                {pty} &bull; {chamber_badge}
            </div>
            <div style="background: #fdf8e8; border-radius: 6px; padding: 4px 8px; font-size: 15px; font-weight: 800; color: #8a1526;">
                {m['pts']} <span style="font-size: 10px; font-weight: 600; color: #666;">PTS</span>
            </div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Newsletter Congreso Perú - El Chambómetro</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f6f5f1; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased;">

<center>
<table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 620px; background-color: #ffffff; margin: 20px auto; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 18px rgba(0,0,0,0.06); border: 1px solid #e2ded5;">
    
    <!-- Enlace superior -->
    <tr>
        <td style="padding: 10px 20px; font-size: 11px; color: #888; text-align: right; background: #faf9f5; border-bottom: 1px solid #ebe8e0;">
            <a href="https://congreso-peru.vercel.app" style="color: #777; text-decoration: underline;" target="_blank">Ver en mi navegador</a>
        </td>
    </tr>

    <!-- HEADER ESTILO EL COMERCIO -->
    <tr>
        <td style="background: linear-gradient(135deg, #ffd000 0%, #f7b700 100%); padding: 24px 24px 20px 24px;">
            <table border="0" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                    <td style="vertical-align: middle;">
                        <!-- Logo / Título El Comercio Style -->
                        <div style="font-family: Georgia, 'Times New Roman', serif; font-size: 26px; font-weight: 900; color: #111111; letter-spacing: -0.5px; line-height: 1;">
                            El Congreso
                        </div>
                        <div style="font-family: Georgia, 'Times New Roman', serif; font-size: 18px; font-style: italic; font-weight: bold; color: #333333; margin-top: 4px;">
                            El Chambómetro Diario
                        </div>
                        <div style="font-size: 11px; font-weight: 700; color: #444; text-transform: uppercase; letter-spacing: 0.8px; margin-top: 6px;">
                            Boletín Oficial de Actividad Parlamentaria &bull; {today_str}
                        </div>
                    </td>
                    <td style="text-align: right; vertical-align: middle;" width="70">
                        <span style="font-size: 40px;">🇵🇪</span>
                    </td>
                </tr>
            </table>
        </td>
    </tr>

    <!-- ARTICULO PRINCIPAL / EDITORIAL -->
    <tr>
        <td style="padding: 24px 24px 12px 24px; background-color: #ffffff;">
            <h1 style="font-family: Georgia, 'Times New Roman', serif; font-size: 22px; font-weight: 800; color: #111111; line-height: 1.3; margin: 0 0 14px 0;">
                ¿Quiénes están produciendo realmente en el Parlamento? Así se mueve el tablero legislativo
            </h1>
            
            <p style="font-size: 14.5px; line-height: 1.6; color: #333333; margin: 0 0 14px 0;">
                El periodo bicameral sigue su curso y el bot oficial de monitoreo legislativo ya superó las <strong>{total_activities} actividades registradas</strong> entre proyectos de ley, mociones parlamentarias e intervenciones en el Pleno.
            </p>
            <p style="font-size: 14.5px; line-height: 1.6; color: #333333; margin: 0 0 16px 0;">
                Hasta el momento, <strong>{total_active_members} de los 190 congresistas</strong> registran actividad oficial cuantificable. A continuación, el podio y los números más destacados de la jornada.
            </p>

            <!-- STATS RAPIDOS -->
            <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background: #faf8f2; border: 1px solid #eae5d7; border-radius: 8px; margin-bottom: 22px;">
                <tr>
                    <td style="padding: 12px; text-align: center; border-right: 1px solid #eae5d7; width: 33%;">
                        <div style="font-size: 20px; font-weight: 800; color: #8a1526;">{total_activities}</div>
                        <div style="font-size: 10px; font-weight: 700; color: #666; text-transform: uppercase;">Actividades</div>
                    </td>
                    <td style="padding: 12px; text-align: center; border-right: 1px solid #eae5d7; width: 33%;">
                        <div style="font-size: 20px; font-weight: 800; color: #1a2b49;">{total_active_members}/190</div>
                        <div style="font-size: 10px; font-weight: 700; color: #666; text-transform: uppercase;">Congresistas Activos</div>
                    </td>
                    <td style="padding: 12px; text-align: center; width: 33%;">
                        <div style="font-size: 20px; font-weight: 800; color: #c5a059;">6</div>
                        <div style="font-size: 10px; font-weight: 700; color: #666; text-transform: uppercase;">Leyes Oficiales</div>
                    </td>
                </tr>
            </table>

            <!-- PODIO DEL DÍA -->
            <div style="font-family: Georgia, 'Times New Roman', serif; font-size: 17px; font-weight: 800; color: #111111; margin-bottom: 10px; border-bottom: 2px solid #111; padding-bottom: 4px;">
                🏆 El Podio del Chambómetro (Top 3)
            </div>
            
            <div style="display: flex; flex-wrap: wrap; margin-bottom: 24px; justify-content: space-between;">
                {podium_html}
            </div>

            <!-- TABLA TOP 10 -->
            <div style="font-family: Georgia, 'Times New Roman', serif; font-size: 17px; font-weight: 800; color: #111111; margin-bottom: 10px; border-bottom: 2px solid #111; padding-bottom: 4px;">
                📊 Tabla de Posiciones: Los 10 con Mayor Puntaje
            </div>

            <table border="0" cellpadding="0" cellspacing="0" width="100%" style="border-collapse: collapse; margin-bottom: 24px;">
                <thead>
                    <tr style="background: #f5f4ef; font-size: 11px; text-transform: uppercase; color: #777;">
                        <th style="padding: 8px; text-align: center;">#</th>
                        <th style="padding: 8px; text-align: left;">Congresista / Bancada</th>
                        <th style="padding: 8px; text-align: right;">Puntos</th>
                        <th style="padding: 8px; text-align: right;">Act.</th>
                    </tr>
                </thead>
                <tbody>
                    {top10_rows}
                </tbody>
            </table>

            <!-- SECCION LEY MEDIATICA (DEBATE NACIONAL) -->
            <div style="background: #fffdf7; border: 1.5px solid #fed7aa; border-left: 5px solid #ea580c; border-radius: 8px; padding: 16px; margin-bottom: 24px;">
                <div style="font-size: 11px; font-weight: 800; color: #ea580c; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">
                    ⚖️ Ley Mediática del Momento &bull; Debate en Pleno
                </div>
                <h3 style="font-family: Georgia, 'Times New Roman', serif; font-size: 16px; font-weight: 800; color: #111; margin: 0 0 8px 0;">
                    ¿Adiós al tope de tasas de interés de los bancos?
                </h3>
                <p style="font-size: 13px; color: #444; line-height: 1.5; margin: 0 0 10px 0;">
                    El pedido de facultades legislativas plantea derogar la <strong>Ley Antiusura (N° 31143)</strong> para que la banca fije tasas libres.
                </p>
                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="font-size: 12px; margin-top: 8px;">
                    <tr>
                        <td style="width: 50%; vertical-align: top; padding-right: 6px;">
                            <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; padding: 8px;">
                                <strong style="color: #166534;">🟢 Poder Ejecutivo (Keiko Fujimori):</strong><br>
                                <span style="color: #14532d; font-size: 11.5px;">Argumenta que el tope expulsó a 540 mil clientes al crédito informal y al "gota a gota".</span>
                            </div>
                        </td>
                        <td style="width: 50%; vertical-align: top; padding-left: 6px;">
                            <div style="background: #fef2f2; border: 1px solid #fecaca; border-radius: 6px; padding: 8px;">
                                <strong style="color: #991b1b;">🔴 Consumidores (Jaime Delgado):</strong><br>
                                <span style="color: #7f1d1d; font-size: 11.5px;">Advierte que sin topes las tarjetas de crédito volverán a cobrar más de 150% anual de interés.</span>
                            </div>
                        </td>
                    </tr>
                </table>
            </div>

            <!-- BOTON CTA -->
            <div style="text-align: center; margin: 28px 0 14px 0;">
                <a href="https://congreso-peru.vercel.app" target="_blank" style="display: inline-block; background: #8a1526; color: #ffffff; text-decoration: none; padding: 13px 26px; border-radius: 6px; font-size: 14px; font-weight: 700; box-shadow: 0 3px 10px rgba(138,21,38,0.25);">
                    🏛️ Explorar el Hemiciclo y Votar en Vivo &rarr;
                </a>
            </div>

        </td>
    </tr>

    <!-- FOOTER -->
    <tr>
        <td style="background-color: #1a1a1a; color: #aaaaaa; padding: 20px 24px; font-size: 11px; line-height: 1.6; text-align: center;">
            <p style="margin: 0 0 6px 0; color: #dddddd; font-weight: 700;">
                Congreso de la República del Perú &bull; Monitor Interactivo 2026-2031
            </p>
            <p style="margin: 0 0 8px 0;">
                Este correo fue enviado de manera automática con la recopilación de datos oficiales del portal de Comunicaciones, SPLEY y SMOCIONES del Congreso del Perú.
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
    
    # Save a preview file
    with open('newsletter_preview.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Newsletter preview saved to: newsletter_preview.html")
    
    # Check if SMTP credentials are provided in env
    smtp_user = os.environ.get('SMTP_USER')
    smtp_pass = os.environ.get('SMTP_PASSWORD')
    smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = os.environ.get('SMTP_PORT', 587)
    to_emails = os.environ.get('NEWSLETTER_TO')
    
    if smtp_user and smtp_pass and to_emails:
        subject = f"📰 El Chambómetro: Ranking y Novedades del Congreso ({datetime.now().strftime('%d/%m/%Y')})"
        recipients = [e.strip() for e in to_emails.split(',') if e.strip()]
        send_email(subject, html, recipients, smtp_host, smtp_port, smtp_user, smtp_pass)
    else:
        print("Note: To send emails, set environment variables: SMTP_USER, SMTP_PASSWORD, NEWSLETTER_TO")
