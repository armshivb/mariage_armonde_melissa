import os
import csv
import io
import secrets
import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from datetime import datetime, timezone
from fastapi import FastAPI, Request, Form, Depends, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from database import get_db, init_db
from models import Guest, Setting

BASE_DIR = Path(__file__).parent

# ── Configuration ───────────────────────────────────────────────────────────────
# ── SMTP (Gmail) ───────────────────────────────────────────────────────────────
SMTP_HOST     = os.environ.get("SMTP_HOST",     "smtp.gmail.com")
SMTP_PORT     = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER     = os.environ.get("SMTP_USER",     "")   # votre adresse Gmail
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")   # mot de passe d'application Gmail
SMTP_FROM     = os.environ.get("SMTP_FROM",     SMTP_USER)

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD",  "mariage2027")
COUPLE_NAMES   = os.environ.get("COUPLE_NAMES",    "Melissa & Armonde")
WEDDING_DATE   = os.environ.get("WEDDING_DATE",    "Samedi 6 Février 2027")
WEDDING_PLACE  = os.environ.get("WEDDING_PLACE",   "Le Carbet, Martinique")
WEDDING_HOUR   = os.environ.get("WEDDING_HOUR",    "14h30")
FLIGHT_NUM     = os.environ.get("FLIGHT_NUM",      "VOL MA-060227")
GATE           = os.environ.get("GATE",            "G3")
DESTINATION    = os.environ.get("DESTINATION",     "LE CARBET")

