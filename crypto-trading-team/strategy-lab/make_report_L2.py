#!/usr/bin/env python3
"""Generates report_section_L2.md (section 10) + registry_rows_L2.md from results_L2*.csv / run_L2_output.txt / diagnostics_L2_output.txt. All numbers come from those files.
Run: python3 make_report_L2.py"""
import os, re, numpy as np, pandas as pd
H = os.path.dirname(os.path.abspath(__file__)); R = pd.read_csv(f"{H}/results_L2.csv"); Y = pd.read_csv(f"{H}/results_L2_L101_by_year.csv"); HP = pd.read_csv(f"{H}/results_L2_L101_hour_profile.csv")
RUN = open(f"{H}/run_L2_output.txt").read(); DIAG = open(f"{H}/diagnostics_L2_output.txt").read()
PER = ["IS70", "OOS30", "FULL", "IS_fixed", "OOS_fixed"]
PN = {"IS70": "IS (أول 70%)", "OOS30": "**OOS (آخر 30%)**", "FULL": "FULL", "IS_fixed": "IS_fixed (قبل 2023-06-01)", "OOS_fixed": "OOS_fixed (من 2023-06-01)"}
def row(s, g, p): return R[(R.strat == s) & (R.group == g) & (R.period == p)].iloc[0]
def pc(x, d=1, sign=True):
    return "n/a" if pd.isna(x) else (f"{x*100:+.{d}f}%" if sign else f"{x*100:.{d}f}%")
def f2(x): return "n/a" if pd.isna(x) else ("∞" if np.isinf(x) else f"{x:.2f}")
def ci2(a, b): return "n/a" if pd.isna(a) else f"[{pc(a,2)}, {pc(b,2)}]"
def ci(a, b): return "n/a" if pd.isna(a) else f"[{pc(a)}, {pc(b)}]"
def pcb(x):   # big returns
    return "n/a" if pd.isna(x) else (f"{x*100:+,.0f}%" if abs(x) >= 10 else f"{x*100:+.1f}%")
def nlab(n): return "**غير كافٍ**" if n < 100 else "كافٍ (≥100)"
def table(head, rows): return "\n".join(["| " + " | ".join(head) + " |", "|" + "---|"*len(head)] + ["| " + " | ".join(map(str, r)) + " |" for r in rows])
def trade_tbl(strat, groups, first="الأصل"):
    rows = []
    for g in groups:
        for p in PER:
            r = row(strat, g, p); n = int(r.n)
            rows.append([g, PN[p], n, pc(r.win_rate, 1, False), pc(r.avg_win, 2 if strat.startswith('L101') else 1), pc(r.avg_loss, 2 if strat.startswith('L101') else 1), f2(r.profit_factor), pc(r.avg_trade, 2 if strat.startswith("L101") else 1), pc(r.median_trade, 2 if strat.startswith("L101") else 1),
                         ci(r.ci_lo, r.ci_hi) if not strat.startswith("L101") else f"[{pc(r.ci_lo,2)}, {pc(r.ci_hi,2)}]", ci(r.t_lo, r.t_hi) if not strat.startswith("L101") else f"[{pc(r.t_lo,2)}, {pc(r.t_hi,2)}]", f2(r.pf_ex_top3), nlab(n)])
    return table([first, "الفترة", "#صفقات", "Win rate", "متوسط الربح", "متوسط الخسارة", "PF", "متوسط الصفقة", "Median", "95% CI bootstrap", "95% CI t/normal", "PF بدون أفضل 3", "حجم العينة"], rows)
def triple(r, pre): return f"{pcb(r[pre+'ret'])} / {pc(r[pre+'maxdd'])} / {r[pre+'sharpe']:.2f}"

# ---------- facts
m = re.search(r"trade lists identical.*: (\w+) \| n trades (\d+)", RUN); same = m.group(1) == "True"; ntr = int(m.group(2))
mc = re.search(r"cells compared: (\d+) \| max abs diff per column: (\{.*\})", RUN); ncells = int(mc.group(1)); md = eval(mc.group(2))
nonci = max(v for k, v in md.items() if not k.startswith("ci_")); cimax = max(md["ci_lo"], md["ci_hi"])
rawb = pd.read_csv(f"{H}/data/BTCUSDT_1h.csv", usecols=["time"], parse_dates=["time"]); rawb = rawb[rawb.time < "2026-10-04"]; gaps = int((rawb.time.diff().dropna() != pd.Timedelta("1h")).sum())
hrs = f"{rawb.time.iloc[0]} → {rawb.time.iloc[-1]}"; nbars = len(rawb)
SPL101 = re.search(r'L-101 BTC: hourly.*70/30 split (\S+)', RUN).group(1)
best = {a: int(row("L101_ISsel", a, "FULL").start_hour) for a in ["BTC", "ETH"]}
b101 = row("L101", "BTC", "FULL"); e101 = row("L101", "ETH", "FULL")
b106 = row("L106", "BTC", "FULL"); b106o = row("L106", "BTC", "OOS30"); e106o = row("L106", "ETH", "OOS30"); p106 = row("L106", "POOLED", "FULL"); p106o = row("L106", "POOLED", "OOS30")
fdiag = re.findall(r"L-106 diagnostics (\w+): mean\|F\| per speed.*?: (\{.*?\}) \| mean target ([\d.]+) \| share target>0 ([\d.]+)", RUN)

