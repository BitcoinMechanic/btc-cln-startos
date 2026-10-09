# Core Lightning

## Swapping with 0060

After the packaging-VM script reports READY, install BTC 26.6.9:7, XBT 0.1.0:25
and Swap Controller 0.1.0:22. Keep your saved pairing, inspection credentials and
grants. This update does not require grant renewal or a new test payment.
Finish any active swap before updating the installed services.

In **Swap Controller → Swaps**, open **Swap Status** to check connections,
remaining grant slots, expiry and any setup problem. It is read-only. A ready
status means you can check an invoice; it does not guarantee a usable route.
Then use the actions for the direction you want:

- **New BTC to XBT Swap** → **Confirm BTC to XBT Swap** → pay the BTC invoice.
  Check **BTC to XBT Swap History** and the XBT recipient receipt.
- **New XBT to BTC Swap** → **Confirm XBT to BTC Swap** → pay the XBT invoice.
  Check **XBT to BTC Swap History** and the BTC recipient receipt.

The fixed prices remain 1,000 BTC sats → 2,000 XBT sats and 3,000 XBT sats →
1,500 BTC sats. Payer routing fees are additional. Use a fresh recipient invoice
with at least 33 minutes remaining and final CLTV at most 40. Include private
routing hints where needed. Review the recipient, amounts and route fee before
confirming. Only an unapproved draft can be cancelled.

**Swap Setup** contains node pairing, inspection credentials, **Pair BTC to XBT
Grants** and **Pair XBT to BTC Grants**. On each coordinator, **Swap Grants**
contains **Enable BTC to XBT Grant**, **Enable XBT to BTC Grant** and each
direction's pause control. Keep replacement off to retrieve a grant using its
original settings. Expiry or pause stops new enrollment while already enrolled
swaps retain recovery rights. Explicitly replace grants only after existing
swaps finish; this update does not widen an old grant or replenish its slots.

The controller normally shows 15 actions. Regtest and old pilot-creation tools
are hidden from the menu. **Legacy Pilot Status** and its approval action appear
if an older record exists. Legacy quote/recovery inspection appears when its
records exist. **Advanced / Recovery → Worker Status** remains available.
Coordinator single-pilot authorization is retained under **Advanced / Legacy**
for an older reviewed contract. Current direct swaps still work through the
normal swap actions and existing direct grants.

If an action reports an uncertain response, check Swap Status and that swap's
history. Keep the existing record and let its worker recover the original
attempt. Do not pay a second time because a reply was lost. On-chain recovery
requires separate claim/sweep verification; it is not a settled result.

## Documentation

