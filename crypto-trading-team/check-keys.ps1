# Health check for every API key in .env — read-only, never places orders, never prints key values.
# Run from this folder:  powershell -ExecutionPolicy Bypass -File .\check-keys.ps1

$ErrorActionPreference = 'Stop'
$e = @{}
Get-Content (Join-Path $PSScriptRoot '.env') | Where-Object { $_ -match '^[A-Z_]+=' } | ForEach-Object {
    $k, $v = $_ -split '=', 2; $e[$k] = $v.Trim().Trim('"').Trim("'")
}
$results = New-Object System.Collections.Generic.List[object]
function Add($area, $name, $ok, $detail) { $results.Add([pscustomobject]@{ Area = $area; Service = $name; OK = $(if ($ok) { 'OK' } else { 'FAIL' }); Detail = $detail }) }
function Err($x) { $m = $x.ErrorDetails.Message; if (-not $m) { $m = $x.Exception.Message }; ($m -replace '\s+', ' ').Substring(0, [Math]::Min(110, ($m -replace '\s+', ' ').Length)) }
function HmacBytes($alg, $secret, $msg) { $h = if ($alg -eq 512) { New-Object Security.Cryptography.HMACSHA512 } else { New-Object Security.Cryptography.HMACSHA256 }; $h.Key = [Text.Encoding]::UTF8.GetBytes($secret); $h.ComputeHash([Text.Encoding]::UTF8.GetBytes($msg)) }
function Hex($b) { ($b | ForEach-Object { $_.ToString('x2') }) -join '' }

$ip = try { Invoke-RestMethod 'https://api.ipify.org' -TimeoutSec 10 } catch { '?' }

# --- Data ---
try { $r = Invoke-WebRequest -UseBasicParsing 'https://api.coingecko.com/api/v3/ping' -Headers @{ 'x-cg-demo-api-key' = $e['COINGECKO_API_KEY'] }; Add 'Data' 'CoinGecko' $true 'key accepted' } catch { Add 'Data' 'CoinGecko' $false (Err $_) }
try { $r = Invoke-RestMethod -Method Post "https://mainnet.helius-rpc.com/?api-key=$($e['HELIUS_API_KEY'])" -ContentType 'application/json' -Body '{"jsonrpc":"2.0","id":1,"method":"getHealth"}'; Add 'Data' 'Helius (Solana)' ($r.result -eq 'ok') "health=$($r.result)" } catch { Add 'Data' 'Helius (Solana)' $false (Err $_) }
try { $r = Invoke-RestMethod "https://api.etherscan.io/v2/api?chainid=1&module=proxy&action=eth_blockNumber&apikey=$($e['ETHERSCAN_API_KEY'])"; Add 'Data' 'Etherscan (Ethereum)' ($r.result -match '^0x') 'Ethereum only on free plan' } catch { Add 'Data' 'Etherscan (Ethereum)' $false (Err $_) }
$alchemyNets = [ordered]@{ 'eth-mainnet' = 'eth_blockNumber'; 'base-mainnet' = 'eth_blockNumber'; 'bnb-mainnet' = 'eth_blockNumber'; 'solana-mainnet' = 'getSlot' }
foreach ($n in $alchemyNets.GetEnumerator()) {
    try { $r = Invoke-RestMethod -Method Post "https://$($n.Key).g.alchemy.com/v2/$($e['ALCHEMY_API_KEY'])" -ContentType 'application/json' -Body (@{ jsonrpc = '2.0'; id = 1; method = $n.Value; params = @() } | ConvertTo-Json); Add 'Data' "Alchemy $($n.Key)" (-not $r.error) $(if ($r.error) { $r.error.message } else { 'ok' }) } catch { Add 'Data' "Alchemy $($n.Key)" $false (Err $_) }
}
try { $r = Invoke-WebRequest -UseBasicParsing -Method Post 'https://api.nansen.ai/api/v1/smart-money/netflow' -Headers @{ apiKey = $e['NANSEN_API_KEY'] } -ContentType 'application/json' -Body '{"chains":["ethereum"],"pagination":{"page":1,"per_page":1}}'; Add 'Data' 'Nansen' $true 'smart-money data (uses credits)' } catch { Add 'Data' 'Nansen' $false (Err $_) }
if ($e['X_BEARER_TOKEN']) { try { $r = Invoke-RestMethod 'https://api.x.com/2/tweets/search/recent?query=bitcoin&max_results=10' -Headers @{ Authorization = "Bearer $($e['X_BEARER_TOKEN'])" }; Add 'Data' 'X (Twitter)' $true "read $(@($r.data).Count) posts" } catch { Add 'Data' 'X (Twitter)' $false (Err $_) } }

# --- Alerts ---
try { $r = Invoke-RestMethod "https://api.telegram.org/bot$($e['TELEGRAM_BOT_TOKEN'])/getMe"; Add 'Alerts' 'Telegram bot' ($r.ok -and $e['TELEGRAM_CHAT_ID']) "@$($r.result.username), chat id $(if ($e['TELEGRAM_CHAT_ID']) { 'set' } else { 'MISSING' })" } catch { Add 'Alerts' 'Telegram bot' $false (Err $_) }