o = []
o.append("\n\n---\n\n## 10. Part B — الدفعة الثانية: L-001 (إعادة تشغيل BTC/ETH) و L-106 و L-101 — 2026-10-04\n")
o.append("> **الثلاثة \"experimental — paper only\" ولا تولّد أي إشارة تداول حقيقية.** أقصى حالة ممكنة هنا BACKTESTED؛ APPROVED مستحيلة (تحتاج ≥100 صفقة OOS + walk-forward + أسبوعين paper، ولم يتحقق شيء منها).\n"
         "> كل رقم أدناه مولَّد بالسكربت `strategy-lab/backtest_L2.py` (المخرجات الخام: `results_L2.csv`، `results_L2_L101_by_year.csv`، `results_L2_L101_hour_profile.csv`، `trades_L106.csv`، `trades_L101_*.csv`، `trades_L001_rerun_BTC_ETH.csv`، `run_L2_output.txt`) والجداول مولَّدة آليًا من الـ CSV بواسطة `make_report_L2.py`. **لم يُضبط أي معامل** — قواعد المكتبة وقيمها الافتراضية كما هي، والقرارات الإضافية مثبّتة قبل رؤية أي نتيجة (10.1). إعادة التشغيل الكاملة تعطي ملفات متطابقة بايت-ببايت (md5).\n")
