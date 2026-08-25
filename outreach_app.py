from __future__ import annotations
import csv
import html
import json
import os
import re
import smtplib
import ssl
import threading
import webbrowser
from dataclasses import asdict, dataclass
from email.message import EmailMessage
from email.parser import BytesParser
from email.policy import default
from pathlib import Path
from tkinter import END, BOTH, LEFT, X, BooleanVar, StringVar, Tk, filedialog, messagebox
from tkinter import ttk

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "campaign_output"
INBOX = ROOT / "mailbox" / "inbox"
OUT.mkdir(exist_ok=True)
INBOX.mkdir(parents=True, exist_ok=True)

@dataclass
class Lead:
    name: str
    category: str
    city: str
    country: str
    email: str = ""
    phone: str = ""
    address: str = ""
    hours: str = ""
    menu: str = ""
    website: str = ""
    rating: float = 0
    reviews: int = 0
    mobile_gap: int = 10
    booking_signal: int = 10
    independent_signal: int = 10
    source: str = ""
    @property
    def score(self):
        need = 22 if not self.website else 0
        social = min(18, int(self.rating * 3) + min(10, self.reviews // 25))
        fit = min(20, self.booking_signal + self.independent_signal)
        return min(100, need + self.mobile_gap + social + fit + 10)

COUNTRIES = {
    "Thailand": ["Bangkok", "Chiang Mai", "Phuket", "Pattaya", "Khon Kaen"],
    "United Kingdom": ["London", "Manchester", "Liverpool", "Bath", "Blackpool"],
    "Australia": ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide"],
    "Singapore": ["Central Area", "East Coast", "Tiong Bahru", "Katong"],
}
LEADS = [
    Lead("Khao Soi Mae Sai", "Northern Thai noodles", "Chiang Mai", "Thailand", phone="053 213 284", address="29/1 Soi Ratchaphruek, Chiang Mai", hours="Mon–Sat 08:00–16:00", menu="Chicken Khao Soi ฿70; Beef Khao Soi ฿75; Nam Ngiao ฿50", rating=4.1, reviews=253, mobile_gap=13, booking_signal=12, independent_signal=13, source="https://www.wongnai.com/restaurants/24090Sd"),
    Lead("Yunai Oden", "Japanese street food", "Chiang Mai", "Thailand", phone="065 417 9979", address="Suriwong Soi 5, Chang Khlan, Chiang Mai", hours="Daily 11:00–15:00, 16:30–22:00", menu="Oden buffet; mala broth; beer", mobile_gap=15, booking_signal=15, independent_signal=14, source="https://www.wongnai.com/restaurants/744739Tj"),
    Lead("Sandwich Bar", "Cafe & sandwiches", "Chiang Mai", "Thailand", phone="+66 53 221 528", address="3 Arak Road, Chiang Mai", hours="Daily 07:00–20:30", menu="Baked pork rib; beef curry; sandwiches", mobile_gap=13, booking_signal=10, independent_signal=15, source="https://www.wongnai.com/restaurants/8047Ap"),
]

def esc(value):
    return html.escape(str(value or ""))

def slug(value):
    return re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-") or "local-business"

def make_demo(lead):
    folder = OUT / ("demo-" + slug(lead.name))
    folder.mkdir(parents=True, exist_ok=True)
    rows = []
    for item in lead.menu.split(";"):
        item = item.strip()
        if " ฿" in item:
            n, p = item.rsplit(" ฿", 1)
            rows.append(f"<li><span>{esc(n)}</span><b>฿{esc(p)}</b></li>")
        else:
            rows.append(f"<li>{esc(item)}</li>")
    page = f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(lead.name)}</title><style>
:root{{--ink:#202820;--cream:#f5f0e4;--accent:#c75a37;--sage:#c8d0bd}}*{{box-sizing:border-box}}body{{margin:0;background:var(--cream);color:var(--ink);font:16px system-ui,sans-serif}}main{{max-width:1100px;margin:auto;padding:34px 6vw}}nav,.foot{{display:flex;justify-content:space-between;align-items:center}}.logo{{font-weight:800;letter-spacing:.08em}}.pill{{background:var(--accent);color:#fff;padding:12px 18px;border-radius:99px;text-decoration:none}}.hero{{padding:110px 0 80px;display:grid;grid-template-columns:1.1fr .9fr;gap:50px;align-items:center}}h1,h2{{font-family:Georgia,serif;font-weight:600;line-height:1}}h1{{font-size:clamp(52px,7vw,92px);margin:20px 0}}h2{{font-size:48px}}em,.eyebrow,li b{{color:var(--accent)}}.eyebrow{{letter-spacing:.18em;font-size:12px;font-weight:700}}p{{color:#657067;line-height:1.7}}.art{{min-height:350px;border-radius:180px 180px 22px 22px;background:linear-gradient(140deg,#e9bc69,#b74d31);display:grid;place-items:center;font-size:100px;box-shadow:18px 18px 0 var(--sage)}}section{{padding:70px 0}}.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}}.card{{background:#fff;padding:22px;border:1px solid #ddd7c8;min-height:160px}}.card h3{{font:600 25px Georgia,serif}}ul{{list-style:none;padding:0}}li{{display:flex;justify-content:space-between;padding:16px 0;border-bottom:1px solid #ddd7c8}}.visit{{background:var(--sage);padding:35px;display:grid;grid-template-columns:1fr 1fr;gap:25px}}.foot{{padding:25px 0;color:#657067;font-size:13px}}@media(max-width:700px){{.hero,.visit,.grid{{grid-template-columns:1fr}}h1{{font-size:55px}}}}
</style><body><main><nav><div class="logo">{esc(lead.name)}</div><a class="pill" href="tel:{esc(lead.phone)}">Call the shop</a></nav><div class="hero"><div><div class="eyebrow">{esc(lead.category)} · {esc(lead.city)}</div><h1>A local bowl<br><em>worth the detour.</em></h1><p>{esc(lead.name)} serves everyday comfort food for hungry locals and travellers. This concept brings the menu, prices, hours and contact details into one clear page.</p></div><div class="art">🍜</div></div><section><div class="eyebrow">MENU</div><h2>What to order</h2><div class="grid"><div class="card"><ul>{''.join(rows)}</ul></div><div class="card"><h3>Fresh, simple, local.</h3><p>Show signature dishes, prices and daily updates before guests arrive.</p></div><div class="card"><h3>Plan your stop.</h3><p>Clear hours, directions and a call button help visitors decide.</p></div></div></section><section class="visit"><div><div class="eyebrow">VISIT</div><h2>Come by.</h2><p>{esc(lead.address)}</p><p><strong>{esc(lead.hours)}</strong></p></div><div><div class="eyebrow">CONTACT</div><p><strong>{esc(lead.phone)}</strong></p><p>Walk-in · takeaway · ask about today’s queue</p><a class="pill" href="https://www.google.com/maps/search/?api=1&query={esc(lead.address)}">Get directions ↗</a></div></section><div class="foot"><span>{esc(lead.name)} · {esc(lead.city)}</span><span>Website concept demo</span></div></main></body></html>"""
    path = folder / "index.html"
    path.write_text(page, encoding="utf-8")
    return path


def search_places(country, region, api_key):
    if not api_key:
        raise ValueError("Set GOOGLE_MAPS_API_KEY before searching public places.")
    import urllib.request
    query = f"independent restaurant in {region}, {country}"
    payload = json.dumps({"textQuery": query, "pageSize": 20, "languageCode": "en"}).encode()
    req = urllib.request.Request("https://places.googleapis.com/v1/places:searchText", data=payload, method="POST", headers={"Content-Type":"application/json", "X-Goog-Api-Key":api_key, "X-Goog-FieldMask":"places.displayName,places.formattedAddress,places.internationalPhoneNumber,places.websiteUri,places.rating,places.userRatingCount,places.regularOpeningHours.weekdayDescriptions"})
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.loads(response.read().decode())
    leads = []
    for place in data.get("places", []):
        name = place.get("displayName", {}).get("text", "Unnamed business")
        hours = "; ".join(place.get("regularOpeningHours", {}).get("weekdayDescriptions", []))
        leads.append(Lead(name, "Restaurant", region, country, phone=place.get("internationalPhoneNumber", ""), address=place.get("formattedAddress", ""), hours=hours, website=place.get("websiteUri", ""), rating=float(place.get("rating", 0) or 0), reviews=int(place.get("userRatingCount", 0) or 0), mobile_gap=15, booking_signal=10, independent_signal=12, source="Google Places API"))
    return leads
FIXED = {
    "price": "I can provide a fixed quote after confirming the pages, booking needs and whether you own a domain. There is no charge for the initial concept.",
    "timeline": "A simple restaurant site usually takes 3–7 working days after content and photos are approved.",
    "photos": "I will use owner-approved photos before publishing and will not present AI images as real menu items.",
    "maintenance": "I can offer a handover guide and optional maintenance. The exact arrangement will be written in the quote.",
}

def compose(lead, demo, sender):
    subject = "A quick website idea for " + lead.name
    body = f"""Hi there,

I came across {lead.name} while looking for local places in {lead.city}. I made a small concept using your public business details so you can see the idea before deciding anything:

{Path(demo).resolve().as_uri()}

It brings together your main dishes, prices, opening hours, directions and a clear call button. This is only a demonstration; I would confirm every detail and use owner-approved photos before publishing.

If this feels useful, reply “details” and I can send a fixed quote. Reply “not interested” and I will not follow up.

Best,
{sender}"""
    return subject, body

def smtp_send(config, recipient, subject, body):
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = config["from_email"], recipient, subject
    msg.set_content(body)
    paragraphs = "".join(f"<p>{esc(line) if not line.startswith('file:') else f'<a href=\"{esc(line)}\">Open the personalised website concept ↗</a>'}</p>" for line in body.splitlines() if line.strip())
    msg.add_alternative(f"<html><body style='font-family:Arial,sans-serif;color:#202820'><div style='background:#f5f0e4;padding:28px;border-radius:12px'><h2 style='color:#c75a37'>A small website idea for your business</h2>{paragraphs}</div></body></html>", subtype="html")
    with smtplib.SMTP(config["host"], int(config.get("port", 587)), timeout=30) as server:
        server.starttls(context=ssl.create_default_context())
        server.login(config["username"], config["password"])
        server.send_message(msg)

def read_eml():
    result = []
    for path in sorted(INBOX.glob("*.eml")):
        with path.open("rb") as stream:
            msg = BytesParser(policy=default).parse(stream)
        body = msg.get_body(preferencelist=("plain", "html"))
        result.append((path.name, msg.get("From", ""), msg.get("Subject", ""), body.get_content() if body else ""))
    return result

def fixed_answer(message):
    low = message.lower()
    aliases = {"price": ["price", "cost", "quote"], "timeline": ["when", "time", "timeline"], "photos": ["photo", "image"], "maintenance": ["update", "maintenance"]}
    for key, words in aliases.items():
        if any(word in low for word in words):
            return FIXED[key]
    return "No fixed answer matched. Review and write a human response."

class App:
    def __init__(self, root):
        self.root, self.leads, self.selected, self.demo = root, LEADS[:], None, None
        root.title("Local Outreach Studio")
        root.geometry("1120x760")
        self.build()

    def build(self):
        top = ttk.Frame(self.root, padding=12); top.pack(fill=X)
        ttk.Label(top, text="Local Outreach Studio", font=("Segoe UI", 18, "bold")).pack(side=LEFT)
        ttk.Label(top, text="  research → demo → draft → human-approved send", foreground="#667").pack(side=LEFT, padx=12)
        self.country = StringVar(value="Thailand"); self.region = StringVar(value="Chiang Mai")
        ttk.Label(top, text="Country").pack(side=LEFT, padx=(25,4)); c = ttk.Combobox(top, textvariable=self.country, values=list(COUNTRIES), width=15); c.pack(side=LEFT); c.bind("<<ComboboxSelected>>", self.change_regions)
        ttk.Label(top, text="Region").pack(side=LEFT, padx=(10,4)); self.regions = ttk.Combobox(top, textvariable=self.region, values=COUNTRIES["Thailand"], width=15); self.regions.pack(side=LEFT)
        ttk.Button(top, text="Load sample leads", command=self.load).pack(side=LEFT, padx=10)
        tabs = ttk.Notebook(self.root); tabs.pack(fill=BOTH, expand=True, padx=12, pady=(0,12))
        self.t_research, self.t_demo, self.t_mail, self.t_reply = [ttk.Frame(tabs, padding=12) for _ in range(4)]
        for tab, title in [(self.t_research,"1 · Research & ranking"),(self.t_demo,"2 · Demo website"),(self.t_mail,"3 · Email draft"),(self.t_reply,"4 · Replies")]: tabs.add(tab, text=title)
        self.build_research(); self.build_demo(); self.build_mail(); self.build_reply()

    def change_regions(self, _=None):
        values = COUNTRIES.get(self.country.get(), []); self.regions["values"] = values
        if values: self.region.set(values[0])

    def build_research(self):
        ttk.Label(self.t_research, text="Score = missing-site need + mobile gap + social proof + service fit. Edit the data before outreach.", foreground="#667").pack(anchor="w")
        cols = ("rank","name","city","category","score","rating","site","source")
        self.tree = ttk.Treeview(self.t_research, columns=cols, show="headings", height=17)
        for col, title, width in [("rank","#",40),("name","Business",190),("city","City",100),("category","Category",150),("score","Score",65),("rating","Rating",65),("site","Site",65),("source","Source",260)]:
            self.tree.heading(col,text=title); self.tree.column(col,width=width)
        self.tree.pack(fill=BOTH, expand=True, pady=12); self.tree.bind("<<TreeviewSelect>>", self.pick)
        search=ttk.Frame(self.t_research); search.pack(fill=X, pady=(0,8)); self.maps_key=StringVar(value=os.environ.get("GOOGLE_MAPS_API_KEY","")); ttk.Label(search,text="Google Places API key (optional)").pack(side=LEFT); ttk.Entry(search,textvariable=self.maps_key,show="*",width=26).pack(side=LEFT,padx=8); ttk.Button(search,text="Search selected region",command=self.search_web).pack(side=LEFT)
        ttk.Button(self.t_research, text="Export ranking CSV", command=self.export).pack(anchor="e")
        self.populate()

    def search_web(self):
        try:
            found = search_places(self.country.get(), self.region.get(), self.maps_key.get().strip())
            if not found:
                messagebox.showinfo("No results", "No public places were returned for this query.")
                return
            self.leads = found
            self.populate()
            messagebox.showinfo("Search complete", f"Loaded {len(found)} public places. Review every record before outreach.")
        except Exception as exc:
            messagebox.showerror("Search failed", str(exc))

    def populate(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        for i, lead in enumerate(sorted(self.leads, key=lambda x:x.score, reverse=True), 1):
            self.tree.insert("", END, iid=slug(lead.name), values=(i,lead.name,lead.city,lead.category,lead.score,lead.rating or "—","Yes" if lead.website else "No",lead.source))

    def pick(self, _=None):
        if not self.tree.selection(): return
        key = self.tree.selection()[0]; self.selected = next((x for x in self.leads if slug(x.name)==key), None)
        if self.selected:
            self.detail.config(text=f"Selected: {self.selected.name} · score {self.selected.score}/100 · {self.selected.address}")
            self.mail_selected.config(text=f"Selected: {self.selected.name}")

    def load(self):
        self.leads = LEADS[:]; self.populate(); messagebox.showinfo("Loaded","Thailand sample leads loaded. Replace with approved public data before outreach.")

    def export(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv")])
        if not path: return
        with open(path,"w",newline="",encoding="utf-8-sig") as stream:
            fields = list(asdict(self.leads[0]).keys()) + ["score"]; writer = csv.DictWriter(stream,fieldnames=fields); writer.writeheader()
            for lead in sorted(self.leads,key=lambda x:x.score,reverse=True): writer.writerow({**asdict(lead),"score":lead.score})

    def build_demo(self):
        self.detail = ttk.Label(self.t_demo, text="Select a lead in Research, then generate a personalized demo.", wraplength=900); self.detail.pack(anchor="w")
        ttk.Button(self.t_demo,text="Generate website demo",command=self.generate).pack(anchor="w",pady=12)
        self.demo_path = StringVar(); ttk.Entry(self.t_demo,textvariable=self.demo_path).pack(fill=X,pady=5)
        ttk.Button(self.t_demo,text="Open demo in browser",command=lambda:webbrowser.open(Path(self.demo_path.get()).as_uri()) if self.demo_path.get() else None).pack(anchor="w")

    def generate(self):
        if not self.selected: messagebox.showwarning("Select a lead","Select a lead in the ranking table first."); return
        self.demo = make_demo(self.selected); self.demo_path.set(str(self.demo)); messagebox.showinfo("Created",str(self.demo))

    def build_mail(self):
        self.mail_selected = ttk.Label(self.t_mail,text="Selected: none"); self.mail_selected.pack(anchor="w")
        row=ttk.Frame(self.t_mail); row.pack(fill=X,pady=10); ttk.Label(row,text="Sender name").pack(side=LEFT); self.sender=StringVar(value="Your Name"); ttk.Entry(row,textvariable=self.sender,width=24).pack(side=LEFT,padx=8); ttk.Button(row,text="Compose draft",command=self.compose_mail).pack(side=LEFT)
        ttk.Label(self.t_mail,text="Subject").pack(anchor="w"); self.subject=StringVar(); ttk.Entry(self.t_mail,textvariable=self.subject).pack(fill=X,pady=4)
        self.body=ttk.Text(self.t_mail,height=19,wrap="word"); self.body.pack(fill=BOTH,expand=True)
        send=ttk.Frame(self.t_mail); send.pack(fill=X,pady=8); ttk.Label(send,text="Recipient").pack(side=LEFT); self.recipient=StringVar(); ttk.Entry(send,textvariable=self.recipient,width=34).pack(side=LEFT,padx=8); self.dry=BooleanVar(value=True); ttk.Checkbutton(send,text="Preview / dry-run",variable=self.dry).pack(side=LEFT,padx=12); ttk.Button(send,text="Send after confirmation",command=self.send).pack(side=LEFT)
        ttk.Label(self.t_mail,text="No bulk sending. Review recipient, content and opt-out basis before each message.",foreground="#a55").pack(anchor="w")

    def compose_mail(self):
        if not self.selected: messagebox.showwarning("Select a lead","Select a lead first."); return
        if not self.demo: self.demo = make_demo(self.selected)
        subject, body = compose(self.selected,self.demo,self.sender.get()); self.subject.set(subject); self.recipient.set(self.selected.email); self.body.delete("1.0",END); self.body.insert("1.0",body)

    def send(self):
        if self.dry.get(): messagebox.showinfo("Dry run","No email was sent. Uncheck dry-run only after reviewing the message."); return
        recipient, subject, body = self.recipient.get().strip(), self.subject.get().strip(), self.body.get("1.0",END).strip()
        if not recipient or not subject or not body: messagebox.showwarning("Incomplete","Recipient, subject and body are required."); return
        if not messagebox.askyesno("Confirm one-to-one send",f"Send one email to {recipient}?"): return
        try:
            with open(os.environ.get("SMTP_CONFIG_JSON","smtp_config.json"),encoding="utf-8") as stream: config=json.load(stream)
            smtp_send(config,recipient,subject,body); messagebox.showinfo("Sent","Email sent successfully.")
        except Exception as exc: messagebox.showerror("Send failed",str(exc))

    def build_reply(self):
        ttk.Label(self.t_reply,text="Drop .eml files into mailbox/inbox, or paste an inbound message. Replies stay drafts until reviewed.",wraplength=900).pack(anchor="w")
        self.inbox=ttk.Combobox(self.t_reply,values=[x[0] for x in read_eml()],width=60); self.inbox.pack(anchor="w",pady=10); self.inbox.bind("<<ComboboxSelected>>",self.load_eml)
        self.incoming=ttk.Text(self.t_reply,height=10,wrap="word"); self.incoming.pack(fill=X)
        row=ttk.Frame(self.t_reply); row.pack(fill=X,pady=10); ttk.Button(row,text="Fixed answer",command=self.fixed).pack(side=LEFT); ttk.Label(row,text="Optional AI key").pack(side=LEFT,padx=(20,4)); self.key=StringVar(value=os.environ.get("OPENAI_API_KEY","")); ttk.Entry(row,textvariable=self.key,show="*",width=25).pack(side=LEFT); ttk.Button(row,text="Generate AI draft",command=self.ai).pack(side=LEFT,padx=8); ttk.Button(row,text="Send reply after confirmation",command=self.send_reply).pack(side=LEFT,padx=8)
        self.reply_to=StringVar(); ttk.Label(self.t_reply,textvariable=self.reply_to,foreground="#667").pack(anchor="w"); self.reply=ttk.Text(self.t_reply,height=9,wrap="word"); self.reply.pack(fill=BOTH,expand=True)

    def load_eml(self,_=None):
        for name,sender,_,body in read_eml():
            if name==self.inbox.get(): self.reply_to.set("Reply to: "+sender); self.incoming.delete("1.0",END); self.incoming.insert("1.0",body)

    def send_reply(self):
        recipient=self.reply_to.get().replace("Reply to: ","").strip(); body=self.reply.get("1.0",END).strip()
        if not recipient or "@" not in recipient: messagebox.showwarning("No recipient","Load an inbound .eml first or enter a verified recipient."); return
        if not body: messagebox.showwarning("Empty draft","Generate or write a reply first."); return
        if not messagebox.askyesno("Confirm reply",f"Send one reply to {recipient}?"): return
        try:
            with open(os.environ.get("SMTP_CONFIG_JSON","smtp_config.json"),encoding="utf-8") as stream: config=json.load(stream)
            smtp_send(config,recipient,"Re: Website concept",body); messagebox.showinfo("Sent","Reply sent successfully.")
        except Exception as exc: messagebox.showerror("Send failed",str(exc))
    def fixed(self):
        self.reply.delete("1.0",END); self.reply.insert("1.0",fixed_answer(self.incoming.get("1.0",END)))

    def ai(self):
        message=self.incoming.get("1.0",END).strip()
        if not message: return
        self.reply.delete("1.0",END); self.reply.insert("1.0","AI draft is optional; configure OPENAI_API_KEY to enable it.")
        if not self.key.get().strip(): return
        def work():
            try:
                import urllib.request
                payload={"model":"gpt-4.1-mini","messages":[{"role":"system","content":"Write a concise, truthful business reply. Do not invent prices, guarantees or reviews."},{"role":"user","content":message}],"temperature":0.2}
                req=urllib.request.Request("https://api.openai.com/v1/chat/completions",data=json.dumps(payload).encode(),headers={"Authorization":"Bearer "+self.key.get().strip(),"Content-Type":"application/json"})
                with urllib.request.urlopen(req,timeout=30) as response: result=json.loads(response.read().decode())["choices"][0]["message"]["content"]
            except Exception as exc: result="AI draft failed: "+str(exc)
            self.root.after(0,lambda:(self.reply.delete("1.0",END),self.reply.insert("1.0",result.strip())))
        threading.Thread(target=work,daemon=True).start()

if __name__ == "__main__":
    root=Tk(); App(root); root.mainloop()