# --- Exchanges (permissions only) ---
try {
    $srv = (Invoke-RestMethod 'https://api.binance.com/api/v3/time').serverTime; $q = "timestamp=$srv&recvWindow=10000"
    $r = Invoke-RestMethod "https://api.binance.com/sapi/v1/account/apiRestrictions?$q&signature=$(Hex (HmacBytes 256 $e['BINANCE_API_SECRET'] $q))" -Headers @{ 'X-MBX-APIKEY' = $e['BINANCE_API_KEY'] }
    $safe = $r.enableSpotAndMarginTrading -and -not $r.enableWithdrawals -and -not $r.enableFutures -and -not $r.enableMargin -and $r.ipRestrict
    Add 'Exchange' 'Binance' $safe "spot=$($r.enableSpotAndMarginTrading) withdraw=$($r.enableWithdrawals) futures=$($r.enableFutures) ipLock=$($r.ipRestrict)"
} catch { Add 'Exchange' 'Binance' $false (Err $_) }
try {
    $ts = [string][DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds(); $rw = '10000'
    $r = Invoke-RestMethod 'https://api.bybit.com/v5/user/query-api' -Headers @{ 'X-BAPI-API-KEY' = $e['BYBIT_API_KEY']; 'X-BAPI-SIGN' = (Hex (HmacBytes 256 $e['BYBIT_API_SECRET'] ($ts + $e['BYBIT_API_KEY'] + $rw))); 'X-BAPI-TIMESTAMP' = $ts; 'X-BAPI-RECV-WINDOW' = $rw }
    $p = $r.result.permissions; $extra = @($p.PSObject.Properties | Where-Object { $_.Name -ne 'Spot' -and @($_.Value).Count -gt 0 } | ForEach-Object { "$($_.Name):$(@($_.Value) -join '/')" })
    Add 'Exchange' 'Bybit' (($extra.Count -eq 0) -and @($r.result.ips).Count -gt 0 -and $r.result.ips[0] -ne '*') $(if ($extra.Count) { "EXTRA perms: $($extra -join ', ')" } else { "spot only, ipLock=$(@($r.result.ips) -join ',')" })
} catch { Add 'Exchange' 'Bybit' $false (Err $_) }
try {
    $ts = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ss.fffZ'); $path = '/api/v5/account/config'
    $r = Invoke-RestMethod "https://eea.okx.com$path" -Headers @{ 'OK-ACCESS-KEY' = $e['OKX_API_KEY']; 'OK-ACCESS-SIGN' = [Convert]::ToBase64String((HmacBytes 256 $e['OKX_API_SECRET'] ($ts + 'GET' + $path))); 'OK-ACCESS-TIMESTAMP' = $ts; 'OK-ACCESS-PASSPHRASE' = $e['OKX_API_PASSPHRASE'] }
    $d = $r.data[0]; Add 'Exchange' 'OKX (EU)' ($r.code -eq '0' -and $d.perm -notmatch 'withdraw' -and $d.acctLv -eq '1' -and $d.ip) "perm=$($d.perm) spotMode=$($d.acctLv -eq '1') ipLock=$([bool]$d.ip)"
} catch { Add 'Exchange' 'OKX (EU)' $false (Err $_) }
try {
    $ts = [string][DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds(); $path = '/api/v1/user/api-key'
    $r = Invoke-RestMethod "https://api.kucoin.com$path" -Headers @{ 'KC-API-KEY' = $e['KUCOIN_API_KEY']; 'KC-API-SIGN' = [Convert]::ToBase64String((HmacBytes 256 $e['KUCOIN_API_SECRET'] ($ts + 'GET' + $path))); 'KC-API-TIMESTAMP' = $ts; 'KC-API-PASSPHRASE' = [Convert]::ToBase64String((HmacBytes 256 $e['KUCOIN_API_SECRET'] $e['KUCOIN_API_PASSPHRASE'])); 'KC-API-KEY-VERSION' = '2' }
    Add 'Exchange' 'KuCoin' ($r.code -eq '200000' -and $r.data.permission -eq 'General,Spot' -and $r.data.ipWhitelist) "perm=$($r.data.permission) ipLock=$([bool]$r.data.ipWhitelist)"
} catch { Add 'Exchange' 'KuCoin' $false (Err $_) }
try {
    $ts = [string][DateTimeOffset]::UtcNow.ToUnixTimeSeconds(); $bh = Hex ([Security.Cryptography.SHA512]::Create().ComputeHash([byte[]]@()))
    $sig = Hex (HmacBytes 512 $e['GATE_API_SECRET'] "GET`n/api/v4/spot/accounts`n`n$bh`n$ts")
    $null = Invoke-RestMethod 'https://api.gateio.ws/api/v4/spot/accounts' -Headers @{ KEY = $e['GATE_API_KEY']; SIGN = $sig; Timestamp = $ts }
    Add 'Exchange' 'Gate' $true 'spot read ok'
} catch { Add 'Exchange' 'Gate' $false (Err $_) }

"Public IP now: $ip  (must be whitelisted on every exchange)"
$results | Format-Table -AutoSize -Wrap
$bad = @($results | Where-Object OK -eq 'FAIL').Count
if ($bad) { "$bad problem(s) found." } else { 'All checks passed.' }