o.append("### 10.1 الإعداد والقرارات المسبقة\n")
o.append(table(["البند", "القيمة"], [
 ["الأصول", "BTC وETH فقط (ليس SOL). L-101 ورقتها عن BTC؛ تشغيل ETH = اختبار متانة خارج الورقة (موسوم)"],
 ["L-001", "نفس السكربت `backtest_L.py` بنفس المعاملات (Donchian 20/10، وقف 2×ATR20، حجم min(100%، 1% مخاطرة/مسافة الوقف)) على BTC وETH فقط؛ لم أكرر القسم 9 (انظر 10.2)"],
 ["L-106 — القاعدة", "forecast_k = (EMA_fast − EMA_slow) ÷ (close × تقلب يومي EWMA بـ span=35 للعوائد اليومية) للأزواج 8/32 و16/64 و32/128 و64/256؛ ×scalar؛ cap ±20؛ متوسط بسيط للأربعة (بلا FDM)؛ long-only: **الوزن = max(0, F)/20 من رأس المال في [0,1]**"],
 ["L-106 — scalars (اخترتها قبل رؤية النتائج)", "**Carver المنشورة: 5.3 و3.75 و2.65 و1.87** — لم تُحسب من بيانات ولم تُضبط. تشخيص فقط (لا يُستعمل لإعادة المعايرة): متوسط |F| الفعلي لكل سرعة ≈ " + "؛ ".join(f"{a}: " + ", ".join(f"{k}={v}" for k, v in eval(d).items()) for a, d, _, _ in fdiag) + " (قريب من 10 كما هو مقصود)"],
 ["L-106 — إعادة التوازن", "الإشارة عند إغلاق i → التنفيذ عند افتتاح i+1. **no-trade buffer = 10% من رأس المال** (لا تداول إلا إذا |الهدف − الوزن الحالي| > 0.10، أو الهدف = 0 أثناء الاحتفاظ ⇒ خروج كامل). الإشارات تبدأ من الشمعة 256 (إحماء EMA 64/256). **نسخة بلا buffer ونسخة بلا تكاليف (gross) = حساسيات موسومة فقط**"],
 ["L-106 — تكاليف ومقاييس", "رسوم 0.10% + انزلاق 0.05% لكل جهة على قيمة المتداول (notional). \"الصفقة\" = حلقة flat→long حتى العودة إلى صفر (عائدها = إجمالي ما بيع ÷ إجمالي ما اشتُري − 1، صافٍ من التكاليف). **قاعدة الـ100 صفقة لا تنطبق فعليًا** على استراتيجية بحجم مستمر: مقاييس المحفظة هي المرجع. turnover/yr = مجموع قيمة المتداول ÷ رأس المال ÷ السنوات؛ cost = مجموع (رسوم+انزلاق) كنسبة من رأس المال وقت التنفيذ"],
 ["L-101 — الساعات (تحقق)", "**تم التحقق**: ورقة Padyšák & Vojtko (2022)، SSRN 4081000، عبر وصف الاستراتيجية في Quantpedia الذي يقتبس الورقة: \"open a long position in the BTC at 22:00 (UTC +0) and hold it for two hours\" ⇒ دخول 22:00 وخروج 00:00 UTC. **لم أقرأ نص PDF الورقة نفسها** (تحقق من مصدر ثانوي يقتبسها)، وهذا يطابق نافذة المكتبة 22:00–00:00"],
 ["L-101 — التنفيذ", "دخول عند **افتتاح** شمعة 22:00 وخروج عند **إغلاق** شمعة 23:00 (= 00:00 UTC)، 100% من رأس المال لكل صفقة (بدون رافعة)، صفقة واحدة يوميًا (~365 دورة/سنة). تكاليف: 0.10% + 0.05% لكل جهة (~0.30% ذهابًا وإيابًا). أيام ينقصها أي من الشمعتين (توقفات Binance) تُتخطى"],
 ["L-101 — اختبار ثانوي (موسوم)", f"أفضل بداية لنافذة ساعتين تُختار **على أول 70% فقط** (بمتوسط الصفقة الصافي، 24 ساعة بداية) ثم تُطبَّق دون تغيير على آخر 30%: اختيارها = {best['BTC']}:00 UTC لـ BTC و{best['ETH']}:00 UTC لـ ETH. هذا اختبار تحيّز-انتقاء موسوم، وليس القاعدة المسبقة"],
 ["البيانات اليومية", "نفس ملفات المختبر `data/{BTC,ETH}USDT_1d.csv` (Binance spot عبر data-api.binance.vision)؛ شمعة 2026-10-04 الجزئية محذوفة؛ فترة الإحماء 200 شمعة وتقسيم 70/30 **مطابقان للقسم 9** (usable from 2018-03-05؛ split 2024-03-07)، مع التقسيم الثابت 2023-06-01 موسومًا IS_fixed/OOS_fixed. إشارات L-106 تبدأ بعد 256 شمعة (فالسلة مسطحة في الأيام 200–256 داخل النافذة)"],
 ["البيانات الساعية (L-101)", f"**مصدر**: Binance spot klines 1h من `data-api.binance.vision` (عامة بلا مفتاح؛ نجح من الجهاز، بعكس HTTP 451 من السحابة)، حُفظت في `data/BTCUSDT_1h.csv` و`data/ETHUSDT_1h.csv` عبر `fetch_1h.py`. **التغطية**: {hrs} UTC، {nbars:,} شمعة لكل أصل، {gaps} فجوة (توقفات المنصة). نوافذ L-101: من 2017-08-18 (لا يلزم إحماء)، IS70 = أول 70% من تاريخ الشموع الساعية (split = {SPL101})، + IS_fixed/OOS_fixed بتاريخ 2023-06-01. **نوافذ L-101 تختلف عن نوافذ L-001/L-106 (التاريخ يبدأ 2017 لا 2018 ولا إحماء)، فمقارنة الأرقام بين الاستراتيجيات تقريبية على مستوى النافذة**"],
 ["الإحصاءات", "95% CI: bootstrap (5000، seed ثابت لكل استدعاء) + تقريب t/طبيعي (±1.96·SE)؛ لا يُحسب عند n<10. PF بدون أفضل 3 صفقات. Sharpe = متوسط/انحراف العائد اليومي × √365 بلا معدل خالٍ من المخاطرة. L-101: السلسلة اليومية = عائد صفقة اليوم (0 في الأيام الأخرى) بتركيب أرباح كامل رأس المال. المحفظة المجمّعة (POOLED) = أوزان متساوية BTC+ETH بإعادة توازن يومية؛ لا POOLED لـ L-101 (الأصلان شديدا الارتباط والورقة عن BTC فقط)"],
]) + "\n")
o.append("### 10.2 تحقق: إعادة تشغيل L-001 على BTC/ETH مقابل القسم 9\n")
o.append(f"- **النتيجة: {'تطابق تام' if same else 'يوجد اختلاف — راجع run_L2_output.txt'}** في قائمة الصفقات (تواريخ الدخول/الخروج والعائد الصافي بدقة 1e-12): {ntr} صفقة (BTC+ETH) تطابق شريحتي BTC وETH من `trades_L001.csv`.\n"
         f"- قارنت {ncells} خلية من `results_L.csv` (BTC وETH × 5 نوافذ): أقصى فرق مطلق في كل مقاييس الصفقات والمحفظة والـ B&H = {nonci:.1e} (أخطاء فاصلة عائمة). **الاستثناء الوحيد: حدود bootstrap CI** (أقصى فرق {cimax*100:.2f} نقطة مئوية) لأن bootstrap عشوائي والبذرة هنا ثابتة لكل استدعاء بينما في القسم 9 كانت تتقدم عبر كل الاستدعاءات؛ ليس اختلافًا في الصفقات. أرقام CI في هذا القسم هي من التشغيل الجديد.\n"
         "- **لا تعارض** مع القسم 9. ما هو جديد هنا: صف POOLED = BTC+ETH فقط (بدون SOL)، لذلك يختلف عن POOLED في القسم 9 (3 أصول).\n")
