import os, time, json, random
from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

def color_for_score(score):
    if score >= 80: return "success"
    if score >= 60: return "warning"
    return "danger"

def generate_leads(industry, city, n=8):
    random.seed(f"{industry}-{city}")
    leads = []
    for i in range(n):
        name = f"{industry.title()} {city.title()} #{i+1}"
        domain = f"www.{industry.lower().replace(' ', '')}{i+1}-{city.lower().replace(' ', '')}.de"
        web_age = random.randint(1, 12)
        reviews = random.randint(0, 250)
        social = random.choice(["low", "medium", "high"])
        speed = random.randint(40, 100)
        base = 40 + min(web_age*3, 20) + min(reviews/5, 20) + (10 if social=='high' else 5 if social=='medium' else 0) + (speed-40)/6
        score = int(max(10, min(100, base)))
        reason_bits = [
            f"Domain-Aktivität ~{web_age} Jahre",
            f"{reviews} Bewertungen gefunden",
            f"Soziale Präsenz: {social}",
            f"Performance-Index: {speed}/100"
        ]
        email = f"""Betreff: Schneller Quick Win für {name}

Hi {name.split()[0]},

ich habe mir kurz eure Online-Präsenz angesehen und sehe 2–3 schnelle Ansatzpunkte,
mit denen ihr messbar mehr Anfragen aus {city} holen könnt (ohne mehr Ad-Spend). 
Ich kann dir das in 10–15 Min zeigen – vollkommen unverbindlich.

Wenn’s passt, baue ich euch einen kleinen Automations-Workflow als Test (kostenlos). 
Wie klingt {random.choice(['morgen 10:00','morgen 15:00','übermorgen 11:30'])}?

Beste Grüße
William
"""
        leads.append({
            "name": name,
            "domain": domain,
            "score": score,
            "score_color": color_for_score(score),
            "reasons": reason_bits,
            "email": email
        })
    leads.sort(key=lambda x: -x["score"])
    return leads

def analyze_site(url):
    t0 = time.time()
    ok = True
    html = ""
    try:
        resp = requests.get(url if url.startswith("http") else "https://" + url, timeout=8, headers={"User-Agent":"Mozilla/5.0 (AITool/1.0)"})
        elapsed = resp.elapsed.total_seconds() if hasattr(resp, "elapsed") else (time.time()-t0)
        size_kb = round(len(resp.content)/1024, 1)
        html = resp.text
    except Exception as e:
        ok = False
        elapsed = time.time()-t0
        size_kb = 0
    
    soup = BeautifulSoup(html, "html.parser") if ok else BeautifulSoup("", "html.parser")
    title = (soup.title.string.strip() if soup.title and soup.title.string else "")
    meta_desc_tag = soup.find("meta", attrs={"name":"description"}) or soup.find("meta", attrs={"property":"og:description"})
    meta_desc = (meta_desc_tag.get("content","").strip() if meta_desc_tag else "")
    h1s = [h.get_text(strip=True) for h in soup.find_all("h1")]
    imgs = soup.find_all("img")
    imgs_total = len(imgs)
    imgs_with_alt = sum(1 for i in imgs if i.get("alt"))
    alt_ratio = round((imgs_with_alt/imgs_total*100),1) if imgs_total>0 else 100.0

    seo_score = 0
    if title: seo_score += 25
    if 35 <= len(title) <= 65: seo_score += 15
    if meta_desc: seo_score += 25
    if 80 <= len(meta_desc) <= 160: seo_score += 15
    if len(h1s)==1: seo_score += 20
    seo_score = min(100, seo_score)

    perf_score = 0
    if elapsed < 1.0: perf_score += 40
    elif elapsed < 2.0: perf_score += 25
    else: perf_score += 10
    if size_kb < 1500: perf_score += 40
    elif size_kb < 3500: perf_score += 25
    else: perf_score += 10
    if alt_ratio >= 80: perf_score += 20
    perf_score = min(100, perf_score)

    overall = int(0.5*seo_score + 0.4*perf_score + 0.1*alt_ratio)
    suggestions = []
    if not title: suggestions.append("Fehlender <title>-Tag – dringend ergänzen (SEO-Basic).")
    if title and (len(title) < 35 or len(title) > 65): suggestions.append("Title-Länge optimieren (35–65 Zeichen).")
    if not meta_desc: suggestions.append("Meta-Description fehlt – für höhere CTR ergänzen (80–160 Zeichen).")
    if meta_desc and (len(meta_desc) < 80 or len(meta_desc) > 160): suggestions.append("Meta-Description auf 80–160 Zeichen trimmen.")
    if len(h1s) != 1: suggestions.append(f"Genau eine H1 verwenden – aktuell {len(h1s)} gefunden.")
    if elapsed >= 1.0: suggestions.append(f"Antwortzeit reduzieren – aktuell {elapsed:.2f}s (Ziel <1.0s).")
    if size_kb >= 1500: suggestions.append(f"Seitengewicht optimieren – aktuell {size_kb}KB (Bilder/JS/CSS minifizieren).")
    if alt_ratio < 80: suggestions.append(f"Bild-Alt-Texte ergänzen – nur {alt_ratio}% mit Alt.")

    return {
        "ok": ok,
        "url": url,
        "metrics": {
            "response_time_s": round(elapsed,2),
            "html_size_kb": size_kb,
            "images_total": imgs_total,
            "images_alt_pct": alt_ratio
        },
        "seo": {
            "title": title,
            "meta_description": meta_desc,
            "h1_count": len(h1s),
            "h1_samples": h1s[:3],
            "seo_score": seo_score
        },
        "performance": {
            "perf_score": perf_score
        },
        "overall_score": overall,
        "suggestions": suggestions
    }

from flask import render_template

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/lead-scoring", methods=["GET", "POST"])
def lead_scoring():
    results = None
    industry = city = ""
    if request.method == "POST":
        industry = request.form.get("industry","").strip()
        city = request.form.get("city","").strip()
        n = int(request.form.get("count","8"))
        results = generate_leads(industry, city, n)
    return render_template("lead_scoring.html", results=results, industry=industry, city=city)

@app.route("/website-check", methods=["GET", "POST"])
def website_check():
    report = None
    url = ""
    if request.method == "POST":
        url = request.form.get("url","").strip()
        report = analyze_site(url)
    return render_template("website_check.html", report=report, url=url)

@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