- [Start9 Bitcoin Guides](https://docs.start9.com/bitcoin-guides/) — connecting wallets and dashboards to a Lightning node on StartOS, and how that node reaches Bitcoin.
- [Core Lightning documentation](https://docs.corelightning.org/docs/) — the upstream operator and developer reference.

## What you get on StartOS

- A **Core Lightning** node (`lightningd`) running mainnet, with an auto-created wallet on first start.
- A **Web UI** (CLN Application) for managing channels, payments, and invoices, with its own password set on first access.
- A **JSON-RPC** interface, a **gRPC** interface, and (when enabled) a **CLNrest** REST interface that publishes a URL containing a pre-generated rune for wallet apps.
- An optional **Clams Websocket** endpoint for Clams Remote.
- A bundled set of plugins built into the image: **CLBOSS** (automated channel management), **Sling** (channel rebalancing), and **TEOS** for watchtower client and server functionality.
- A required dependency on **Bitcoin** — install and fully sync Bitcoin first; CLN will not start without it.

## Getting set up

1. Install and fully sync **Bitcoin** if you haven't already.
2. Start Core Lightning. The wallet is created automatically on first start; no seed phrase setup is required.
3. Open the **Web UI** interface and set the UI password on first access. Save this password — it is independent of your StartOS credentials. After 5 wrong passwords within 15 minutes, the Web UI pauses logins for everyone for 15 minutes; restart Core Lightning to clear it sooner.
4. To connect a wallet app or other client, run the **Create Rune** action to generate an unrestricted rune, or use the rune embedded in the **CLNrest** interface URL.

## Using Core Lightning

### Interfaces

- **Web UI** — the CLN Application web dashboard for day-to-day node operation.
- **RPC** — JSON-RPC over HTTP for `lightning-cli` and scripts.
- **Peer** — the Lightning peer-to-peer port; share this address with peers who want to open channels with you.
- **grpc** — the gRPC API for apps and plugins that prefer typed RPC.
- **CLNrest** — REST API. When enabled, the published URL contains the rune wallet apps need to authenticate. The scheme tells wallets like Zeus which protocol to use: `clnrest+http://` for plain-HTTP addresses (use this for Tor onion addresses — Tor already encrypts) and `clnrest+https://` for SSL addresses (LAN/clearnet).
- **Clams Websocket** — websocket endpoint for Clams Remote, shown when the `clams-remote-websocket` option is on.
- **TEOS Watchtower** — present only when the watchtower server is enabled.

### Actions

- **Node Info** — display your node ID and peer URI(s) to share with channel partners.
- **Display BIP-39 Seed** — show the 12-word BIP-39 seed for on-chain recovery. Hidden if your wallet predates BIP-39 support in CLN; the seed alone does not recover channel state.
- **Create Rune** — generate an unrestricted rune for app integrations.
- **Revoke All Runes** — blacklist every rune this node has issued, so none of them can authenticate again. Run it if a rune may have been copied or exposed, or if an app with RPC access to your node may have created one without your knowledge — for example if you run BTCPay Server, which reaches Core Lightning over its admin RPC socket and shipped an actively exploited vulnerability in versions before 2.4.2. Core Lightning restarts afterwards to issue the web UI a fresh rune; re-issue any other integration's rune with **Create Rune**.
- **General Settings** — set alias, color, fee base and rate, minimum channel capacity, funding confirmations, Tor-only mode, Clams Websocket, a custom external host, and the Bitcoin retry timeout.
  - **Bitcoin Retry Timeout** is how long Core Lightning keeps retrying Bitcoin before it shuts down with "The Bitcoin backend died". The default is 60 seconds; raise it if that happens while Bitcoin is busy, such as during a reindex.
  - **Custom External Host** announces an external tunnel or VPN endpoint, as your node's public address. It is announced in place of any public IP StartOS detects, so peers are not handed the home IP the tunnel exists to hide; your Tor address is still announced. Core Lightning resolves the name once at startup, so restart it if the endpoint moves to a new address. Nothing is announced while Tor-only mode is on, because Core Lightning cannot resolve a hostname with every connection forced through the proxy — a failing **Custom External Host** health check appears while both are set, to tell you so.
- **Plugins** — enable or disable CLNrest, Sling, and CLBOSS, with sub-settings for CLBOSS (min on-chain reserve, auto-close, zero base fee, channel size limits).
- **Experimental Features** — toggle shutdown-wrong-funding and dual funding / liquidity ads (with policy, fuzz percentage, fund probability, and merchant lease-fee settings). Dual-funding amounts are in satoshis, except Channel Fee Max Base, which is in millisatoshis.
- **Watchtower Settings** — enable the TEOS watchtower server, enable the watchtower client, and add tower URIs to register with. A tower URI is `<pubkey>@<host>:<port>`, reached over plain HTTP; prefix the host with `https://` for a tower that serves its API over TLS. Give each tower an optional label, such as who runs it, so you know who to contact if it goes offline. While you subscribe to towers, the **Watchtowers** health check shows whether each one is reachable.
- **Watchtower Info** — visible when the watchtower server is enabled; shows the server URI and stats.
- **Watchtower Client Info** — visible when at least one tower is configured; shows registered towers and subscription state. Towers you add are registered automatically the next time Core Lightning starts, and stay registered across restarts and updates. If this list is empty, give the service a minute after startup and check it again — registration runs shortly after Core Lightning is up. Tower URIs are usually `.onion` addresses, which need Tor installed and running to reach.
- **Rescan Blockchain** — rescan the blockchain from a given depth or block height. **Required after restoring from backup** — the wallet balance reads zero until a rescan completes.
- **Reset UI Password** — clear the CLN Application UI password so you can set a new one on your next visit from its `.local`, IP, or `.onion` address.
- **Delete Gossip Store** — delete a corrupted `gossip_store`; CLN will rebuild it from peers on next start. Available when the service is stopped.
- **CLBOSS** — available while CLBOSS is enabled in **Plugins** and the service is running:
  - **CLBOSS Status** — what CLBOSS sees and is doing: connectivity, its view of on-chain fees, whether it is managing on-chain funds, peers you have excluded, and its swap totals.
  - **Ignore On-chain Funds** — stop CLBOSS from putting on-chain funds into channels for a number of hours, so you can open a channel or withdraw funds yourself. **Resume On-chain Management** ends it early.
  - **Unmanage Peer** — stop CLBOSS managing fees, channel opens, channel closes, or rebalancing for one peer, for example to set your own fees on a channel to a friend. Run it again with nothing selected to hand the peer back.

### Paying and receiving

**Pay Invoice** pays a Lightning invoice from your node without a wallet app: paste it, enter an amount only if the invoice leaves it open, set the most you are willing to pay in routing fees, and confirm. Verify the decoded amount, destination, and description before sending; payments cannot be reversed. The result shows what was paid and the preimage. A service that needs a payment from you can raise the same prompt with those details disclosed and the invoice locked.

**Receive Payment** creates an invoice for someone to pay you: set an amount (or leave it empty to let them choose), a description they will see, and how long it stays payable, then show them the QR code or send them the invoice text. Both live under **Payments**.

### Backups and restore

StartOS backs up the `main` volume, excluding live database files and the gossip store. Restoring brings back your keys and settings, but **not** the wallet's record of its own coins — so right after a restore, your on-chain balance reads **zero**. This is expected and your funds are not lost.

After a restore, Core Lightning automatically:

- runs `emergencyrecover` to attempt recovery of channel funds via peer cooperation (best-effort — it depends on peers responding),
- pre-registers your wallet's addresses so the rescan below finds all of your coins,
- saves an untouched copy of the channel-recovery file as `bitcoin/emergency.recover.restored-<date>` for support and manual recovery,
- prompts you with a task to run **Rescan Blockchain**.

Run the rescan with a blockheight from before your node was created, prefixed with a hyphen (e.g. `-800000`). It takes hours; the **Synced** health check stays red while it works — leave Core Lightning and Bitcoin running until it turns green, then check your balance.

If the balance is still missing funds after the rescan completes, contact support: your funds are recoverable — the wallet's public descriptors can locate every coin exactly, even ones the rescan missed.

Once any recovered channels have resolved, sweep remaining funds to another wallet and reinstall fresh if you want to keep using the node. Restore only what you must: restoring an old backup over a working node replaces its live records with stale ones.

### Moving an existing node to StartOS

You can bring a Core Lightning node from another machine, keeping its node ID and channels, by copying its data into this service.

1. **Stop Core Lightning on the old machine and make sure it cannot start again.** Two running copies of one node will broadcast old channel states and lose funds. Leave it stopped for good once the move is done.
2. Install Core Lightning here, start it once so it creates its data directory, then stop it.
3. From the old node's lightning directory (usually `~/.lightning/bitcoin/`), copy these files to your server's home directory, for example with `scp`: `hsm_secret`, `lightningd.sqlite3`, and `emergency.recover`, plus `lightningd.sqlite3-wal`, `lightningd.sqlite3-shm` and `accounts.sqlite3` if they exist. The gossip store is not needed; the node rebuilds it.
4. SSH into your server and copy the files into the service's data, replacing the ones there:

   ```
   sudo cp ~/hsm_secret ~/lightningd.sqlite3 ~/emergency.recover /media/startos/data/package-data/volumes/c-lightning/data/main/bitcoin/
   ```

   Add any of the optional files you copied to the same command.

5. Start Core Lightning and watch its logs. Settings such as alias and fees are not carried over; set them in **General Settings**.

The old node must run the same Core Lightning version as this service or an older one; its database is upgraded automatically on first start, but it cannot be downgraded. If your `hsm_secret` is encrypted, decrypt it on the old machine with `lightning-hsmtool decrypt` before copying it — this service cannot ask for its password at startup.

## Limitations

- **Mainnet only.** Testnet, signet, and regtest are not exposed.
- **Bitcoin authentication is cookie-based.** `bitcoin-rpcuser` and `bitcoin-rpcpassword` are intentionally not configurable; CLN uses the mounted Bitcoin cookie file.
- **The `config` file is managed through actions.** Manual edits will be overwritten on the next config sync.


## Coordinator setup and grants

Existing paired installations can keep their saved setup after this update.
For a fresh coordinator, use **Swap Setup → Coordinator Readiness**, then
**Prepare Coordinator** with explicit confirmation. Preparation checks identity,
chain synchronization, recovery state and pending HTLCs; it grants no payment
authority. Use **Create or Show Read-only Controller Credential** to obtain the
restricted monitoring rune for **Pair Coordinator Nodes** in Swap Controller.
Use that node's verified HTTPS interface and authenticated StartOS root CA.

Create or retrieve the node's separate **Inspection Credential** under
**Swap Setup**, then save both node inspection credentials in the controller.
These allow invoice, reserve and channel checks without payment authority.
Keep them private. Do not substitute an administrator rune, delete interrupted
credential records, or bypass a restore barrier.

Enable the bounded swap gate when the setup action requests it. On the XBT
coordinator, reverse swaps require **Enable Bounded XBT Swap Gate**, followed by
a restart if indicated and **XBT Swap Gate Status**. The BTC grant setup reports
any required BTC gate restart. Gate activation alone does not authorize a swap.
Grant controls under **Swap Grants** separately approve the fixed amounts,
route limits, selected channels and enrollment budget. Review those bounds
before confirming, then pair the credentials for that direction in the controller.

For routed BTC to XBT grants, explicitly enable **Allow routed swaps** and leave
the optional channel field empty to approve all currently eligible local channels
(up to eight). Existing direct grants keep their mode unless explicitly replaced.
XBT to BTC grants automatically select eligible local channels. New reverse
grants allow up to 288 BTC route-delay blocks; old grants retain 80 or 144.
A status check never renews or widens a grant.

After adding or closing channels, finish existing swaps before explicitly
replacing grants and pairing the new credentials. More receiving liquidity does
not resolve a fee/dust protection refusal. Preserve records if the outcome of
any earlier payment or grant operation is uncertain.

Development fixtures and historical release details are documented in README.md.

## Recipient hints and preparation errors

A recipient invoice needs a route the paying coordinator can discover. Private
hints being enabled does not guarantee a hint was included: CLN can omit a
channel whose peer appears to be a dead end. If preparation reports an unavailable
coordinator request while Swap Status says ready, check the recipient invoice's
actual hint count and channel readiness. A read-only route/history diagnostic
can distinguish a route refusal from an authority or transport problem. Keep
existing grants and records while diagnosing.

On a customer CLN node, explicitly selecting eligible local channels in the
invoice's exposeprivatechannels array can provide hints omitted by the boolean
setting. Select from current connected, normal channels with sufficient receiving
liquidity and verify that the new invoice contains a hint; never invent a SCID.
This does not widen grant authority or route limits. The forward preparation UI
can still mask a specific route refusal as a generic coordinator-request error.