app = FastAPI()
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def send_confirmation_email(guest, seat: str):
    """Envoie un email de confirmation à l'invité (dans un thread pour ne pas bloquer)."""
    if not SMTP_USER or not SMTP_PASSWORD or not guest.email:
        return

    def _send():
        try:
            if guest.response == "yes":
                subject = f"✈ Embarquement confirmé — Mariage {COUPLE_NAMES}"
                body_html = f"""
<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"/>
<style>
  body {{ font-family: Georgia, serif; background: #FBF5EC; margin: 0; padding: 0; }}
  .wrap {{ max-width: 600px; margin: 0 auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,.1); }}
  .header {{ background: #2C1208; padding: 2.5rem 2rem; text-align: center; }}
  .header h1 {{ font-family: Georgia, serif; color: #C8953A; font-size: 1.6rem; margin: 0 0 .3rem; }}
  .header p {{ color: #D4B8A0; font-size: .85rem; letter-spacing: .1em; text-transform: uppercase; margin: 0; }}
  .bp {{ background: #FFFDF8; border: 1px solid #EDE0CC; border-radius: 8px; margin: 2rem; padding: 2rem; position: relative; }}
  .bp-stripe {{ height: 5px; background: linear-gradient(135deg,#B85233,#CC6E50,#8C3A20); border-radius: 4px 4px 0 0; margin: -2rem -2rem 1.5rem; }}
  .bp-flight {{ font-family: 'Courier New', monospace; font-size: .7rem; letter-spacing: .2em; color: #B85233; text-transform: uppercase; margin-bottom: .3rem; }}
  .bp-name {{ font-size: 1.8rem; font-weight: 700; color: #2C1208; margin-bottom: 1.2rem; }}
  .bp-route {{ display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem; }}
  .bp-iata {{ font-family: 'Courier New', monospace; font-size: 2rem; font-weight: 700; color: #2C1208; }}
  .bp-arrow {{ color: #B85233; font-size: 1.2rem; flex: 1; text-align: center; }}
  .bp-city {{ font-size: .65rem; color: #8B6450; letter-spacing: .1em; text-transform: uppercase; margin-top: .2rem; }}
  .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem 1.5rem; margin-bottom: 1.5rem; }}
  .info-label {{ font-family: 'Courier New', monospace; font-size: .6rem; letter-spacing: .15em; text-transform: uppercase; color: #8B6450; margin-bottom: .25rem; }}
  .info-value {{ font-family: 'Courier New', monospace; font-size: .9rem; color: #2C1208; font-weight: 700; }}
  .seat-block {{ text-align: center; background: #2C1208; border-radius: 8px; padding: 1rem; margin-bottom: 1.5rem; }}
  .seat-num {{ font-family: 'Courier New', monospace; font-size: 2.5rem; color: #E8A090; font-weight: 700; }}
  .seat-label {{ font-family: 'Courier New', monospace; font-size: .6rem; color: #C8953A; letter-spacing: .15em; text-transform: uppercase; }}
  .stamp {{ border: 3px solid #2A8C4A; color: #2A8C4A; border-radius: 4px; display: inline-block; padding: .4rem 1rem; font-family: 'Courier New', monospace; font-size: .85rem; letter-spacing: .15em; text-transform: uppercase; transform: rotate(-8deg); margin: .5rem 0 1.5rem; }}
  .footer {{ text-align: center; padding: 2rem; color: #8B6450; font-size: .82rem; line-height: 1.8; }}
  .footer strong {{ color: #B85233; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <h1>Mariage {COUPLE_NAMES}</h1>
    <p>{FLIGHT_NUM} · {WEDDING_DATE}</p>
  </div>
  <div style="padding: 1.5rem 2rem 0; text-align:center">
    <p style="font-size:1rem;color:#2C1208">Bonjour <strong>{guest.prenom}</strong>,</p>
    <p style="color:#8B6450;font-size:.9rem;line-height:1.7">
      Votre embarquement est confirmé ! Nous avons hâte de vous accueillir pour ce grand jour.
    </p>
  </div>
  <div class="bp">
    <div class="bp-stripe"></div>
    <div class="bp-flight">{FLIGHT_NUM}</div>
    <div class="bp-name">{guest.prenom.upper()} {guest.nom.upper()}</div>
    <div class="bp-route">
      <div><div class="bp-iata">PAR</div><div class="bp-city">Paris</div></div>
      <div class="bp-arrow">✈</div>
      <div><div class="bp-iata">CAR</div><div class="bp-city">{DESTINATION}</div></div>
    </div>
    <div class="info-grid">
      <div><div class="info-label">Date</div><div class="info-value">{WEDDING_DATE}</div></div>
      <div><div class="info-label">Heure</div><div class="info-value">{WEDDING_HOUR}</div></div>
      <div style="grid-column:1/-1"><div class="info-label">Lieu</div><div class="info-value">Habitation Beau Pays</div><div style="font-size:.75rem;color:#8B6450;margin-top:.2rem">60 boulevard du bord de mer, Petite Anse<br>Le Carbet 97221, Martinique</div><div style="margin-top:.4rem"><a href="https://www.google.com/maps/dir/?api=1&destination=Habitation+Beau+Pays,+60+boulevard+du+bord+de+mer,+Le+Carbet+97221+Martinique" style="color:#B85233;text-decoration:none;font-family:'Courier New',monospace;font-size:.7rem;letter-spacing:.06em">📍 Itinéraire Google Maps →</a></div></div>
      {'<div><div class="info-label">Accompagnants</div><div class="info-value">+' + str(guest.plus_one) + '</div></div>' if guest.plus_one > 0 else ''}
      {'<div><div class="info-label">Régime</div><div class="info-value">' + (guest.regime or '').upper() + '</div></div>' if guest.regime and guest.regime != 'standard' else ''}
    </div>
    <div class="seat-block">
      <div class="seat-label">Siège / Seat</div>
      <div class="seat-num">{seat}</div>
    </div>
    <div style="text-align:center"><span class="stamp">Embarquement Confirmé ✓</span></div>
  </div>
  <div class="footer">
    Avec tout notre amour,<br>
    <strong>{COUPLE_NAMES}</strong><br>
    <span style="font-size:.75rem">{WEDDING_DATE} · {WEDDING_PLACE}</span>
  </div>
</div>
</body>
</html>"""
            else:
                subject = f"Votre réponse — Mariage {COUPLE_NAMES}"
                body_html = f"""
<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8"/>
<style>
  body {{ font-family: Georgia, serif; background: #FBF5EC; margin:0; padding:0; }}
  .wrap {{ max-width:600px; margin:0 auto; background:#fff; border-radius:12px; overflow:hidden; box-shadow:0 4px 24px rgba(0,0,0,.1); }}
  .header {{ background:#2C1208; padding:2.5rem 2rem; text-align:center; }}
  .header h1 {{ color:#C8953A; font-size:1.5rem; margin:0 0 .3rem; }}
  .header p {{ color:#D4B8A0; font-size:.8rem; letter-spacing:.1em; text-transform:uppercase; margin:0; }}
  .body {{ padding:2rem; text-align:center; }}
  .footer {{ text-align:center; padding:1.5rem; color:#8B6450; font-size:.82rem; }}
</style></head>
<body><div class="wrap">
  <div class="header"><h1>Mariage {COUPLE_NAMES}</h1><p>{FLIGHT_NUM}</p></div>
  <div class="body">
    <p style="font-size:2rem">💌</p>
    <p style="font-size:1rem;color:#2C1208">Bonjour <strong>{guest.prenom}</strong>,</p>
    <p style="color:#8B6450;font-size:.9rem;line-height:1.7">
      Nous avons bien reçu votre réponse. Nous sommes tristes de ne pas pouvoir vous accueillir,
      mais nous pensons à vous avec beaucoup d'amour !
    </p>
  </div>
  <div class="footer">Avec tout notre amour,<br><strong>{COUPLE_NAMES}</strong></div>
</div></body></html>"""

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"]    = f"Mariage {COUPLE_NAMES} <{SMTP_FROM}>"
            msg["To"]      = guest.email
            msg.attach(MIMEText(body_html, "html", "utf-8"))

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.ehlo()
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_FROM, guest.email, msg.as_string())
        except Exception as e:
            print(f"[EMAIL] Erreur envoi à {guest.email}: {e}")

    threading.Thread(target=_send, daemon=True).start()


