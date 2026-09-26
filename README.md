# StockWise — Complete Beginner Guide

Investment analysis & recommendation system for retail and small-scale investors.
**Django** (website + backend) · **PostgreSQL** (database) · **pandas + yfinance** (analysis) · **Bootstrap + Chart.js** (design + charts)

> ⚠️ This app is educational. Every page reminds users: *take your own decisions, don't rely on market tips.*

---

## 0. Where do I start — backend or frontend?

**Backend first, then frontend.** The frontend (pages) only shows what the backend (Python) gives it.
The code is already written, so the order you *set it up* in is:

1. Install tools (Python, PostgreSQL, VS Code)
2. Create the database
3. Start the backend (install packages → connect database → create tables)
4. Open the frontend in your browser and test every page
5. Then read the code, file by file (section 9), and start changing things

Commands below are for **Windows**. Mac/Linux differences are marked 🍎.

---

## 1. Install the tools (one time)

| Tool | Download | Important while installing |
|---|---|---|
| Python 3.12 | https://www.python.org/downloads/ | ✅ Tick **"Add python.exe to PATH"** on the first screen |
| PostgreSQL 16 or 17 | https://www.postgresql.org/download/windows/ | Remember the **password** you set for user `postgres`. Keep port **5432**. Keep **pgAdmin** ticked |
| VS Code | https://code.visualstudio.com/ | After installing, add the **Python** extension (Extensions icon on the left) |

Check Python works — open **Command Prompt** (Start → type `cmd`):

```bat
python --version
```
You should see `Python 3.12.x`. (🍎 use `python3 --version`)

---

## 2. Put the project on your computer

1. Unzip `stockwise.zip` to e.g. `C:\Projects\stockwise`
2. VS Code → **File → Open Folder** → choose `C:\Projects\stockwise`
3. **Terminal → New Terminal** (a terminal opens at the bottom, already inside the folder)

You should see `manage.py` when you type:
```bat
dir
```
(🍎 `ls`)

---

## 3. Create a virtual environment and install packages

A virtual environment (`venv`) is a private box of Python packages just for this project.

```bat
python -m venv venv
venv\Scripts\activate
```
🍎 `python3 -m venv venv` then `source venv/bin/activate`

Your terminal line now starts with `(venv)`. **Every time you open a new terminal, run the activate command again.**

> If PowerShell says *"running scripts is disabled"*: run
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, type `Y`, then activate again.
> Or switch the terminal to Command Prompt (the ⌄ next to `+` in the terminal panel).

Install everything the project needs:
```bat
python -m pip install --upgrade pip
pip install -r requirements.txt
```

This installs Django, psycopg (PostgreSQL driver), python-dotenv, pandas, numpy and yfinance.

---

## 4. Create the PostgreSQL database

**Option A — pgAdmin (clicking):**
1. Open **pgAdmin 4** → enter your master password
2. Left side: **Servers → PostgreSQL** → enter the `postgres` password
3. Right-click **Databases → Create → Database…**
4. Name: `stockwise_db` → **Save**

**Option B — SQL Shell (typing):** Start → **SQL Shell (psql)** → press Enter for the defaults, type your password, then:
```sql
CREATE DATABASE stockwise_db;
\q
```

---

## 5. Create your `.env` settings file

In the project folder, copy the example file:
```bat
copy .env.example .env
```
🍎 `cp .env.example .env`

Open `.env` in VS Code and change these two lines:
```
SECRET_KEY=any-long-random-text-like-k8f3!jd92hH2kd0q
DB_PASSWORD=the_postgres_password_you_chose
```
Save (Ctrl+S). Never share or upload `.env` — it holds your passwords.

---

## 6. Create the tables in the database

```bat
python manage.py migrate
```
You should see a list of `Applying ... OK` lines. Django just created all tables (users, watchlist, prediction log, contact messages, community posts) inside `stockwise_db`.

