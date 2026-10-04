# كيف تجيب مفاتيح الـ API

> الأسعار والخطط المجانية تتغير هلبا. شوف صفحة الأسعار في كل موقع قبل ما تشترك.

## الترتيب

1. **ابدأ بالمجاني (الجزء الأول)** — يكفي للـ Paper trading.
2. **المدفوع (الجزء الثاني)** — بس لو النتائج بعد شهر تستاهل.
3. **مفاتيح المنصات (الجزء الثالث)** — آخر حاجة، لما تقرر تتداول بفلوس حقيقية.

---

## 1) مجاني — ابدأ بيهم

| الموقع | يستعمله | كيف تجيب المفتاح | المتغير |
|--------|---------|------------------|---------|
| **Dexscreener** | المحقق، المحلل | ما يحتاجش مفتاح | — |
| **GeckoTerminal** | المحلل | ما يحتاجش مفتاح | — |
| **CoinGecko** | المحقق (عملات الميم) | coingecko.com/en/api ← سجّل ← Developer Dashboard ← أنشئ **Demo** key | `COINGECKO_API_KEY` |
| **Birdeye** | المحقق، المحلل | bds.birdeye.so ← سجّل ← API Keys | `BIRDEYE_API_KEY` |
| **Helius** (Solana) | المحلل، خبير الأمان | dashboard.helius.dev ← سجّل ← الصفحة الرئيسية فيها المفتاح | `HELIUS_API_KEY` |
| **Etherscan** (Ethereum/Base/BNB) | المحلل، خبير الأمان | etherscan.io/register ← My Profile ← API Keys ← Add (مفتاح واحد لعدة سلاسل — شوف أي سلاسل تشملها الخطة المجانية) | `ETHERSCAN_API_KEY` |
| **RugCheck** (Solana) | خبير الأمان | الفحص العام ما يحتاجش مفتاح | — |
| **GoPlus Security** | خبير الأمان | الفحص الأساسي بدون مفتاح؛ للحدود الأعلى: gopluslabs.io ← Developer | `GOPLUS_API_KEY` |
| **CryptoPanic** (أخبار) | القناص | cryptopanic.com/developers/api ← سجّل ← المفتاح يظهر في الصفحة | `CRYPTOPANIC_API_KEY` |
| **Telegram Bot** (تنبيهات لتليفونك) | المدير | في تيليجرام كلّم **@BotFather** ← `/newbot` ← ياخذ التوكن. بعدها ابعت أي رسالة للبوت وافتح `https://api.telegram.org/bot<TOKEN>/getUpdates` باش تلقى `chat.id` | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` |

## 2) مدفوع — اختياري

| الموقع | يستعمله | كيف | ملاحظة |
|--------|---------|-----|--------|
| **X (تويتر) API** | المحقق، القناص | developer.x.com ← Developer Portal ← أنشئ Project + App ← Keys and tokens ← **Bearer Token** | قراءة التغريدات تحتاج خطة مدفوعة وغالية. بدونها الوكلاء يستعملوا البحث العادي |
| **Arkham** | القناص | intel.arkm.com ← اطلب API access | محافظ المشاهير والصناديق مصنّفة |
| **Nansen** | المحقق، القناص، المحلل، خبير الأمان | ✅ موصول كـ Connector في Claude (MCP). في VS Code: سجّل دخول بنفس حساب Claude، أو أضفه بـ `/mcp` | Smart Money، تصنيف المحافظ، تدفقات العملات |
| **Whale Alert** | القناص | whale-alert.io ← API ← اشترك | التحويلات الكبيرة لحظياً |

## 3) التنفيذ

### المنصات المركزية (Binance / Bybit / OKX)

نفس الخطوات في الثلاثة:

1. فعّل **2FA** على الحساب قبل أي حاجة.
2. **Binance:** Profile ← API Management ← Create API ← System generated.
   **Bybit:** Profile ← API ← Create New Key ← System-generated.
   **OKX:** Profile ← API ← Create V5 API key (وحط Passphrase).
   **KuCoin:** API Management ← Create API ← API-Based Trading (وحط Passphrase، 7–32 حرف بدون فراغات).
   **Gate:** API Key Management ← Create API Key ← API v4 Key ← Trading Account ← Spot Trading: Read And Write بس.
3. الصلاحيات: ✅ **Read** + ✅ **Spot Trading** فقط.
   ❌ **Withdrawals — ممنوع تفعّله أبداً.** ❌ Futures/Margin.
4. **IP restriction:** حط IP الجهاز اللي يشغّل الفريق.
5. الـ Secret يظهر مرة وحدة — حطه في `.env` مباشرة.

### المنصات اللامركزية (Jupiter / 1inch / 0x)

| الموقع | كيف | المتغير |
|--------|-----|---------|
| Jupiter (Solana) | portal.jup.ag ← سجّل ← API Keys | `JUPITER_API_KEY` |
| 1inch (Base/BNB) | portal.1inch.dev ← سجّل ← API Keys | `ONEINCH_API_KEY` |
| 0x (Base/BNB) | dashboard.0x.org ← سجّل ← Apps ← API key | `ZEROX_API_KEY` |

هذي المفاتيح تجيب **الأسعار والمسار** بس. **التوقيع على الصفقة يكون منك انت في محفظتك (Phantom / MetaMask / Rabby).** عمرك ما تعطي الـ private key أو الـ seed phrase لأي وكيل.

---

## كيف تحطهم

```bash
cd crypto-trading-team
cp .env.example .env        # .env محمي في .gitignore وما يترفعش لـ GitHub
nano .env                   # عبّي المفاتيح
set -a; source .env; set +a
claude
```

الوكلاء يقروا المفاتيح من المتغيرات، وما يكتبوهاش في أي ملف ولا تقرير. أي مفتاح فاضي، الوكيل يرجع للبحث العادي ويقولك.

## لو مفتاح تسرّب

احذفه فوراً من الموقع واعمل واحد جديد. في المنصات المركزية: احذف المفتاح، وغيّر كلمة السر، وراجع آخر العمليات.