o.append("### 10.3 ملخص الحالة\n")
l1 = row("L001", "POOLED", "FULL"); l1o = row("L001", "POOLED", "OOS30")
o.append(table(["الاستراتيجية", "الحالة", "أهم الأرقام (صافية من التكاليف)"], [
 ["L-001 (BTC+ETH)", "**BACKTESTED (ضعيف)** — بلا تغيير عن القسم 9", f"FULL: {int(l1.n)} صفقة، PF {f2(l1.profit_factor)}، متوسط {pc(l1.avg_trade)}، median {pc(l1.median_trade)}؛ OOS30: {int(l1o.n)} صفقة، PF {f2(l1o.profit_factor)}، متوسط {pc(l1o.avg_trade,2)}، CI {ci(l1o.ci_lo,l1o.ci_hi)}، PF بدون أفضل 3 = {f2(l1o.pf_ex_top3)}"],
 ["L-106 Carver EWMAC (BTC / ETH / POOLED)", "**BACKTESTED (ضعيف — يخفض الـ drawdown لكنه لا يتفوق على B&H خارج العينة)**", f"BTC FULL: عائد {pcb(b106.port_ret)} / maxDD {pc(b106.port_maxdd)} / Sharpe {b106.port_sharpe:.2f} مقابل B&H {pcb(b106.bh_ret)} / {pc(b106.bh_maxdd)} / {b106.bh_sharpe:.2f}؛ تعرض متوسط {pc(b106.avg_exposure,0,False)} وtime-in-market {pc(b106.time_in_mkt,0,False)}، turnover {b106.turnover_yr:.1f}×/سنة؛ OOS30 مجمّعًا: عائد {pc(p106o.port_ret)} / Sharpe {p106o.port_sharpe:.2f} مقابل B&H {pc(p106o.bh_ret)} / {p106o.bh_sharpe:.2f}"],
 ["L-101 BTC 22:00–00:00 UTC", "**REJECTED** (بعد التكاليف)", f"BTC FULL: {int(b101.n)} صفقة، متوسط gross {pc(b101.gross_avg_trade,2)} → net {pc(b101.avg_trade,2)} (CI t {ci2(b101.t_lo,b101.t_hi)})، PF net {f2(b101.profit_factor)} (gross {f2(b101.gross_profit_factor)})، عائد مركّب gross {pcb(b101.gross_port_ret)} → net {pcb(b101.port_ret)}؛ ETH نفس النافذة: net {pc(e101.avg_trade,2)}"],
]) + "\n")
o.append("### 10.4 L-001 Donchian 20/10 (وقف 2×ATR20) — BTC وETH\n")
o.append("**مستوى الصفقة** (net، العائد على قيمة المركز؛ مرجع القسم 9 للقواعد):\n")
o.append(trade_tbl("L001", ["BTC", "ETH", "POOLED"]) + "\n")
rows = []
for g in ["BTC", "ETH", "POOLED"]:
    for p in PER:
        r = row("L001", g, p); rows.append([g, PN[p], int(r.port_days), triple(r, "port_"), triple(r, "full_"), triple(r, "bh_")])
o.append("**مستوى المحفظة** (عائد / Max DD / Sharpe):\n")
o.append(table(["الأصل", "الفترة", "أيام", "حجم 1% مخاطرة (نفس S-01)", "حجم 100% notional", "Buy&Hold"], rows) + "\n")
o.append("### 10.5 L-106 Carver EWMAC ensemble (يومي، long-only، buffer 10%)\n")
o.append("**مستوى المحفظة** — الاستراتيجية الرئيسية (مع تكاليف). `avg exposure` = متوسط الوزن من رأس المال؛ `time in mkt` = نسبة الأيام بوزن > 0:\n")
rows = []
for g in ["BTC", "ETH", "POOLED"]:
    for p in PER:
        r = row("L106", g, p); rows.append([g, PN[p], int(r.port_days), triple(r, "port_"), triple(r, "bh_"), pc(r.time_in_mkt, 0, False), pc(r.avg_exposure, 0, False), f"{r.turnover_yr:.2f}×", pc(r.cost_sum, 2, False)])
o.append(table(["الأصل", "الفترة", "أيام", "L-106: عائد / Max DD / Sharpe", "Buy&Hold: عائد / Max DD / Sharpe", "time in mkt", "avg exposure", "turnover/yr", "تكاليف مجمّعة (% رأس المال)"], rows) + "\n")
o.append("**حلقات flat→long** (تعريفي للـ\"صفقات\"؛ **لا معنى لقاعدة الـ100 صفقة هنا** — العينة صغيرة جدًا والعائد موزّع على مراكز بأحجام متغيرة):\n")
rows = []
for g in ["BTC", "ETH", "POOLED"]:
    for p in PER:
        r = row("L106", g, p); rows.append([g, PN[p], int(r.n), pc(r.win_rate, 1, False), pc(r.avg_win), pc(r.avg_loss), f2(r.profit_factor), pc(r.avg_trade), pc(r.median_trade), ci(r.ci_lo, r.ci_hi), f2(r.pf_ex_top3)])
o.append(table(["الأصل", "الفترة", "#حلقات", "Win rate", "متوسط الربح", "متوسط الخسارة", "PF", "المتوسط", "Median", "95% CI bootstrap", "PF بدون أفضل 3"], rows) + "\n")
o.append("**حساسيات موسومة (ليست القاعدة المسبقة)** — buffer 10% (الرئيسية) مقابل بلا buffer مقابل بلا تكاليف (gross):\n")
rows = []
for g in ["BTC", "ETH", "POOLED"]:
    for p in ["FULL", "OOS30"]:
        for s, lab in [("L106", "رئيسية: buffer 10%، مع تكاليف"), ("L106_nobuf", "حساسية: بلا buffer (تداول يومي)"), ("L106_gross", "حساسية: buffer 10%، **بلا** تكاليف")]:
            r = row(s, g, p); rows.append([g, PN[p], lab, triple(r, "port_"), f"{r.turnover_yr:.2f}×", pc(r.cost_sum, 2, False), int(r.n)])