Create your admin account (you'll use it for the Admin page):
```bat
python manage.py createsuperuser
```
Type a username, email and password (the password stays invisible while typing — that's normal).

---

## 7. Run the website 🎉

```bat
python manage.py runserver
```
Open **http://127.0.0.1:8000** in Chrome.
Stop the server with **Ctrl + C**. Start it again with the same command.

---

## 8. Test every page

| Page | URL | What to check |
|---|---|---|
| Home | `/` | Navbar (About, Features, Help, Contacts), video hero, sections |
| Features | `/features/` | Fundamental + technical feature cards |
| Help | `/help/` | Quick start, glossary accordion, FAQ |
| Contacts / Community | `/contact/` | Send a message; log in and write a post |
| Register | `/register/` | Create a normal user |
| Login | `/login/` | Log in / out (Logout button in navbar) |
| Dashboard | `/dashboard/` | Search `TCS` + NSE → Analyse → **Add to watchlist**. Add 3–4 stocks; each card shows a mini chart + next-week range |
| Stock page | `/stock/TCS.NS/` | Outlook, charts (price, RSI, MACD, volume, BIAS, footprint), signals table, fundamentals table |
| Nifty 50 | `/nifty50/` | All 50 NIFTY companies: sector filter, search, outlook filter, mini charts, **Add all 50 to my watchlist** |
| Admin page | `/admin-panel/` | Only for your superuser: stats, messages, posts, most-watched stocks |
| Django admin | `/admin/` | Full database editor |

**No internet or Yahoo Finance not working?** Set `FORCE_DEMO_DATA=True` in `.env` and restart the server. The app then uses generated practice prices, shown with a yellow **DEMO DATA** badge. Set it back to `False` for real data.

**Indian stock symbols:** NSE = `.NS` (e.g. `RELIANCE.NS`), BSE = `.BO`. The dashboard adds the suffix for you when you choose the exchange.

---

## 9. How the project is organised (read in this order)

```
stockwise/
├── manage.py                 ← the command tool (runserver, migrate, …)
├── requirements.txt          ← list of packages
├── .env.example → .env       ← your secrets & options
├── stockwise/                ← PROJECT settings
│   ├── settings.py           ← database, apps, static files, login rules
│   └── urls.py               ← the "front door": sends URLs to the apps
├── core/                     ← APP 1: website pages & accounts
│   ├── models.py             ← tables: ContactMessage, CommunityPost
│   ├── forms.py              ← Register, Login, Contact, Post forms
│   ├── views.py              ← Python functions that build each page
│   ├── urls.py               ← /  /features/  /help/  /contact/  /login/ …
│   └── admin.py              ← shows tables in /admin/
├── analysis/                 ← APP 2: the stock brain
│   ├── models.py             ← tables: WatchlistItem, PredictionLog
│   ├── views.py              ← dashboard, stock page, watchlist, JSON API, Nifty 50 page
│   ├── nifty50.py            ← the 50 NIFTY companies (symbol, name, sector) — edit when NSE changes the index
│   ├── urls.py               ← /dashboard/  /stock/<symbol>/  /api/stock/<symbol>/
│   └── services/             ← pure analysis code (no web stuff)
│       ├── market_data.py    ← downloads prices + ratios from Yahoo Finance
│       ├── fundamentals.py   ← ROE, ROIC, Net margin, P/E, P/B, PEG → Good/Okay/Weak
│       ├── technicals.py     ← SMA, MACD, RSI, Bollinger, BIAS, order flow, volume footprint
│       ├── predictor.py      ← next-week (5 day) forecast + price range
│       ├── pipeline.py       ← joins all of the above into one result
│       ├── engine.py         ← adds caching + saves each forecast to PostgreSQL
│       ├── news.py           ← news from GNews API / Google News / Yahoo, all in one format
│       ├── sentiment.py      ← NLP: FinBERT deep learning sentiment (+ basic word-list fallback)
│       ├── markets.py        ← Market pulse: world indices, Indian & global sectors, commodities
│       └── demo.py           ← offline practice data
├── templates/                ← FRONTEND HTML
│   ├── base.html             ← shared layout (navbar, footer, CSS/JS links)
│   ├── partials/             ← navbar, footer, disclaimer
│   ├── core/                 ← home, features, help, contact, login, register, admin_panel
│   └── analysis/             ← dashboard, stock_detail
└── static/                   ← FRONTEND files
    ├── css/style.css         ← colours, layout, animations
    ├── js/main.js            ← scroll animations, counters
    ├── js/charts.js          ← all Chart.js graphs
    ├── images/               ← logo + illustrations (SVG)
    └── videos/hero.mp4       ← home page background video
```

### How frontend and backend connect (the most important idea)

**Normal pages:**
```
Browser asks /dashboard/
  → stockwise/urls.py  → analysis/urls.py  (finds name="dashboard")
  → analysis/views.py  dashboard()  reads the WatchlistItem table in PostgreSQL
  → render("analysis/dashboard.html", data)  fills {{ … }} in the HTML
  → browser shows the page
```

**Charts (JavaScript ↔ API):**
```
dashboard.html card has  data-api="/api/stock/TCS.NS/"
  → charts.js  fetch()es that URL
  → views.stock_api()  → engine.analyze_symbol()  → JSON
  → charts.js draws the mini chart with Chart.js
```
On the stock page the whole result is placed in the page with `{{ r|json_script:"analysis-data" }}` and `renderStockDetail()` draws the big charts.

**Forms:** `<form method="post">` + `{% csrf_token %}` → view checks `form.is_valid()` → saves to PostgreSQL → `redirect()`.

---

## 10. How the prediction works (explain this in your project report)

1. **Download** 1 year of daily prices + company ratios (Yahoo Finance via yfinance).
2. **Fundamental score** — each ratio gets +1 (good), 0 (okay) or −1 (weak):

   | Ratio | Good | Weak |
   |---|---|---|
   | ROE | ≥ 15% | < 8% |
   | ROIC (calculated: EBIT × (1−tax) ÷ (debt + equity − cash)) | ≥ 12% | < 6% |
   | Net profit margin | ≥ 15% | < 5% |
   | P/E | < 20 | > 40 or negative |
   | P/B | < 1.5 | > 5 |
   | PEG | < 1 | > 2 |

3. **Technical score** — seven signals scored from −1 to +1, then a weighted average:
   Moving averages 20%, MACD 20%, RSI 15%, order-flow 15%, Bollinger 10%, BIAS 10%, volume footprint 10%.
4. **Combined score** = 75% technical + 25% fundamental.
5. **Forecast**: expected move = score × ½ of the stock's normal weekly move (volatility of the last 60 days). Range = expected price ± one normal weekly move.
6. **Honesty check (back-test)**: the page shows how often the technical signal's direction matched the actual next-5-day move over the past year. ~50% = coin flip.

**Order books & volume footprints — be honest in your report:** real Level-2 order books and tick-by-tick footprint charts need paid live broker data (e.g. Zerodha Kite Connect, Upstox API). With free daily data this project uses well-known approximations: *order-flow pressure* (splits each day's volume into buying/selling by where the price closed in its range) and a *volume profile* (volume at each price level, Point of Control, 70% value area). Section 12 shows how to upgrade later.

---

## 11. Changing images and video

- **Video:** replace `static/videos/hero.mp4` with any MP4 (free stock videos: https://www.pexels.com/videos/ — search "stock market"). Keep it under ~10 MB.
- **Photos:** save JPGs with these exact names and they appear automatically (otherwise the built-in illustrations show):
  - `static/images/about.jpg` (Home → About)
  - `static/images/dashboard.jpg` (Home → How it works, Features)
  - `static/images/features.jpg` (Features → Technical)
  Free photos: https://unsplash.com (search "trading", "finance")
- **Colours:** edit the variables at the top of `static/css/style.css` (`--sw-green`, `--sw-blue`, …).
- After changing static files, press **Ctrl + F5** in the browser to reload without cache.

---

## 11b. News & Market pulse (Dashboard)

The Dashboard has two extra sections:

- **Market pulse**: coloured tiles showing today / this week / this month % change for NIFTY, SENSEX, Indian sector indices (IT, Auto, Pharma, FMCG, Metal, Energy…), world indices (S&P 500, Nasdaq, FTSE, Nikkei…), **global sectors** (iShares Global sector funds, which hold the biggest companies worldwide in each sector), gold, crude oil and USD/INR. Data comes from Yahoo Finance; no key is needed.
- **Market news**: tabs for India/NSE, Global markets, By sector (India or Global), and My stocks. Every stock page also shows the latest news about that company.

**News sources (tried in order, automatically):**

| Source | Key? | Used for |
|---|---|---|
| GNews API | Free key (100 requests/day, headlines up to 12 h old) | Market & sector news, company news backup |
| Google News RSS | No key | Backup when there is no key, the limit is reached, or GNews finds nothing |
| Yahoo Finance | No key | Company news on stock pages (tried first there) |

**How to add your GNews key (5 minutes):**

1. Go to https://gnews.io and click **Get API key**. Sign up with your email and confirm it.
2. On your GNews **Dashboard**, copy the **API key** (a long line of letters and numbers).
3. Open `.env` in VS Code and paste it after the `=` (no spaces, no quotes):
   ```
   GNEWS_API_KEY=paste_your_key_here
   ```
4. Save (**Ctrl + S**), stop the server (**Ctrl + C**) and start it again (`python manage.py runserver`).
5. Open the Dashboard. Under the news list it should say **"Source: GNews"**.

If the note says *"API key is wrong"*, check that you copied the whole key. *"daily limit reached"* means the 100 free requests are used up; the app switches to the free backup until the next day. News is reused for 30 minutes (`NEWS_CACHE_SECONDS`) to save requests. Keep the key secret: it lives only in `.env`, which is never uploaded.

**How the integration works (for your report):**
```
Browser (news.js) --fetch--> /api/news/?type=market&topic=india   (analysis/views.py: news_api)
   --> analysis/services/news.py: market_news()
         1. GNews  https://gnews.io/api/v4/search?q=...&country=in&apikey=KEY   (urllib, JSON)
         2. if that fails -> Google News RSS (XML)
   --> same simple format for every article {title, url, source, published, ...}
   --> cached 30 min --> JSON --> news.js draws the list (text is escaped for safety)
```

---

## 11c. AI news sentiment: FinBERT (NLP + deep learning)

Every headline gets a tag (🙂 Positive / 😐 Neutral / 🙁 Negative with a confidence %), and every news list shows a **News mood** bar. Each stock page's outlook card also shows the stock's news mood.

**Two engines (chosen automatically):**

| Engine | What it is | When it's used |
|---|---|---|
| **FinBERT (deep learning)** | A BERT neural network (110 million parameters) fine-tuned on financial news ([ProsusAI/finbert](https://huggingface.co/ProsusAI/finbert)). It understands context, e.g. "profit falls less than feared" | After you set it up (below) |
| Word list (basic) | Counts finance words like "surge", "loss", with simple "not" handling | Until FinBERT is set up, or if it fails |

The list always says which engine was used ("Analysed by …").

**Set up FinBERT (one time, ~10 minutes, needs ~1 GB free disk):**

1. In the VS Code terminal, with **(venv)** showing, install PyTorch + transformers (~300 MB download):
   ```
   pip install -r requirements-ml.txt
   ```
2. Create the new database table (for the sentiment history):
   ```
   python manage.py migrate
   ```
3. Download FinBERT (~440 MB, only once) and test it:
   ```
   python manage.py setup_finbert
   ```
   You'll see 5 test headlines labelled positive / negative / neutral.
4. Restart the server: `python manage.py runserver`. The news box should now say **"Analysed by FinBERT (deep learning)"**.

If `pip install` fails on torch, check your Python version with `python --version` (PyTorch needs 64-bit Python 3.10–3.13), or install the CPU build directly:
`pip install torch --index-url https://download.pytorch.org/whl/cpu`

**How it works (for your report):**
```
headline text ──► tokenizer (splits into word pieces) ──► FinBERT (12 transformer layers)
      ──► 3 numbers (logits) ──► softmax ──► P(positive), P(negative), P(neutral)
headline score = P(positive) − P(negative)      (−1 … +1)
news mood      = average score of all headlines (> +0.15 Positive, < −0.15 Negative)
```
- Code: `analysis/services/sentiment.py` (model loading + prediction) and `analysis/services/news.py` (runs it on every fresh news download).
- Each result is saved in the **SentimentLog** table (PostgreSQL). Browse it at `/admin/`.
- **Why news mood isn't mixed into the forecast:** the forecast only uses signals we can back-test on past data, and free APIs don't provide years of old headlines. The saved SentimentLog history is what Stage 2 can learn from later.
- Settings (`.env`): `SENTIMENT_ENGINE=auto` (default), `wordlist`, or `off`.

---

## 12. Troubleshooting

| Error | Fix |
|---|---|
| `'python' is not recognized` | Reinstall Python and tick "Add to PATH", then open a new terminal |
| `No module named django` | You forgot `venv\Scripts\activate` (look for `(venv)`) |
| `password authentication failed for user "postgres"` | Wrong `DB_PASSWORD` in `.env` |
| `database "stockwise_db" does not exist` | Do step 4 again |
| `connection refused … port 5432` | PostgreSQL isn't running: Start → Services → `postgresql-x64-16` → Start |
| `relation "…" does not exist` | Run `python manage.py migrate` |
| Stock page: "No price data found" | Check the symbol (TCS.NS not TCS), check internet, or set `FORCE_DEMO_DATA=True` |
| Page looks unstyled | CSS/JS load from the internet (Bootstrap, Chart.js CDN) — check your connection |
| `That port is already in use` | Another server is running: close it, or `python manage.py runserver 8001` |
| Admin page sends me to Home | Log in with the superuser from step 6 |
| Some Nifty 50 cards show "Too many requests" / fail | Yahoo Finance limits free requests. Wait a minute and click **Retry**, or set `ANALYSIS_CACHE_SECONDS=3600` in `.env` so results are reused for an hour |

**Quick test without PostgreSQL:** set `USE_SQLITE=True` in `.env` and run `python manage.py migrate` — Django uses a local file instead. Switch back to `False` for the real project.

---

## 13. Every command in one place

```bat
python -m venv venv                  :: create virtual env (once)
venv\Scripts\activate                :: activate (every new terminal)
pip install -r requirements.txt      :: install packages (once)
copy .env.example .env               :: settings file (once, then edit)
python manage.py migrate             :: create/update tables
python manage.py createsuperuser     :: make an admin user
python manage.py runserver           :: start the website
python manage.py makemigrations      :: ONLY after you change a models.py
python manage.py shell               :: Python console with your project loaded
```

---

## 14. What to learn / build next

1. Learn the basics used here: Python functions & dictionaries → Django tutorial (https://docs.djangoproject.com/en/5.2/intro/tutorial01/) → pandas basics.
2. Add an "accuracy" page: compare rows in `PredictionLog` with the real price 5 days later.
3. Try a machine-learning model (scikit-learn) using the indicator scores as features — and compare its hit rate honestly with the rule-based score.
4. Real order-book / footprint data: connect a broker API (Zerodha Kite Connect or Upstox) — needs an account and API subscription.
5. Deploy online (e.g. Render or Railway with a managed PostgreSQL). Before deploying: `DEBUG=False`, a real `SECRET_KEY`, your domain in `ALLOWED_HOSTS`, and `python manage.py collectstatic`.

---

⚠️ **Disclaimer:** StockWise is for learning. It is not investment advice. Take your own decisions and don't rely on market tips.
