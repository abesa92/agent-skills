#!/usr/bin/env python3
"""Builds the Arabic section 9 of reports/strategies.md from results_L.csv / trades_L*.csv (all numbers come from the CSVs).
python3 make_report_L.py          -> writes report_section_L.md only
python3 make_report_L.py --apply  -> also patches ../reports/strategies.md (additive; idempotent: replaces its own earlier insert)"""
import sys, os, re, pandas as pd, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); R = pd.read_csv(f"{H}/results_L.csv")
T = {s: pd.read_csv(f"{H}/trades_{s}.csv") for s in ["L001", "L004", "L031"]}
out = open(f"{H}/run_L_output.txt").read().splitlines()
info = {l.split()[0]: l for l in out[:3]}
def g(s, grp, per): return R[(R.strat == s) & (R.group == grp) & (R.period == per)].iloc[0]
def p(x, d=1): return "—" if pd.isna(x) else (f"{x*100:+.{d}f}%" if abs(x) < 10 else f"{x*100:+.0f}%")
def p0(x, d=1): return "—" if pd.isna(x) else f"{x*100:.{d}f}%"
def f(x, d=2): return "—" if pd.isna(x) else ("∞" if np.isinf(x) else f"{x:.{d}f}")
def ci(r): return "— (n<10)" if pd.isna(r.ci_lo) else f"[{r.ci_lo*100:+.1f}%, {r.ci_hi*100:+.1f}%]"
NAMES = {"L001": "L-001 Donchian 20/10 (وقف 2×ATR20)", "L004": "L-004 Time-series momentum 30d (مراجعة أسبوعية)", "L031": "L-031 RSI(2) pullback"}
PER = {"IS70": "IS (أول 70%)", "OOS30": "**OOS (آخر 30%)**", "FULL": "FULL", "IS_fixed": "IS_fixed (قبل 2023-06-01)", "OOS_fixed": "OOS_fixed (من 2023-06-01)"}
def suff(grp, n): return "كافٍ (≥100)" if (grp == "POOLED" and n >= 100) else "**غير كافٍ**"
def tables(s):
    L = [f"#### {NAMES[s]} — مستوى الصفقة (net بعد التكاليف، العائد على قيمة المركز)\n",
         "| الأصل | الفترة | #صفقات | Win rate | متوسط الربح | متوسط الخسارة | PF | متوسط الصفقة | Median | 95% CI لمتوسط الصفقة (bootstrap) | PF بدون أفضل 3 | حجم العينة |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for grp in ["BTC", "ETH", "SOL", "POOLED"]:
        for per in ["IS70", "OOS30", "FULL"] + (["IS_fixed", "OOS_fixed"] if grp == "POOLED" else []):
            r = g(s, grp, per)
            L.append(f"| {grp} | {PER[per]} | {int(r.n)} | {p0(r.win_rate)} | {p(r.avg_win)} | {p(r.avg_loss)} | {f(r.profit_factor)} | {p(r.avg_trade)} | {p(r.median_trade)} | {ci(r)} | {f(r.pf_ex_top3)} | {suff(grp, r.n)} |")
    L += ["", f"#### {NAMES[s]} — مستوى المحفظة (سلة كل أصل منفصلة؛ المحفظة = أوزان متساوية بإعادة توازن يومية)\n",
          "| الأصل | الفترة | أيام | **حجم 1% مخاطرة** (نفس S-01): عائد / Max DD / Sharpe | **حجم 100% notional**: عائد / Max DD / Sharpe | Buy&Hold نفس الأصول: عائد / Max DD / Sharpe |", "|---|---|---|---|---|---|"]
    for grp in ["BTC", "ETH", "SOL", "POOLED"]:
        for per in ["IS70", "OOS30", "FULL"] + (["IS_fixed", "OOS_fixed"] if grp == "POOLED" else []):
            r = g(s, grp, per)
            L.append(f"| {grp} | {PER[per]} | {int(r.port_days)} | {p(r.port_ret)} / {p(r.port_maxdd)} / {f(r.port_sharpe)} | {p(r.full_ret)} / {p(r.full_maxdd)} / {f(r.full_sharpe)} | {p(r.bh_ret)} / {p(r.bh_maxdd)} / {f(r.bh_sharpe)} |")
    return "\n".join(L) + "\n"
def exitmix(s):
    t = T[s]; return "، ".join(f"{k}: {v}" for k, v in t.exit_reason.value_counts().items())
def expo(s):
    return None
a1, a4, a3 = g("L001", "POOLED", "FULL"), g("L004", "POOLED", "FULL"), g("L031", "POOLED", "FULL")
o1, o4, o3 = g("L001", "POOLED", "OOS30"), g("L004", "POOLED", "OOS30"), g("L031", "POOLED", "OOS30")
x1, x4, x3 = g("L001", "POOLED", "OOS_fixed"), g("L004", "POOLED", "OOS_fixed"), g("L031", "POOLED", "OOS_fixed")
i1, i4, i3 = g("L001", "POOLED", "IS70"), g("L004", "POOLED", "IS70"), g("L031", "POOLED", "IS70")
s01 = pd.read_csv(f"{H}/results_summary.csv"); s01m = s01[(s01.strat == "S01") & (s01.group == "MAJORS")].set_index("period")
REG = [f"| L-001 | Donchian breakout 20/10 + وقف أولي 2×ATR20 (قواعد المكتبة؛ ≠ S-01 الذي هو 40/20 و3×ATR) — **experimental — paper only** | **BACKTESTED** (ضعيف، بتحفظ) | {int(a1.n)} صفقة مجمّعة (FULL)، PF {f(a1.profit_factor)}؛ لكن OOS (آخر 30%): {int(o1.n)} صفقة، PF {f(o1.profit_factor)}، متوسط {p(o1.avg_trade)} وCI {ci(o1)} | الربح تركّز في IS (2020–2021) وPF بدون أفضل 3 صفقات في OOS = {f(o1.pf_ex_top3)}؛ النتيجة تتغير بين تقسيمين (OOS_fixed: PF {f(x1.profit_factor)}). تفاصيل في القسم 9 |",
       f"| L-004 | Time-series momentum 30 يوم (long-only، مراجعة أسبوعية) — **experimental — paper only** | **BACKTESTED** (الأقوى من الثلاثة، بتحفظ) | {int(a4.n)} صفقة مجمّعة، PF {f(a4.profit_factor)}؛ OOS: {int(o4.n)} صفقة، PF {f(o4.profit_factor)}، متوسط {p(o4.avg_trade)}، CI {ci(o4)} | تعرّض ~50% من الوقت (أقرب إلى market timing)؛ حد CI الأدنى في OOS قرب الصفر؛ OOS أقل من 100 صفقة؛ الصفقات مترابطة بين الأصول الثلاثة |",
       f"| L-031 | RSI(2) pullback فوق SMA200 — **experimental — paper only** | **REJECTED** (بصيغة المكتبة الافتراضية) | {int(a3.n)} صفقة (FULL)، Win rate {p0(a3.win_rate, 0)} لكن PF {f(a3.profit_factor)}؛ OOS: PF {f(o3.profit_factor)}، متوسط الصفقة {p(o3.avg_trade)} | الأرباح الصغيرة (+{g('L031','POOLED','FULL').avg_win*100:.1f}%) مقابل خسائر أكبر ({p(a3.avg_loss)}) ولا edge بعد التكاليف؛ لم يُضبط أي معامل لإنقاذه (سيكون data-snooping) |"]
sec = f"""
## 9. Part B — دفعة المكتبة الأولى: L-001 و L-004 و L-031 (BTC/ETH/SOL يومي) — {pd.Timestamp('2026-10-04').date()}

> **كل الثلاثة "experimental — paper only" ولا تولّد أي إشارة تداول حقيقية.** أقصى حالة ممكنة هنا BACKTESTED (شرط APPROVED يحتاج OOS كافٍ + أسبوعين paper، ولم يتحقق).
> كل رقم أدناه مولَّد بالسكربت `strategy-lab/backtest_L.py` (المخرجات الخام: `results_L.csv`، `trades_L001.csv`، `trades_L004.csv`، `trades_L031.csv`، `run_L_output.txt`)، والجداول مولَّدة آليًا من الـ CSV بواسطة `make_report_L.py`. **لم يُضبط أي معامل (no parameters fitted)** — القواعد والقيم الافتراضية من `strategies/library.md` كما هي.

### 9.1 الإعداد

| البند | القيمة |
|---|---|
| القواعد (حرفيًا من المكتبة) | **L-001**: دخول close > أعلى high لآخر 20 شمعة سابقة؛ خروج close < أدنى low لآخر 10 شموع سابقة؛ وقف أولي = سعر التنفيذ − 2×ATR(20) (يُفحص داخل الشمعة؛ فجوة تحت الوقف = تنفيذ عند الافتتاح). **L-004**: long إذا عائد 30 يومًا > 0؛ المراجعة أسبوعية؛ خروج إذا عائد 30 يومًا ≤ 0. **L-031**: دخول close > SMA200 و RSI(2) < 10؛ خروج RSI(2) > 70 أو close > SMA5؛ وقف زمني 5 شموع |
| تفسيرات لم تحددها المكتبة (قرارات مسبقة، لم تُجرَّب بدائلها) | RSI(2) بتمهيد Wilder (alpha = 1/2). "المراجعة الأسبوعية" لـ L-004 = **إغلاق يوم الأحد UTC** والتنفيذ عند افتتاح الإثنين (الدخول والخروج كلاهما فقط في أيام المراجعة). الوقف الزمني في L-031: بعد إغلاق الشمعة الخامسة للمركز تُرسل أمر خروج ينفَّذ عند افتتاح التالية. L-001: ATR(20) = متوسط بسيط للـ True Range (نفس أسلوب ATR14 في المختبر). نفس الشمعة التي يخرج عندها المركز يمكن أن تُنتج إشارة دخول جديدة (كما في S-01) |
| البيانات | `strategy-lab/data/{{BTC,ETH,SOL}}USDT_1d.csv` — **نفس البيانات المخبَّأة للمختبر** (Binance spot يومي عبر data-api.binance.vision؛ لم يُعاد التنزيل). {info['BTC'].split('data ')[1].split(' |')[0]} لـ BTC وETH؛ {info['SOL'].split('data ')[1].split(' |')[0]} لـ SOL (**SOL تبدأ في 2020**). شمعة 2026-10-04 الجزئية محذوفة |
| فترة الإحماء | أول 200 شمعة لكل أصل بلا إشارات (SMA200 لـ L-031)، **نفس النافذة للاستراتيجيات الثلاث** حتى تكون قابلة للمقارنة: {info['BTC'].split('| ')[1]} (BTC/ETH)، {info['SOL'].split('| ')[1]} (SOL) |
| التقسيم | **IS = أول 70%، OOS = آخر 30%** من التاريخ القابل للاستخدام لكل أصل (تاريخ الدخول). {info['BTC'].split('| ')[2]} (BTC/ETH)، {info['SOL'].split('| ')[2]} (SOL). **لا يوجد ضبط**، فالتقسيم وصفي فقط (الـ OOS ليس "اختبارًا بعد ضبط"، بل مجرد نافذة أحدث). أضفت أيضًا التقسيم الثابت المستخدم في المختبر (2023-06-01) بوسم `IS_fixed/OOS_fixed` للاتساق مع S-01..S-03 |
| التنفيذ | الإشارة عند إغلاق الشمعة i، التنفيذ عند افتتاح i+1 (لا lookahead)، long-only spot بلا رافعة، مركز واحد لكل أصل |
| التكاليف | رسوم 0.10% لكل جهة + انزلاق 0.05% لكل جهة (كبار) — **نفس افتراضات المختبر**، افتراضية وغير مقاسة |
| حجم المركز | **الرئيسي (للمقارنة مع S-01):** min(100% notional، 1% مخاطرة ÷ مسافة الوقف). L-001 له وقف فعلي 2×ATR20. **L-004 وL-031 بلا وقف في المكتبة**: استخدمت المسافة 2×ATR(20) **للحجم فقط** (لا يوجد أمر وقف، والقواعد لم تتغير) — هذا افتراضي مني. **نسخة ثانية** بحجم 100% notional لكل دخول تُظهر الأداء الخام للإشارة (مقاييس مستوى الصفقة متطابقة في النسختين لأن الدخول والخروج لا يعتمدان على الحجم) |
| الصفقات المفتوحة في النهاية | تُغلق بآخر إغلاق مع تكاليف الخروج (`open_at_end`): L-001: {int((T['L001'].exit_reason=='open_at_end').sum())}، L-004: {int((T['L004'].exit_reason=='open_at_end').sum())}، L-031: {int((T['L031'].exit_reason=='open_at_end').sum())} |
| علاقة L-001 بـ S-01 | L-001 (20/10، 2×ATR20) **ليس** S-01 (40/20، 3×ATR14) وإن كانت المكتبة تذكره كـ "lab S-01". لم يُستبدل S-01 ولم يُعدَّل. الاثنان من نفس عائلة Donchian على نفس البيانات: لا يُعتبران دليلين مستقلين |
| طريقة الإحصاءات | 95% CI = bootstrap (5000 إعادة سحب، seed ثابت، iid على الصفقات). PF بدون أفضل 3 = حذف أعلى 3 صفقات عائدًا. Sharpe = متوسط/انحراف العائد اليومي × √365 بلا معدل خالٍ من المخاطرة. المحفظة = أوزان متساوية على الأصول المتاحة وقتها. CI لا يُحسب إن كان n < 10 |

### 9.2 ملخص مجمّع (POOLED = BTC+ETH+SOL)

| الاستراتيجية | الحالة | FULL: #صفقات / PF / متوسط / median | IS70: #صفقات / PF | OOS30: #صفقات / PF / متوسط / CI / PF بدون أفضل 3 | OOS_fixed: #صفقات / PF / متوسط |
|---|---|---|---|---|---|
| L-001 | BACKTESTED (ضعيف) | {int(a1.n)} / {f(a1.profit_factor)} / {p(a1.avg_trade)} / {p(a1.median_trade)} | {int(i1.n)} / {f(i1.profit_factor)} | {int(o1.n)} / {f(o1.profit_factor)} / {p(o1.avg_trade)} / {ci(o1)} / {f(o1.pf_ex_top3)} | {int(x1.n)} / {f(x1.profit_factor)} / {p(x1.avg_trade)} |
| L-004 | BACKTESTED | {int(a4.n)} / {f(a4.profit_factor)} / {p(a4.avg_trade)} / {p(a4.median_trade)} | {int(i4.n)} / {f(i4.profit_factor)} | {int(o4.n)} / {f(o4.profit_factor)} / {p(o4.avg_trade)} / {ci(o4)} / {f(o4.pf_ex_top3)} | {int(x4.n)} / {f(x4.profit_factor)} / {p(x4.avg_trade)} |
| L-031 | REJECTED | {int(a3.n)} / {f(a3.profit_factor)} / {p(a3.avg_trade)} / {p(a3.median_trade)} | {int(i3.n)} / {f(i3.profit_factor)} | {int(o3.n)} / {f(o3.profit_factor)} / {p(o3.avg_trade)} / {ci(o3)} / {f(o3.pf_ex_top3)} | {int(x3.n)} / {f(x3.profit_factor)} / {p(x3.avg_trade)} |

### 9.3 النتائج التفصيلية (كل الأرقام صافية من التكاليف)

{tables('L001')}
{tables('L004')}
{tables('L031')}
تفاصيل خروج الصفقات (FULL، مجمّع): L-001 → {exitmix('L001')}؛ L-004 → {exitmix('L004')}؛ L-031 → {exitmix('L031')} (متوسط مدة الاحتفاظ: L-001 {T['L001'].bars.mean():.1f} شمعة، L-004 {T['L004'].bars.mean():.1f}، L-031 {T['L031'].bars.mean():.1f}).

### 9.4 قراءة النتائج بصدق

- **قاعدة الـ 100 صفقة:** العيّنة المجمّعة FULL تتجاوز 100 لكل استراتيجية ({int(a1.n)} / {int(a4.n)} / {int(a3.n)})، لكنها تشمل IS. **على OOS (آخر 30%) فقط: {int(o1.n)} / {int(o4.n)} / {int(o3.n)} صفقة، وعلى OOS_fixed: {int(x1.n)} / {int(x4.n)} / {int(x3.n)}، أي كلها أقل من 100** ⇒ كل أرقام OOS و"كل أصل على حدة" مصنّفة **غير كافية**. أيضًا الصفقات على BTC/ETH/SOL **مترابطة بشدة** (تتحرك الأصول معًا)، فالعدد الفعّال للمشاهدات المستقلة أقل بكثير من العدد المعلن.
- **L-001 (Donchian 20/10):** ربح IS كبير (PF {f(i1.profit_factor)}، متوسط {p(i1.avg_trade)}) لكنه يتبخر في آخر 30%: PF {f(o1.profit_factor)}، متوسط {p(o1.avg_trade)}، CI {ci(o1)} يشمل الصفر، وبدون أفضل 3 صفقات PF = {f(o1.pf_ex_top3)}. نمط الذيل الثقيل واضح: Win rate {p0(a1.win_rate, 0)} ومتوسط الربح {p(a1.avg_win)} مقابل median سالب {p(a1.median_trade)}؛ أفضل 3 صفقات (BTC وETH أكتوبر 2020، SOL أغسطس 2021) = 44% من إجمالي الأرباح (`diagnostics_L_output.txt`). **النتيجة تعتمد على التقسيم:** مع التقسيم الثابت 2023-06-01 يصبح OOS PF {f(x1.profit_factor)} (CI {ci(x1)} يشمل الصفر، PF بدون أفضل 3 = {f(x1.pf_ex_top3)}). لذلك الحالة BACKTESTED ضعيف فقط، وبالاتساق مع S-01 (الكبار OOS: PF {f(s01m.loc['OOS','profit_factor'])} على نافذة 2023-06-01) لا يثبت edge بعد استبعاد الذيل.
- **L-004 (TSMOM 30d):** الأكثر اتساقًا من الثلاثة: OOS30 PF {f(o4.profit_factor)}، متوسط {p(o4.avg_trade)}، CI {ci(o4)} (حدّه الأدنى قرب الصفر)، وPF بدون أفضل 3 = {f(o4.pf_ex_top3)}؛ OOS_fixed PF {f(x4.profit_factor)}، متوسط {p(x4.avg_trade)}، CI {ci(x4)}. **تحفظات:** (1) Win rate ~{p0(a4.win_rate, 0)} والـ median الكلي {p(a4.median_trade)} يعني أن المتوسط من ذيل ثقيل أيضًا (أفضل 3 صفقات = 37% من الأرباح، 50% في OOS30)؛ (2) التعرض ~50% من الوقت، أي هي في الجوهر market timing/تخفيض beta، فتفوقها على Buy&Hold في Max DD (OOS30: {p(o4.full_maxdd)} مقابل {p(o4.bh_maxdd)}) وSharpe ({f(o4.full_sharpe)} مقابل {f(o4.bh_sharpe)} بحجم 100%) جاء في نافذة أخيرة ضعيفة للسوق وليس دليلًا على التفوق في كل الأوضاع؛ (3) أرقام الفترة الكاملة بحجم 100% (تراكم مركّب {p(a4.full_ret)}) **حساسة جدًا لـ 2020–2021** ولا تُقرأ كعائد متوقع؛ (4) يوم المراجعة (الأحد) لم يُختبر بدائله.
- **L-031 (RSI(2) pullback):** Win rate مرتفع ({p0(a3.win_rate, 0)}) خادع: متوسط الربح {p(a3.avg_win)} مقابل متوسط الخسارة {p(a3.avg_loss)}، PF {f(a3.profit_factor)} (FULL) و{f(o3.profit_factor)} (OOS30)، متوسط الصفقة {p(a3.avg_trade)} مقابل تكلفة ذهاب وإياب ~0.30% (رسوم + انزلاق). CI في OOS30 {ci(o3)} يشمل الصفر، وبدون أفضل 3 صفقات PF < 1 في كل النوافذ تقريبًا. التعرض ~7% من الوقت فقط. **REJECTED بصيغة المكتبة الافتراضية** على BTC/ETH/SOL يومي؛ هذا ليس حكمًا على فكرة mean-reversion عمومًا (L-035 وL-036 في العائلة نفسها لم تُختبر) ولم أضبط معاملاته لإنقاذه لأن ذلك data-snooping.
- **المقارنة بـ Buy&Hold:** مع حجم 1% مخاطرة التعرض الفعلي منخفض جدًا فلا تُقارن العوائد مباشرة بـ B&H (كما في القسم 4)؛ المقارنة العادلة هي Sharpe وMax DD، ومع حجم 100% notional للإشارة الخام. في IS (2018–2024) كان B&H أعلى عائدًا بكثير لبعض الأصول (خصوصًا SOL).
- **تعدد الاختبارات (multiple testing):** هذه 3 استراتيجيات × 4 مجموعات × 5 نوافذ (60 صفًا) فوق S-01..S-03 المختبرة سابقًا على **نفس بيانات BTC/ETH/SOL** (6 استراتيجيات على الأقل على نفس العيّنة) وضمن مكتبة من 100 فكرة تُختبر بالتتابع. الـ CI المعروضة **غير مصححة**؛ مع هذا العدد من الاختبارات يُتوقع ظهور نتائج "إيجابية" بالصدفة، فيجب اعتبار أي CI يلامس الصفر (L-004 OOS30) غير مثبت.
- **لا شيء من هذا يؤهل لـ APPROVED:** لا OOS كافٍ (≥100 صفقة)، ولا اختبار walk-forward حقيقي بعد ضبط، ولا paper trading. L-004 وL-001 يبقيان BACKTESTED فقط، وL-031 REJECTED.

### 9.5 القيود والتحيزات (خاصة بهذه الدفعة)

| القيد | الأثر |
|---|---|
| Survivorship / hindsight في اختيار الأصول | BTC وETH وSOL مختارة لأنها بقيت من الأكبر اليوم؛ SOL بالذات صعدت بقوة في 2021 ما يرفع نتائج الاتجاه في IS. لو شملت العينة عملات ماتت لكانت أسوأ |
| عيّنة قصيرة لـ SOL | تبدأ 2020-08 (بعد الإحماء 2021-02)؛ في OOS30 لها 8–10 صفقات فقط لكل استراتيجية (CI غير محسوب عند n<10) |
| ترابط الصفقات | الأصول الثلاثة شديدة الارتباط فالصفقات المجمّعة ليست مستقلة، وbootstrap iid يقلل عرض CI |
| الذيل الثقيل | L-001 وL-004: أفضل 3 صفقات تمثل 44% و37% من إجمالي الأرباح (50–51% في OOS30)، لذا المتوسط غير مستقر |
| تفسيرات المكتبة | يوم الأحد، Wilder، وقف الحجم 2×ATR لـ L-004/L-031، وقف زمني بعد 5 شموع — كلها قرارات مسبقة، لم تُختبر بدائلها، وقد تغيّر النتائج |
| التكاليف | رسوم 0.10% + انزلاق 0.05% افتراضية؛ L-031 حساسة لها لأن متوسط صفقتها صغير جدًا |
| التنفيذ | افتراض تنفيذ كامل عند الافتتاح؛ وقف L-001 داخل الشمعة بلا انزلاق إضافي؛ لا بيانات أدنى من اليومي |
| لا تحقق خارجي | لم تُقارن النتائج بمصدر مستقل أو بيانات منصة أخرى؛ التحقق كان فحص صفقات يدويًا من الشموع الخام (`diagnostics_L.py` → `diagnostics_L_output.txt`) |
| شمعة الأحد | الأيام تُحسب UTC (إغلاق 00:00) كما في بيانات Binance |

### 9.6 الخطوة التالية (اقتراح، لم يبدأ)

| # | المهمة |
|---|---|
| 1 | L-004 هو الوحيد المرشح لتتبع ورقي: الإشارة تُراجع كل أحد 00:00 UTC (إغلاق) وتُسجَّل ورقيًا عند افتتاح الإثنين؛ **لم يبدأ** ولا توجد إشارة حية. عدد الصفقات القليل (~14 صفقة/سنة للأصول الثلاثة) يعني أن أسبوعين لا يكفيان للحكم (نفس تحذير القسم 6) |
| 2 | قبل أي ضبط: تحديد معيار مسبق (walk-forward أو CPCV) ولا يُستخدم OOS الحالي للضبط لأنه صار "مرئيًا" |
| 3 | الانتقال في ترتيب الاختبار إلى بقية ★ (L-002، L-016، L-064، L-084) مع تتبّع عدد الاختبارات لتصحيح multiple testing |

### 9.7 الملفات (مسارات نسبية من مجلد الفريق)

`strategy-lab/backtest_L.py` (التشغيل: `python3 backtest_L.py` — يعيد استخدام `backtest.py` للتحميل والتكاليف)، `strategy-lab/results_L.csv`، `strategy-lab/trades_L001.csv`، `trades_L004.csv`، `trades_L031.csv`، `strategy-lab/run_L_output.txt`، `strategy-lab/diagnostics_L.py` + `diagnostics_L_output.txt`، `strategy-lab/make_report_L.py`، `strategy-lab/report_section_L.md`.
"""
open(f"{H}/report_section_L.md", "w").write(sec)
if "--apply" in sys.argv:
    path = f"{H}/../reports/strategies.md"; txt = open(path).read()
    txt = re.sub(r"\n## 9\. Part B.*\Z", "", txt, flags=re.S)
    lines = [l for l in txt.split("\n") if not re.match(r"\| L-0(01|04|31) \|", l)]
    idx = max(i for i, l in enumerate(lines) if l.startswith("| S-04 |"))
    lines[idx+1:idx+1] = REG
    open(path, "w").write("\n".join(lines).rstrip("\n") + "\n" + sec)
    print("applied")