o.append(table(["الأصل", "الفترة", "النسخة", "عائد / Max DD / Sharpe", "turnover/yr", "تكاليف مجمّعة", "#حلقات"], rows) + "\n")
o.append("### 10.6 L-101 BTC intraday seasonality (دخول 22:00 UTC، خروج 00:00 UTC)\n")
o.append("**القاعدة المسبقة — BTC (الورقة)، ثم ETH (متانة خارج الورقة، موسوم)** — مستوى الصفقة، net بعد التكاليف:\n")
o.append(trade_tbl("L101", ["BTC", "ETH"]) + "\n")
rows = []
for g in ["BTC", "ETH"]:
    for p in PER:
        r = row("L101", g, p)
        rows.append([g, PN[p], int(r.n), pc(r.gross_avg_trade, 3), pc(r.avg_trade, 3), pc(r.avg_cost_per_rt, 2, False), f"{r.trades_per_yr:.0f}", pc(r.avg_cost_per_rt*r.trades_per_yr, 0, False), f2(r.gross_profit_factor), f2(r.profit_factor),
                     f"{pcb(r.gross_port_ret)} → {pcb(r.port_ret)}", f"{r.gross_port_sharpe:.2f} → {r.port_sharpe:.2f}", pc(r.port_maxdd), f"{pcb(r.bh_ret)} / {r.bh_sharpe:.2f}"])
o.append("**أثر التكاليف (gross → net)** — ما تدمّره التكاليف. Sharpe من العوائد اليومية للاستراتيجية (0 في الأيام الخارجية):\n")
o.append(table(["الأصل", "الفترة", "#", "متوسط gross/صفقة", "متوسط net/صفقة", "تكلفة/دورة", "دورات/سنة", "تكلفة سنوية (حسابي ≈)", "PF gross", "PF net", "عائد مركّب gross → net", "Sharpe gross → net", "Max DD (net)", "B&H: عائد / Sharpe"], rows) + "\n")
o.append("**اختبار ثانوي موسوم: أفضل نافذة ساعتين اختيرت على أول 70% فقط ثم طُبقت دون تغيير على آخر 30%** (تحيّز انتقاء داخل العينة؛ ليست القاعدة المسبقة):\n")
rows = []
for g in ["BTC", "ETH"]:
    for p in PER:
        r = row("L101_ISsel", g, p)
        rows.append([g, f"{int(r.start_hour)}:00→{(int(r.start_hour)+2)%24:02d}:00", PN[p], int(r.n), pc(r.win_rate, 1, False), f2(r.gross_profit_factor), f2(r.profit_factor), pc(r.gross_avg_trade, 3), pc(r.avg_trade, 3), f"[{pc(r.t_lo,2)}, {pc(r.t_hi,2)}]", f"{pcb(r.gross_port_ret)} → {pcb(r.port_ret)}", f"{r.gross_port_sharpe:.2f} → {r.port_sharpe:.2f}"])
o.append(table(["الأصل", "النافذة", "الفترة", "#", "Win rate", "PF gross", "PF net", "متوسط gross", "متوسط net", "95% CI t (net)", "عائد مركّب gross → net", "Sharpe gross → net"], rows) + "\n")
o.append("**حسب السنة** (القاعدة المسبقة 22:00؛ كل سنة: net مركّب = ماذا يحدث لو طُبقت في تلك السنة وحدها؛ 2026 جزئية حتى 2026-10-03؛ 2017 من أغسطس):\n")
rows = []
for a in ["BTC", "ETH"]:
    for _, r in Y[(Y.strat == "L101") & (Y.asset == a)].iterrows():
        rows.append([a, int(r.year), int(r.n), pc(r.win_rate_net, 0, False), pc(r.avg_gross, 3), pc(r.avg_net, 3), pcb(r.cum_gross), pcb(r.cum_net), pcb(r.bh_year)])
o.append(table(["الأصل", "السنة", "#", "Win rate (net)", "متوسط gross", "متوسط net", "مركّب gross", "مركّب net", "B&H السنة"], rows) + "\n")
o.append("**هل 22:00 فعلًا ساعة مميزة؟** متوسط عائد نافذة الساعتين حسب ساعة البداية (gross، قبل التكاليف) على IS70 مقابل OOS30 — أعلى 5 ساعات بداية في IS لكل أصل + صف 22:00:\n")
rows = []
for a in ["BTC", "ETH"]:
    i_ = HP[(HP.asset == a) & (HP.period == "IS70")].set_index("start_hour"); o_ = HP[(HP.asset == a) & (HP.period == "OOS30")].set_index("start_hour")
    hs = list(i_.mean_gross.sort_values(ascending=False).index[:5]); hs += [22] if 22 not in hs else []
    for h in hs:
        rk = int(i_.mean_gross.rank(ascending=False)[h]); rko = int(o_.mean_gross.rank(ascending=False)[h])
        rows.append([a, f"{h}:00→{(h+2)%24:02d}:00", f"{rk}/24", pc(i_.mean_gross[h], 3), pc(i_.mean_net[h], 3), f"{rko}/24", pc(o_.mean_gross[h], 3), pc(o_.mean_net[h], 3)])
