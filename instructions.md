# Core Lightning

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


## Experimental BTC swap image preparation

This development branch adds an inert Python swap-module bundle from
`BitcoinMechanic/lightning` commit
`81ba4099a63e5a0e83f55cead53c54f2a1b3c1fe`, matching the XBT package.
The BTC daemon remains upstream CLN v26.06.8; the existing UI and wrapper
configuration are retained. Swap files are outside automatic plugin discovery.
No swap gate, quote API, controller or additional listener is enabled.

The initial image checkpoint established binary compatibility. Package
26.6.8:6 now adds preparation actions; live controller pairing is still absent.
An installation over an existing CLN wallet is not part of this pilot.
Existing package ID `c-lightning` is retained: this is not a side-by-side
installation alongside another `c-lightning` package on the same StartOS box.

From the packaging VM, build and check without a backend or wallet:

```sh
docker buildx build --builder startos-builder --platform linux/amd64 \
  --load -f Dockerfile -t btc-cln:swap-preparation .
docker run --rm --network none btc-cln:swap-preparation \
  python3 /usr/local/libexec/check-btc-swap-bundle.py
```

The build checks the source pin, Python imports, CLN/bitcoin-cli executables
and gate manifests. These checks do not establish funded-swap compatibility
with upstream CLN. A separate disposable regtest must verify that before
live gate activation or controller pairing. Do not manually load the bundled
gates against a live wallet. Ordinary-node backup behavior is unchanged;
recovery of active swap state is not established by this image check.


### Funded BTC gate compatibility test

Run the packaged upstream BTC daemon and two disposable nodes with the bundled
quote gate. The mounted Knots binary runs ordinary BTC regtest with BLAKE2b
activation omitted. Docker has no external network and no production volumes.

```sh
bash scripts/test-btc-gate.sh btc-cln:swap-preparation ../bitcoind
bash scripts/test-btc-gate.sh btc-cln:swap-preparation ../bitcoind --fail
```

These tests fund a private channel, hold a signed BTC invoice, restart the
coordinator, and verify the original hook binding and final channel balances.
The success case also checks an outgoing BTC sendpay/waitsendpay and its
preimage. The failure case returns the original channel balances. This is a
BTC compatibility test only: the XBT invoice is a clearly marked fixture,
there is no XBT leg, and no live activation or market pricing is tested.
Logs remain under the printed disposable directory. No image rebuild is
needed for this harness-only patch.


### Combined packaged-binary controller regtests

```sh
bash scripts/test-image-pair.sh \
  btc-cln:swap-preparation xbt-cln:recovery-test ../bitcoind
```

The launcher resolves both local image IDs, copies the XBT image's installed
`/usr/local` tree without starting it, and mounts that tree read-only at
`/opt/xbt` in the BTC test container. CLN finds its matching subdaemons and
builtin plugins relative to its executable. Both image versions and the XBT
source receipt are checked; the controller modules come from the pinned BTC
swap bundle. This tests the packaged binaries together in one Debian runtime,
not StartOS networking or cross-box RPC transport. No new image build is needed.

Four scenarios run sequentially: forward success, forward rejection, reverse
success and reverse rejection. Each uses the existing pinned controller
fixture with operator restarts while HTLCs are pending, recovery of the
original payment, and balance/settlement assertions. Quote rates are fixed
regtest fixtures, not oracle quotes. Use an optional final argument `forward`,
`forward-failure`, `reverse` or `reverse-failure` to select one scenario.

Docker has no external network. Only the backend executable, extracted XBT
binaries, test script and fresh results directory are mounted; no live data
or Docker socket enters the container. The Knots binary supplies two isolated
backends: ordinary BTC regtest and activated XBT regtest. Temporary extracted
binaries are removed at exit, while test logs remain at the printed path.
This does not activate a gate on either installed StartOS node.


## BTC coordinator preparation package — 26.6.8:6

This build retains upstream CLN v26.06.8, the web UI, existing interfaces and
package ID `c-lightning`. Its title is **Core Lightning (Swap Preparation)**
and its package repository is `BitcoinMechanic/btc-cln-startos`. Since the ID
is shared with the stock package, it cannot be installed alongside stock
Core Lightning on the same box. Start with a fresh installation on the BTC
Bitcoin Core box; do not use this pilot to migrate an existing funded wallet.

After ordinary package initialization and synchronization, run **Coordinator
Readiness**, then **Prepare Coordinator** with confirmation, then readiness
again. The expected result includes `prepared: true`,
`controller_pairing_required: true`, and
`live_activation_enabled_by_package: false`. No payment is started.

Preparation checks the pinned modules, BTC network label, expected CLN
version, node identity, absence of synchronization warnings or pending HTLCs,
and pending wrapper restore/rescan flags. It saves a mode-0600 receipt tied
to that node, network, CLN version and source revision. Repeating the action
preserves its bytes; a changed identity or record is refused. The status
action performs only read RPCs (its local lock file may be created).

The receipt is advisory preparation, not gate activation, backend chain proof
or spending authorization. Pairing must independently verify both backends
and operator identities and establish policy. No swap plugin is auto-loaded;
no controller, quote API or new network listener is started by these actions.
The receipt and lock are excluded from backup, and a restore removes any
existing receipt. Ordinary upstream wallet backup/recovery behavior otherwise
remains unchanged. Active swap recovery is not enabled by this package.

Build on the packaging VM:

```sh
python3 tests/test_coordinator.py -v
npm ci --ignore-scripts
npm run check
npm run build
node scripts/check-btc-bundle.cjs
BUILDX_BUILDER=startos-builder make x86
```

The artifact is `c-lightning_x86_64.s9pk`. The XBT package is separate and
unchanged. Before installation, confirm the target box does not already
have a Core Lightning wallet that this same-ID package would replace.