def get_seat(code: str) -> str:
    """Génère un numéro de siège déterministe depuis le code invité."""
    val = int(code, 16)
    row = val % 30 + 1
    col = ['A', 'B', 'C', 'D', 'E', 'F'][val % 6]
    return f"{row}{col}"


def generate_unique_code(db: Session) -> str:
    """Génère un code unique et non utilisé."""
    code = secrets.token_hex(3).upper()
    while db.query(Guest).filter(Guest.code == code).first():
        code = secrets.token_hex(3).upper()
    return code


@app.on_event("startup")
def startup():
    init_db()
    # Migration : ajouter la colonne email si elle n'existe pas encore
    from sqlalchemy import text
    from database import engine
    with engine.connect() as conn:
        cols = [r[1] for r in conn.execute(text("PRAGMA table_info(guests)")).fetchall()]
        if "email" not in cols:
            conn.execute(text("ALTER TABLE guests ADD COLUMN email TEXT DEFAULT ''"))
            conn.commit()


def common(request: Request, **kwargs):
    return {
        "request":     request,
        "couple":      COUPLE_NAMES,
        "date":        WEDDING_DATE,
        "place":       WEDDING_PLACE,
        "hour":        WEDDING_HOUR,
        "flight_num":  FLIGHT_NUM,
        "gate":        GATE,
        "destination": DESTINATION,
        **kwargs,
    }


def tr(name: str, request: Request, **kwargs):
    return templates.TemplateResponse(request=request, name=name, context=common(request, **kwargs))


# ── Page d'accueil / FIDS ──────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return tr("index.html", request)