o.append(table(["الأصل", "نافذة", "ترتيب IS (gross)", "IS gross", "IS net", "ترتيب OOS (gross)", "OOS gross", "OOS net"], rows) + "\n")
o.append("### 10.7 قراءة النتائج بصدق\n")
b101o = row("L101", "BTC", "OOS30"); b101s = row("L101_ISsel", "BTC", "FULL"); b101so = row("L101_ISsel", "BTC", "OOS30")
_i = HP[(HP.asset=='BTC')&(HP.period=='IS70')].set_index('start_hour').mean_gross.rank(ascending=False); _o = HP[(HP.asset=='BTC')&(HP.period=='OOS30')].set_index('start_hour').mean_gross.rank(ascending=False); rk_is, rk_oos = int(_i[22]), int(_o[22])
yb = Y[(Y.strat == "L101") & (Y.asset == "BTC")]; posg = int((yb.cum_gross > 0).sum()); post = int((yb.cum_net > 0).sum())
o.append(f"- **L-101 (REJECTED):** الأثر الإجمالي (gross) موجود لكنه ضئيل: متوسط {pc(b101.gross_avg_trade,3)} للصفقة على BTC (PF gross {f2(b101.gross_profit_factor)}) مقابل تكلفة دورة ≈ {pc(b101.avg_cost_per_rt,2,False)} ⇒ net {pc(b101.avg_trade,3)} للصفقة. مع ~{b101.trades_per_yr:.0f} دورة سنويًا التكلفة الحسابية ≈ {pc(b101.avg_cost_per_rt*b101.trades_per_yr,0,False)}/سنة، فمحفظة 100% في النافذة يوميًا تفقد {pc(-b101.port_ret,2,False)} من رأس المال على FULL (gross كان {pcb(b101.gross_port_ret)}). (افتراض توضيحي لا نتيجة: حتى بتكلفة دورة 0.04% فقط، أي رسوم 0.02%/جهة بلا انزلاق، فمتوسط gross على BTC FULL {pc(b101.gross_avg_trade,3)} لا يزيد عليها كثيرًا ولا يكفي لهامش أمان.) في OOS30 اختفى الأثر عمليًا: gross {pc(b101o.gross_avg_trade,3)} وPF gross {f2(b101o.gross_profit_factor)}؛ في {posg} من {len(yb)} سنوات فقط كان مركّب gross موجبًا على BTC و{post} سنة بنتيجة net موجبة (انظر الجدول السنوي). ساعة 22:00 نفسها لم تكن الأفضل في بياناتنا: ترتيبها {rk_is}/24 في IS و{rk_oos}/24 في OOS (بالـ gross على BTC)، بينما نافذة 21:00 احتلت المرتبة 1/24 في الفترتين. هذا **لا يثبت** أن الأثر خضع لـ arbitrage، لكنه متسق مع الخطر الرئيسي المذكور (انحسار الموسمية بعد نشرها)؛ وأي أثر متبقٍّ (≤ ~0.1% للصفقة gross في أفضل نافذة) أصغر من تكلفة التنفيذ ~0.30%.\n"
         f"- **الاختبار الثانوي (انتقاء IS):** اختيار أفضل نافذة على IS ({best['BTC']}:00) رفع gross قليلًا (متوسط FULL {pc(b101s.gross_avg_trade,3)}، PF gross {f2(b101s.gross_profit_factor)}؛ OOS30: {pc(b101so.gross_avg_trade,3)}) لكن net يبقى سالبًا ({pc(b101so.avg_trade,3)} في OOS30، CI t {ci2(b101so.t_lo,b101so.t_hi)}). الانتقاء من 24 خيارًا يضخّم IS بطبيعته؛ لا شيء يصمد بعد التكاليف.\n"
         f"- **L-106 (BACKTESTED ضعيف):** النمط المتوقع من trend-following الطويل فقط: يقلّل الـ drawdown بشدة (BTC FULL {pc(b106.port_maxdd)} مقابل {pc(b106.bh_maxdd)} لـ B&H) لأن متوسط التعرض {pc(b106.avg_exposure,0,False)} فقط، وSharpe FULL {b106.port_sharpe:.2f} مقابل {b106.bh_sharpe:.2f}، لكن العائد المطلق أقل بكثير ({pcb(b106.port_ret)} مقابل {pcb(b106.bh_ret)}) — المقارنة العادلة بالـ Sharpe/DD وليس بالعائد (تعرض مختلف). **خارج العينة (آخر 30%) لا تفوق**: BTC Sharpe {b106o.port_sharpe:.2f} مقابل B&H {b106o.bh_sharpe:.2f} (عائد {pc(b106o.port_ret)} مقابل {pc(b106o.bh_ret)})؛ ETH عائد {pc(e106o.port_ret)} وSharpe {e106o.port_sharpe:.2f} مقابل B&H {pc(e106o.bh_ret)} وSharpe {e106o.bh_sharpe:.2f} (أقل خسارة من B&H لكن سالب)؛ حلقات OOS30 مجمّعة: {int(p106o.n)} حلقة، PF {f2(p106o.profit_factor)}، CI {ci(p106o.ci_lo,p106o.ci_hi)} (n صغير جدًا، غير ذي دلالة). الـ buffer: {row('L106_nobuf','BTC','FULL').turnover_yr:.1f}× turnover/سنة بدونه مقابل {b106.turnover_yr:.1f}× معه، وتكاليف مجمّعة {pc(row('L106_nobuf','BTC','FULL').cost_sum,1,False)} مقابل {pc(b106.cost_sum,1,False)} (BTC FULL)؛ Sharpe BTC FULL {row('L106_nobuf','BTC','FULL').port_sharpe:.2f} بلا buffer مقابل {b106.port_sharpe:.2f} — فرق صغير، فاختيار الـ buffer لم يكن حاسمًا هنا. النسخة gross (بلا تكاليف) Sharpe {row('L106_gross','BTC','FULL').port_sharpe:.2f} مقابل {b106.port_sharpe:.2f} net: التكاليف تأكل جزءًا صغيرًا فقط لأن الدوران منخفض؛ ضعف L-106 خارج العينة سببه الإشارة لا التكلفة.\n"
         f"- **L-001:** لا جديد (انظر القسم 9.4): ربح IS ثقيل الذيل يتبخر OOS؛ على BTC+ETH فقط OOS30: PF {f2(l1o.profit_factor)}، متوسط {pc(l1o.avg_trade,2)}، PF بدون أفضل 3 = {f2(l1o.pf_ex_top3)}؛ ETH وحدها PF {f2(row('L001','ETH','OOS30').profit_factor)} في OOS30.\n"
         "- **المقارنة بين الثلاثة:** L-106 وL-001 كلاهما trend-following طويل فقط على نفس الأصول والبيانات ⇒ **ليسا دليلين مستقلين** (إشارتهما مترابطة؛ لم أقس الارتباط). L-101 مختلف (موسمية ضمن اليوم) لكنه خاسر بعد التكاليف.\n"
         "- **تعدد الاختبارات:** هذه 3 استراتيجيات × (BTC/ETH/POOLED) × 5 نوافذ × حساسيات، فوق القسم 9 وS-01..S-03 على **نفس بيانات BTC/ETH** وضمن مكتبة من 115 فكرة تُختبر تباعًا. كل الـ CI **غير مصححة** لتعدد الاختبارات (ولا Deflated Sharpe). فوق ذلك استُعملت 24 مقارنة ساعة بداية في الاختبار الثانوي لـ L-101. أي نتيجة إيجابية هنا تُقرأ بحذر شديد.\n"
         "- **لا شيء يؤهل لـ APPROVED:** OOS < 100 صفقة (حلقات L-106 المجمّعة 11–15 في OOS، وصفقات L-001 المجمّعة 33–41)، لا walk-forward بعد ضبط، لا paper. الحالات: L-001 BACKTESTED (ضعيف)، L-106 BACKTESTED (ضعيف)، L-101 REJECTED.\n")