@app.post("/", response_class=HTMLResponse)
def index_post(request: Request, recherche: str = Form(...), db: Session = Depends(get_db)):
    q = recherche.strip()
    guest = db.query(Guest).filter(Guest.telephone == q).first()
    if not guest:
        parts = q.split()
        if len(parts) >= 2:
            prenom, nom = parts[0], " ".join(parts[1:])
            guest = db.query(Guest).filter(
                Guest.prenom.ilike(prenom), Guest.nom.ilike(nom)
            ).first()
            if not guest:
                guest = db.query(Guest).filter(
                    Guest.nom.ilike(parts[0]), Guest.prenom.ilike(" ".join(parts[1:]))
                ).first()
    
    # Si l'invité n'existe pas, le créer automatiquement
    if not guest:
        parts = q.split()
        if len(parts) >= 1:
            prenom = parts[0].strip()
            nom = " ".join(parts[1:]).strip() if len(parts) > 1 else ""
            
            if prenom and nom:
                # Créer automatiquement
                code = generate_unique_code(db)
                guest = Guest(
                    prenom=prenom,
                    nom=nom,
                    code=code,
                    created_at=datetime.utcnow()
                )
                db.add(guest)
                db.commit()
            else:
                return tr("index.html", request,
                          error="Veuillez entrer un prénom ET un nom de famille.")
        else:
            return tr("index.html", request,
                      error="Veuillez entrer un prénom ET un nom de famille.")
    
    return RedirectResponse(f"/rsvp/{guest.code}", status_code=302)


# ── Page RSVP / Boarding pass ──────────────────────────────────────────────────
@app.get("/rsvp/{code}", response_class=HTMLResponse)
def rsvp_get(code: str, request: Request, db: Session = Depends(get_db)):
    guest = db.query(Guest).filter(Guest.code == code.upper()).first()
    if not guest:
        return RedirectResponse("/")
    return tr("rsvp.html", request, guest=guest, seat=get_seat(guest.code))


@app.post("/rsvp/{code}", response_class=HTMLResponse)
def rsvp_post(
    code: str, request: Request,
    response: str = Form(...),
    plus_one: int  = Form(0),
    regime:   str  = Form("standard"),
    message:  str  = Form(""),
    email:    str  = Form(""),
    db: Session = Depends(get_db),
):
    guest = db.query(Guest).filter(Guest.code == code.upper()).first()
    if not guest:
        return RedirectResponse("/")
    guest.response   = response
    guest.plus_one   = max(0, plus_one)
    guest.regime     = regime
    guest.message    = message.strip()
    guest.email      = email.strip()
    guest.updated_at = datetime.utcnow()
    db.commit()
    seat = get_seat(guest.code)
    send_confirmation_email(guest, seat)
    return tr("merci.html", request, guest=guest, seat=seat)


# ── Admin login ────────────────────────────────────────────────────────────────
@app.get("/admin", response_class=HTMLResponse)
def admin_login(request: Request):
    return tr("admin_login.html", request)


@app.post("/admin", response_class=HTMLResponse)
def admin_login_post(request: Request, password: str = Form(...)):
    if password != ADMIN_PASSWORD:
        return tr("admin_login.html", request, error="Code d'accès incorrect.")
    return RedirectResponse("/admin/dashboard", status_code=302)


# ── Admin dashboard ────────────────────────────────────────────────────────────
def get_setting(db: Session, key: str, default: str = "") -> str:
    s = db.query(Setting).filter(Setting.key == key).first()
    return s.value if s else default


def set_setting(db: Session, key: str, value: str):
    s = db.query(Setting).filter(Setting.key == key).first()
    if s:
        s.value = value
    else:
        db.add(Setting(key=key, value=value))
    db.commit()


@app.get("/admin/dashboard", response_class=HTMLResponse)
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    guests    = db.query(Guest).order_by(Guest.nom, Guest.prenom).all()
    yes_count = sum(1 + g.plus_one for g in guests if g.response == "yes")
    no_count  = sum(1 for g in guests if g.response == "no")
    pending   = sum(1 for g in guests if g.response == "pending")
    repondu   = sum(1 for g in guests if g.response != "pending")

    expected_str  = get_setting(db, "expected_guests", "0")
    expected      = int(expected_str) if expected_str.isdigit() else 0
    taux_reponse  = round(repondu   / expected * 100) if expected > 0 else None
    taux_presence = round(yes_count / expected * 100) if expected > 0 else None

    return tr("admin.html", request,
              guests=guests, yes_count=yes_count, no_count=no_count,
              pending=pending, repondu=repondu, expected=expected,
              taux_reponse=taux_reponse, taux_presence=taux_presence)


@app.post("/admin/set-expected")
def set_expected(expected: int = Form(...), db: Session = Depends(get_db)):
    set_setting(db, "expected_guests", str(max(0, expected)))
    return RedirectResponse("/admin/dashboard", status_code=302)


# ── Admin : ajouter un invité ──────────────────────────────────────────────────
@app.post("/admin/add-guest")
def add_guest(
    prenom: str = Form(...), nom: str = Form(...),
    telephone: str = Form(""), db: Session = Depends(get_db)
):
    code = generate_unique_code(db)
    db.add(Guest(prenom=prenom.strip(), nom=nom.strip(),
                 telephone=telephone.strip(), code=code))
    db.commit()
    return RedirectResponse("/admin/dashboard", status_code=302)


# ── Admin : import CSV ─────────────────────────────────────────────────────────
@app.post("/admin/import-csv")
async def import_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    text    = content.decode("utf-8-sig")
    reader  = csv.reader(io.StringIO(text))
    added   = 0
    for row in reader:
        if not row or row[0].strip().lower() in ("prénom", "prenom", "firstname"):
            continue
        prenom = row[0].strip() if len(row) > 0 else ""
        nom    = row[1].strip() if len(row) > 1 else ""
        tel    = row[2].strip() if len(row) > 2 else ""
        if not prenom and not nom:
            continue
        code = generate_unique_code(db)
        db.add(Guest(prenom=prenom, nom=nom, telephone=tel, code=code))
        added += 1
    db.commit()
    return RedirectResponse(f"/admin/dashboard?imported={added}", status_code=302)


# ── Admin : export CSV ─────────────────────────────────────────────────────────
@app.get("/admin/export-csv")
def export_csv(db: Session = Depends(get_db)):
    guests = db.query(Guest).order_by(Guest.nom, Guest.prenom).all()
    output = io.StringIO()
    w = csv.writer(output)
    w.writerow(["Prénom", "Nom", "Téléphone", "Code", "Réponse", "Accompagnants", "Régime", "Message", "Date réponse"])
    for g in guests:
        w.writerow([
            g.prenom, g.nom, g.telephone or "", g.code,
            {"yes": "Confirmé", "no": "Décliné", "pending": "En attente"}.get(g.response, ""),
            g.plus_one if g.response == "yes" else "",
            g.regime or "",
            g.message or "",
            g.updated_at.strftime("%d/%m/%Y %H:%M") if g.updated_at else "",
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": "attachment; filename=invites-mariage.csv"}
    )


# ── ICS calendrier ────────────────────────────────────────────────────────────
@app.get("/ics/{code}")
def download_ics(code: str, db: Session = Depends(get_db)):
    guest = db.query(Guest).filter(Guest.code == code.upper()).first()
    if not guest or guest.response != "yes":
        return RedirectResponse("/")
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Mariage {COUPLE_NAMES}//FR
BEGIN:VEVENT
UID:{guest.code}-mariage@ma2027
DTSTAMP:{now}
DTSTART:20270206T140000Z
DTEND:20270207T020000Z
SUMMARY:Mariage {COUPLE_NAMES}
DESCRIPTION:Vol {FLIGHT_NUM} · Porte {GATE} · {WEDDING_PLACE}
LOCATION:{WEDDING_PLACE}
END:VEVENT
END:VCALENDAR"""
    return StreamingResponse(
        iter([ics]),
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=mariage-{COUPLE_NAMES.replace(' ', '-')}.ics"}
    )


# ── Admin : supprimer un invité ────────────────────────────────────────────────
@app.post("/admin/delete-guest/{guest_id}")
def delete_guest(guest_id: int, db: Session = Depends(get_db)):
    guest = db.query(Guest).filter(Guest.id == guest_id).first()
    if guest:
        db.delete(guest)
        db.commit()
    return RedirectResponse("/admin/dashboard", status_code=302)