o.append("### 10.8 القيود والتحيزات (خاصة بهذه الدفعة)\n")
o.append(table(["القيد", "الأثر"], [
 ["حجم L-106 محافظ بحكم التعريف", "الوزن max(0,F)/20 يصل 100% فقط عند F=20 (الحد الأقصى)؛ متوسط التعرض بين ~13% و~25% حسب الأصل والنافذة. هذا اختياري مسبق (لم أُغيّره)؛ استعمال تقلب مستهدف (L-046) أو سلّم تعرض آخر سيغيّر العائد المطلق دون تغيير شكل الإشارة"],
 ["scalars Carver مأخوذة من أدبياته للعقود الآجلة", "هي مضبوطة على أسواق أخرى؛ متوسط |F| الفعلي هنا 8–9 لا 10 بالضبط؛ لم أُعد المعايرة (سيكون ضبطًا). لا FDM"],
 ["حلقات L-106", "لا تعكس الأداء لأن المركز يُبنى ويُخفَّض تدريجيًا؛ PF والـ CI على حلقات 5–22 لا تُستخلص منها دلالة"],
 ["تحقق الورقة (L-101)", "الساعات (22:00 + ساعتان) مأخوذة من وصف Quantpedia الذي يقتبس الورقة، لا من PDF الورقة؛ لم أعد إنتاج نتائج الورقة الأصلية (عيّنتها وتكاليفها مختلفة)"],
 ["نموذج التنفيذ L-101", "افتراض تنفيذ كامل بسعر الافتتاح/الإغلاق مع 0.05% انزلاق. في الواقع سيولة آخر دقائق الساعة وتأثير أمر 100% من الحساب غير مدروسين؛ وتكلفة maker/VIP أقل. لكن حتى gross متوسطه ضئيل"],
 ["بيانات", "Binance spot USDT فقط (لا بيانات دفتر أوامر)؛ فجوات بسبب توقفات المنصة تُتخطى ({gaps} فجوة). الأيام بتوقيت UTC".replace("{gaps}", str(gaps))],
 ["Survivorship / hindsight", "BTC وETH اختيرتا لأنهما الأكبر اليوم؛ العينة تبدأ 2017-2018 (سوق صاعد طويل ⇒ B&H قوي)"],
 ["ترابط", "BTC وETH شديدا الارتباط: لا تُعامل نتائجهما كاختبارين مستقلين"],
 ["نوافذ مختلفة بين L-101 وبقية الاستراتيجيات", "L-101 تبدأ 2017-08-18 بلا إحماء؛ L-001/L-106 تبدأ 2018-03-05. مقارنة أرقام الدورة بين الاستراتيجيات تقريبية"],
]) + "\n")
o.append("### 10.9 التحقق اليدوي والملفات\n")
o.append("**فحوص يدوية من الشموع الخام** (`diagnostics_L2.py` بلا إعادة استعمال لمحرك الباكتيست → `diagnostics_L2_output.txt`):\n\n```\n" + DIAG.strip() + "\n```\n")
o.append("**إعادة التشغيل:** `python3 backtest_L2.py` مرتين ⇒ كل ملفات النتائج متطابقة (md5) والمخرجات النصية متطابقة. جداول هذا القسم مولّدة من الـ CSV بـ `make_report_L2.py` (لا أرقام مكتوبة يدويًا في الجداول).\n")
o.append("**الملفات (مسارات نسبية من مجلد الفريق):** `strategy-lab/fetch_1h.py`، `strategy-lab/data/BTCUSDT_1h.csv`، `strategy-lab/data/ETHUSDT_1h.csv`، `strategy-lab/backtest_L2.py`، `strategy-lab/results_L2.csv`، `strategy-lab/results_L2_L101_by_year.csv`، `strategy-lab/results_L2_L101_hour_profile.csv`، `strategy-lab/trades_L106.csv`، `strategy-lab/trades_L101_BTC.csv` و`trades_L101_ETH.csv` و`trades_L101_ISsel_BTC.csv` و`trades_L101_ISsel_ETH.csv`، `strategy-lab/trades_L001_rerun_BTC_ETH.csv`، `strategy-lab/curve_L106.csv`، `strategy-lab/signals_L106_BTC.csv`، `strategy-lab/run_L2_output.txt`، `strategy-lab/fetch_1h_output.txt`، `strategy-lab/diagnostics_L2.py` + `diagnostics_L2_output.txt`، `strategy-lab/make_report_L2.py`، `strategy-lab/report_section_L2.md`.\n")
open(f"{H}/report_section_L2.md", "w").write("\n".join(o))
reg = [
 f"| L-001 (إعادة تشغيل BTC/ETH، القسم 10.2/10.4) | تشغيل L-001 على BTC+ETH فقط بنفس السكربت والمعاملات لمقارنة مباشرة مع L-106/L-101 — **experimental — paper only** | **BACKTESTED** (ضعيف، بلا تغيير) | تطابق تام مع شريحتي BTC/ETH من القسم 9 ({ntr} صفقة؛ CI فقط يختلف بسبب بذرة bootstrap). BTC+ETH: FULL PF {f2(l1.profit_factor)}؛ OOS30 {int(l1o.n)} صفقة، PF {f2(l1o.profit_factor)}، متوسط {pc(l1o.avg_trade,2)} | نفس تحفظات القسم 9: ذيل ثقيل وOOS < 100 صفقة |",
 f"| L-106 | Carver EWMAC ensemble (8/32…64/256، scalars Carver المنشورة، long-only، وزن = max(0,F)/20، buffer 10%) على BTC/ETH يومي — **experimental — paper only** | **BACKTESTED** (ضعيف) | BTC FULL: Sharpe {b106.port_sharpe:.2f} مقابل B&H {b106.bh_sharpe:.2f}، maxDD {pc(b106.port_maxdd)} مقابل {pc(b106.bh_maxdd)}، عائد {pcb(b106.port_ret)} مقابل {pcb(b106.bh_ret)}؛ OOS30 مجمّعًا: Sharpe {p106o.port_sharpe:.2f} مقابل B&H {p106o.bh_sharpe:.2f} | تعرض متوسط ~{pc(b106.avg_exposure,0,False)}؛ لا تفوق OOS؛ قاعدة الـ100 صفقة لا تنطبق (حجم مستمر) |",
 f"| L-101 | BTC intraday seasonality: long 22:00→00:00 UTC (Padyšák & Vojtko 2022، SSRN 4081000؛ الساعات تحققت عبر Quantpedia) على BTC 1H، وETH كمتانة — **experimental — paper only** | **REJECTED** (بعد التكاليف) | BTC FULL {int(b101.n)} صفقة: gross {pc(b101.gross_avg_trade,3)} → net {pc(b101.avg_trade,3)} للصفقة؛ PF net {f2(b101.profit_factor)}؛ عائد مركّب gross {pcb(b101.gross_port_ret)} → net {pcb(b101.port_ret)}؛ OOS30 gross {pc(b101o.gross_avg_trade,3)} | التكاليف (~0.30%/دورة × 365) تدمّر أثرًا ضئيلًا أصلًا؛ الأثر غالبًا اختفى بعد النشر |",
]
open(f"{H}/registry_rows_L2.md", "w").write("\n".join(reg)+"\n")
print("ok", len("\n".join(o)))
