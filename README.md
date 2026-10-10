<p align="center">

## Forward error reporting checkpoint (0063)

The user reported 0062 READY on 2026-10-09 (America/Vancouver): both four-case
funded regtest matrices and all three installer builds passed. Build versions:
BTC 26.6.9:8, XBT 0.1.0:26 and Swap Controller 0.1.0:23. After the installation
step, user-supplied read-only status confirmed ready pairing, saved inspection
credentials, a fresh worker, no backup pause and ready coordinator gates.

Initially both forward grants had expired with eight unused slots each; reverse
grants remained ready with three slots. The operator explicitly replaced and
paired only the forward grants. At checked_at 1791591029, both directions were
ready_to_prepare with no blockers, no active swaps and no records requiring
attention: ten forward slots per coordinator, three reverse slots. Forward
caps remained 80 blocks, four hops and 10,000 XBT msat; reverse caps remained
288 blocks, four hops and 10,000 BTC msat. The existing restore barrier remained
present. Readiness does not establish a route or constitute payment authority.
No new live swap, live route refusal, live restart or on-chain recovery result
was requested or reported for this update; prior live evidence remains below.

The UI summary did not make the individual grant reasons easy to locate during
this review; the packaged read-only CLI identified grant_expired on both nodes.
The Connection Status field live_payment_enabled=false describes that read-only
probe, not the separate swap grants. These presentation issues remain follow-up
work; no UI or runtime change is introduced by this checkpoint.

0063 changes seven documentation files only and exports the complete 0062 delta
from the synced swap-interface-live-20261009 tag with the exact tested installer
hashes. Keep those installers; no rebuild is required. Export on the packaging
VM, commit/tag/push on the tower, then retain VM stashes and fast-forward from
GitHub. The checkpoint scripts do not access live grants or payment records.

## Forward planning error fix (0062)

Candidate versions: BTC 26.6.9:8, XBT 0.1.0:26, Swap Controller 0.1.0:23.
The 0061 checkpoint was committed/pushed from the tower and synced on the
packaging VM, with stashes retained (user confirmation, 2026-10-09).
Apply against tag `swap-interface-live-20261009`; continue building/exporting
on the VM and committing/pushing on the tower.

Forward `plan` responses now carry only four fixed refusal codes: no bounded
route, route outside the grant, planning refused, or invalid recipient invoice.
The controller accepts only an exact one-field response during `plan`, and the
preparation action explains the applicable XBT fee, delay and hop limits. It
suggests private routing hints when the recipient has a private channel, without
claiming hints are missing or guaranteeing that they make a route possible.
Transport failures, malformed/unknown replies and all mutation errors remain
opaque. An older node still produces the generic uncertainty message until it
is updated. Reverse error behavior is retained.

This changes error reporting only: route selection, approved channel pins,
fee/delay/hop caps, one part/attempt, grant budgets, confirmation, invoice
publication, payment and restart recovery retain their existing rules. No state
migration or grant renewal is required. Refused preparation neither enrolls a
swap nor reserves a slot. Swap Status still checks setup rather than routes.
The earlier forward UI limitation described below applies to the 0061 release.
The subsequent user-reported funded build and post-update readiness checks
are recorded in the 0063 checkpoint above.

## Installed interface checkpoint (0061)

The user reported 0060 READY on 2026-10-09: operator/status checks, both four-case
funded matrices and all three installers passed. The packages were installed
and the cleaned menus appeared correct. Versions remain BTC 26.6.9:7,
XBT 0.1.0:25 and Swap Controller 0.1.0:22. 0061 changes documentation only;
its source export checkpoints the full 0060 implementation without rebuilding.

Live retesting: the user confirmed the forward customer XBT invoice was paid.
That test requested 1,000 BTC sats -> 2,000 XBT sats. The final received-amount
field and forward controller terminal status were not separately pasted for
this retest. The reverse test requested 3,000 XBT sats -> 1,500 BTC sats; the
user reported customer payment complete, controller settled and receipt in LND.
Final routes, fees, adjacency and payment timestamps were not supplied for these
retests. These are user-reported happy paths; no new live failure, restart or
on-chain recovery claim is made. Earlier 0059 evidence remains recorded below.

The first forward recipient invoice had zero hints despite requesting private
hints. Read-only coordinator diagnosis passed history checks and refused route
planning with bounded_route_unavailable (2,000,000 msat, final CLTV 40, 6,763
seconds remaining). A replacement invoice explicitly selected eligible local
channel hints on the customer VM, without manual SCID entry, and payment then
worked. CLN can filter dead-end peers even when exposeprivatechannels=true;
this is a possible explanation, not a separately observed warning in this run.

Known UI limitation: forward node-side planning refusals still cross the plugin
boundary as an opaque error. The controller can therefore show a generic
coordinator-request error for a missing bounded route. Reverse planning already
has a fixed, privacy-safe refusal protocol. A follow-up should extend that
protocol to forward planning while keeping mutation/unknown errors private.
Swap Status intentionally checks grants/setup, not invoice-specific routes.

Export source and installer copies from the packaging VM; commit/tag/push on the
tower; then retain VM stashes and fast-forward from GitHub. Do not pop retained
stashes onto an already-applied checkpoint. Service backups remain separate.

## Operator interface cleanup (0060)

Candidate versions: BTC 26.6.9:7, XBT 0.1.0:25 and Swap Controller 0.1.0:22.
0059 was committed/pushed from the tower and the packaging VM was synced, with
stashes retained (user confirmation, 2026-10-09). Apply 0060 against that exact
checkpoint tree. Build/test on the VM, export to the tower for commits/pushes,
then retain a VM stash and fast-forward from GitHub as before.

The controller normally presents 15 actions, grouped into Swaps, Swap Setup,
Status and Advanced / Recovery. Both directions have explicit preparation,
confirmation, history and draft-cancellation names. Setup credentials and grant
pairing are grouped together. Legacy quote/record inspection is shown only when
records exist (or cannot be inspected). An existing single pilot keeps its
approval and status actions. Old preparation, readiness, policy, gate-observer
pairing and regtest commands remain registered with hidden menu visibility;
visibility is not an authorization boundary. Their handlers and test entry
points retain all existing authorization and regtest guards.

Swap Status reads connections, the worker heartbeat, inspection binding and each
saved grant through its info operation. It reports remaining slots, enrollment
expiry, pause/replacement/exhaustion, exact direct/routed fee/hop/timing limits
and blockers for new preparation. It never plans a route, enrolls, advances,
renews, publishes or pays. Expired/paused grants remain inspectable. Responses
are bound to the saved session, node identity, network, pairing and restore
epoch; changed or stale observations are discarded. Output uses fixed fields
and reason codes, never endpoints, runes, certificates, invoices or raw RPC text.
The existing read-only pairing client gains no write methods. No report is
payment authority, and recipient-specific route/liquidity checks still happen
when preparing a swap. Existing enrolled recovery is unaffected by the report.

The coordinator grant controls are named by direction under Swap Grants, with
preparation and credentials under Swap Setup. Single-pilot authorization stays
under Advanced / Legacy so an older reviewed contract can still be authorized.
The old standalone gate-observer credential menu is hidden. Current inspection
credentials, grant retrieval, direct mode and all wallet/channel actions remain.

Known reserve, inspection, stale-worker, changed-channel, expired-review and
uncertain-request failures now have specific explanations. Unknown errors still
withhold private details. Existing internal pilot module names, journal paths,
contract profiles and action IDs are retained. No records, grants, restoration
barriers, payment algorithms or approval defaults are migrated. New swaps still
use one part and one outgoing attempt, with the same fixed prices and bounds.

## Live bidirectional checkpoint (0059)

On 2026-10-09 the user confirmed a live XBT → BTC swap: the customer XBT
payment completed, Reverse Swap History showed settled, and the LND recipient
invoice was SETTLED with 1,500 sats received. This follows the live BTC → XBT
result: 2,000,000 XBT msat received at 2026-10-09T01:41:09Z, controller settled,
and the LND payer reached the coordinator through an independent public peer.
These are user-reported live happy-path results, without independent node access.
The earlier reverse read-only route candidate was three hops, 200 blocks and
2,002 msat; the final executed route was not separately supplied. The reverse
XBT payer's adjacency was not reconfirmed. Live failure, restart and on-chain
recovery success have not been demonstrated by these results.

The packaging VM reported 0058 READY: all four reverse and all four forward
funded scenarios passed, and all three installers were built. The seven-node
reverse fixture covers non-neighbor customers, a 200-block public BTC prefix
plus private tail, seven balance changes, exact incoming binding, one outgoing
attempt, definitive failure, lost replies and pending coordinator restarts.
Local validation passed 103 focused Python cases and all three package checks.
These recovery results are regtest evidence, separate from the live settlements.

Installed versions remain BTC 26.6.9:6, XBT 0.1.0:24 and controller 0.1.0:21.
0059 changes documentation only; its cumulative export includes 0056–0058.
Export verified source and installer copies from the packaging VM, commit/push
on the tower, then retain VM stashes and fast-forward from GitHub. Do not pop
those stashes onto the already-applied checkpoint. The source checkpoint does
not replace runtime service backups or change existing grants.

## Reverse public-prefix timing update (0058)

0057 reached READY on the packaging VM: both funded matrices passed and all
three installers were built (user log, 2026-10-09). Its two-hop BTC fixture
covered only a 120-block private tail. The subsequent live read-only diagnostic
confirmed an active 144-block grant and found the complete three-hop route at
200 blocks and 2,002 msat. Increasing only the fee budget did not find a route
at 144. The later 0058 live settlement is recorded above.

New explicitly requested grants use `startos-reverse-repeat-v3`, with a
288-block total BTC route cap; their contracts use `startos-reverse-routed-v3`.
This accommodates three 80-block forwarding deltas plus the fixed 40-block
recipient delay in a four-hop route (280 total). This is a cap, not a promise
that arbitrary routes fit. The fee cap stays 10,000 msat, with at most four hops,
one part and one outgoing attempt. Recipient invoices still require final CLTV
at most 40 and at least 33 minutes remaining.

Existing v1/v2 grants and contracts retain 80/144 blocks. Retrieval never widens
a grant; installation rewrites no authority or journal. The default local enable
API still requests 80, while the explicit StartOS action requests 288. Both
coordinators enforce the contract profile against the stored grant before
reserving a slot. Paired limits must match. Unfinished swaps block renewal;
paused or expired enrolled swaps retain their original recovery authority.

Incoming timing derives from the exact saved outgoing route: BTC delay + 6
submission blocks + 144 XBT recovery blocks, plus 24 quote-drift blocks in the
invoice. A 200-block route requires 350 blocks before submission and advertises
374. The incoming close guard remains 144 blocks. Existing contracts recover
without replanning, changing bindings or repeating mutations. The relative-chain
progress assumptions of the existing policy are unchanged.

Route refusal now names the actual paired cap (80, 144 or 288). This value comes
from the validated grant profile. Only fixed safe reason codes reach the UI;
raw RPC text, invoice data and credentials remain private. Forward/direct flows
and their grant namespace are unchanged.

Verified versions: BTC 26.6.9:6, XBT 0.1.0:24, controller 0.1.0:21. The VM
rebuilt all three images, passed both funded matrices and built the installers.
The reverse fixture has seven nodes:
three on XBT and four on BTC, with two public BTC channels and a private final
channel. Both BTC forwarding nodes advertise 80 blocks, 1,000 msat base and
1 ppm; the fixture requires 200 blocks, 2,002 msat, all seven balance changes,
actual incoming binding and one outgoing attempt. The process preflight covers
the same route for settlement, lost replies, failure and restart. Local tests
simulate CLN/transport; the native funded and installer checks ran on the VM.

## Historical reverse implementation and validation (0056–0056c)

Adds a separate XBT → BTC repeat flow at a fixed test price: 3,000 XBT sats in,
1,500 BTC sats delivered. At 0056 this was a candidate pending the VM funded
matrix; the current funded and live outcomes are recorded above. The forward live checkpoint is
retained: BTC `1211fcd`, XBT `50635bb`, controller `910fc28`.

Reverse credentials use only `swap-reverse-call`, with a named session ID and
exactly five parameters. They cannot call raw payment/close methods or the
forward authority method. Forward credentials cannot authorize BTC spending.
Reverse session and swap records use separate `reverse-sessions` and
`reverse-swaps` directories; grants last 24 hours and consume 1–10 durable slots.
Recovery rights for an enrolled swap survive expiry, pause and renewal. New
admission checks unresolved records in both directions under the common lock.
Restores block old authority; backups omit credentials and executable records.

The signed BTC recipient invoice determines one immutable route: at most four
hops, 10,000 msat BTC fee, 80 blocks first-hop delay and 40 blocks final delay.
The incoming XBT invoice advertises approved channels using the peer's remote
alias where required. The actual committed incoming HTLC/funding pin is persisted
before BTC submission. There is one part and one outgoing attempt, with no
payment retry after a missing reply. The actual outgoing BTC HTLC ID and expiry
are also persisted when observed; route planning is never repeated during recovery.

Reverse timing uses the existing candidate budget: BTC route delay + 6 blocks
submission slack + 144 XBT blocks recovery reserve; the invoice adds 24 blocks
quote drift. Independent chains do not guarantee relative progress. At 144 XBT
blocks remaining an unresolved attempt requests protection of the original
incoming channel exactly once. Expiry alone never authorizes failure or resend.
Post-close status remains on-chain recovery, not verified settlement.

The XBT extension retains the pinned reverse gate's existing activation, journal,
and older quote profiles. `reverse-repeat-register` validates the new exact
contract, while `reverse-retire-repeat` permanently expires an unpaid quote.
An accepted replay can only resolve its original binding. The shared anchor
fee/dust check and actual untrimmed-HTLC checks remain in force.

Packaging workflow: apply/build/test on the packaging VM, export verified source
to the tower, commit/push there, then stash and fast-forward the VM. Never pop
checkpoint stashes onto already-applied source. This candidate makes no commits,
pushes, live activations or live payments automatically.

  <img src="icon.svg" alt="Core Lightning Logo" width="21%">
</p>

# Core Lightning on StartOS

> Everything not listed in this document should behave the same as upstream
> Core Lightning. If a feature, setting, or behavior is not mentioned here, the
> upstream documentation is accurate and fully applicable — see the
> Documentation section of `instructions.md` for links.

[Core Lightning](https://github.com/ElementsProject/lightning) is a Lightning Network node implementation. This package builds it with three plugins built into the image, runs a web UI alongside it, and can act as — or subscribe to — a BOLT13 watchtower.

- **Upstream repo:** <https://github.com/ElementsProject/lightning>
- **Wrapper repo:** <https://github.com/Start9Labs/cln-startos>

---

## Table of Contents

- [Image and Container Runtime](#image-and-container-runtime)
- [Volume and Data Layout](#volume-and-data-layout)
- [File Models](#file-models)
- [Dependencies](#dependencies)
- [Network Access and Interfaces](#network-access-and-interfaces)
- [Installation and First-Run Flow](#installation-and-first-run-flow)
- [Actions](#actions)
- [Tasks](#tasks)
- [Health Checks](#health-checks)
- [Backups and Restore](#backups-and-restore)
- [Limitations and Differences](#limitations-and-differences)
- [Quick Reference for AI Consumers](#quick-reference-for-ai-consumers)

---

## Image and Container Runtime

Two images. The node's is built here: upstream's signed release tarball is unpacked onto a slim Debian base and three extra plugins are added; the web UI's is pulled as published. lightningd comes from the tarball rather than the `elementsproject/lightningd` image because the tarball is signed: its checksum is pinned in the `lightningd-tarball` stage and taken from a GPG-verified manifest. For a release upstream published no arm64 tarball for, the arm64 image instead compiles lightningd in the `lightningd-source` stage from the release's source zip, whose checksum comes from the same manifest; `lightningd-dist` picks the stage per architecture. `bitcoin-cli` is pinned and checksummed the same way in the `bitcoin-cli` stage, because `plugin-bcli` and the `check-synced` health check both exec it.

| Property      | Value                                                                                             |
| ------------- | ------------------------------------------------------------------------------------------------- |
| Images        | Built from `Dockerfile` on `debian:bookworm-slim`, plus `ghcr.io/elementsproject/cln-application` |
| Architectures | x86_64, aarch64 — both images declare `emulateMissingAs: 'aarch64'`                               |
| Entrypoint    | `lightningd` with an explicit config path; the UI runs its own server                             |

The final stage also installs `wireguard-tools`, `iptables` and `iproute2` for the tunnel the hidden Clearnet VPN action brings up, and the manifest sets `virtualNetworking` so the container can create its interface. Three plugins are dropped into the plugin directory at build time: **CLBOSS** (automated channel management) and **watchtower-client**/**teosd** from rust-teos (BOLT13 watchtower, both client and server) are compiled from their git submodules, and **sling** (rebalancing) is an upstream release binary pinned by `SLING_VERSION` in the `Dockerfile`. Nothing is fetched at runtime, so the image is self-contained.

| Subcontainer          | Purpose                                                                         |
| --------------------- | ------------------------------------------------------------------------------- |
| `lightning-sub`       | `lightningd`, the watchtower server, and every oneshot — the one to `attach` to |
| `cln-application-sub` | The web UI, which talks to the node over its RPC and rune                       |

## Volume and Data Layout

One volume, holding everything.

| Volume | Mount Point        | Purpose                                                                                                                                |
| ------ | ------------------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| `main` | `/root/.lightning` | The lightning directory: `config`, the node's `hsm_secret` and channel database, the UI's own data, the watchtower's, and `store.json` |

Bitcoin's data directory is mounted **read-only** at `/mnt/bitcoin`, which is how both `lightningd` and the watchtower read its RPC cookie without a password ever being stored.

The watchtower client's own database is deliberately relocated onto this volume. Upstream defaults it to the user's home directory, which is not persistent here, and the effect of leaving it there is silent: the client would re-key and forget every registered tower on each container rebuild.

## File Models

Four models. One is the node's own configuration, one is the web UI's, one is the watchtower's, and one is StartOS-side state.

| File                    | Format | Modelled                | Written by                                                          |
| ----------------------- | ------ | ----------------------- | ------------------------------------------------------------------- |
| `/config`               | INI    | Yes — `FileHelper.raw`  | Every init, the config actions, and `watchHosts` on address changes |
| `/store.json`           | JSON   | Yes — `FileHelper.json` | Every init, the watchtower and rescan actions, `main`, and restore  |
| `/data/app/config.json` | JSON   | Yes — `FileHelper.json` | Every init, and the Reset UI Password action                        |
| `/.teos/teos.toml`      | TOML   | Yes — `FileHelper.toml` | Every init                                                          |

### config

**Enforced** — rewritten whenever the package writes the file: `network`, `bitcoin-datadir`, `bind-addr`, `grpc-port`, `grpc-host`, and `clnrest-protocol`. `bitcoin-rpcuser` and `bitcoin-rpcpassword` are modelled as "must be absent" and deleted if present, because authentication is by the cookie read through the mount.

`clnrest-protocol` is the one enforced value that is an override rather than a constant: **upstream defaults CLNrest to HTTPS, and this package forces plaintext.** A Tor onion address already encrypts, and wallets reaching the node that way cannot validate a StartOS-issued certificate; LAN and clearnet callers still get TLS, terminated by StartOS at the edge. See [Network Access and Interfaces](#network-access-and-interfaces).

**Derived, and rewritten whenever the underlying address changes:** `proxy` (Tor's SOCKS address), `announce-addr` (the onion and public addresses published on the peer interface, or your custom external host in place of the IPs), and `bitcoin-rpcconnect` / `bitcoin-rpcport`. Editing any of these by hand does not stick.

Everything else — alias, colour, fee policy, channel minimums, the Bitcoin retry timeout, the plugin selection, CLBOSS's tuning, the experimental flags — is yours, through the config actions. The only override install makes is switching `clnrest` on.

Two interactions are worth knowing because they produce a state neither setting explains alone. A **custom external host is dropped rather than written while Tor Only is enabled**: `always-use-proxy` disables lightningd's DNS resolution, and an `announce-addr` it cannot resolve is a fatal startup error rather than a warning — so the package omits it and raises a health check saying so. And **enabling the Clams websocket adds a second `ws::` bind address** rather than replacing the first.

### store.json

`watchtowerServer`, `watchtowerClients` and `watchtowerLabels` are the watchtower configuration — the labels are kept apart from the tower URIs, keyed by tower id, so renaming a tower does not restart the node — `customExternalHosts` the user-managed announced address overrides, `clearnetVpn` the Clearnet VPN's WireGuard configuration and companion-managed public address (kept verbatim; `vpn/wg0.conf` is generated from it on every start and never hand-edited), and `rescan` and `restore` are one-shot request flags.

Those two flags are deliberately **not** cleared when `main` reads them. A session where `lightningd` never comes up must not consume a request, or it vanishes silently — which is how a rescan requested during a crash loop used to be lost. A oneshot clears them only once the node answers RPC, and `main` ignores that clearing write so it does not bounce the service.

### config.json and teos.toml

The web UI's `config.json` carries its display preferences and its password hash. `teos.toml` is entirely enforced apart from Bitcoin's address, which is derived like the node's: every port, bind address, and subscription parameter is a fixed value, so the watchtower is not configurable from here.

## Dependencies

One, and it is required.

| Dependency | Kind      | Health checks               | Mount                     | Why                            |
| ---------- | --------- | --------------------------- | ------------------------- | ------------------------------ |
| Bitcoin    | `running` | `bitcoind`, `sync-progress` | `/mnt/bitcoin`, read-only | Chain data, and the RPC cookie |

Both health checks are required, not just "running": a node that is up but still syncing cannot serve a Lightning node correctly, and the sync state is surfaced again in this package's own [`check-synced`](#health-checks).

Bitcoin's RPC address is resolved from its own binding over the service bridge, so nothing is configured by hand and a Bitcoin update does not move it. When Bitcoin is absent the address keys are cleared rather than left stale, and `lightningd` fails to connect until it returns.

The node additionally **restarts when Bitcoin writes a replacement RPC cookie**, but not when the cookie merely disappears — an absent cookie means Bitcoin is down, and stopping `lightningd` at that moment hangs its shutdown.

## Network Access and Interfaces

Four interfaces always, and three more depending on what is enabled.

| Interface       | Id           | Type | Port | Present                                     |
| --------------- | ------------ | ---- | ---- | ------------------------------------------- |
| Web UI          | `ui`         | ui   | 4500 | always                                      |
| RPC             | `rpc`        | api  | 8080 | always                                      |
| Peer            | `peer`       | p2p  | 9735 | always                                      |
| gRPC            | `grpc`       | api  | 2106 | always                                      |
| CLNrest         | `clnrest`    | api  | 3010 | when CLNrest is enabled (it is, at install) |
| Clams Websocket | `websocket`  | api  | 7272 | when the Clams remote websocket is enabled  |
| TEOS Watchtower | `watchtower` | api  | 9814 | when the watchtower server is enabled       |

**gRPC is forwarded as a plain TCP port, with no StartOS TLS listener in front of it.** The plugin performs its own mutual TLS, and its certificate names only `cln` and `localhost`, so every client that verifies it sends `cln` as the TLS server name whatever address it dials. A terminating listener would present the device certificate and strip the client's; a passthrough listener routes by server name and refuses one that is not an address of the interface, which `cln` never is. The binding is a raw forward deliberately — either TLS arrangement would look correct and refuse every client.

**CLNrest carries its own credential in the address.** The interface's URL includes the rune the package generated, and its scheme is overridden to `clnrest+https` or `clnrest+http` so that a wallet reading the scheme knows which transport to use — a bare `clnrest://` is assumed to be TLS, which would be wrong for the Tor address.

## Installation and First-Run Flow

Install seeds the four models and switches CLNrest on — there is no wizard, and no credential is asked for. The service remains stopped until the user starts it; `lightningd` then creates `hsm_secret` on its first start.

The one piece of setup the package performs is the web UI's credential. A oneshot creates a rune scoped to the application and records it alongside the node's public key, regenerating it only if the node's identity changes or the rune is missing. The UI cannot start until that has happened.

The ordering that matters is Bitcoin's: the node starts, but `check-synced` reports Bitcoin's progress and then its own until both are caught up, which on a fresh Bitcoin node is the length of an initial block download.

## Actions

Twenty actions. Three configure the node, three concern the watchtower, four drive CLBOSS, two handle payments, one is hidden and exists for a companion package, and the rest are recovery and information.

### Configuration — General Settings, Plugins, Experimental Features

Three actions writing `/config`, grouped together. Each writes only the fields it presents, costs seconds plus a restart, and is safe to re-run — the forms are pre-filled from the current file.

- **General Settings** carries node identity, fee policy, channel minimums, Tor Only, the custom external host, the Clams toggle, and `bitcoin-retry-timeout` — how long `plugin-bcli` retries a failing `bitcoin-cli` call before `lightningd` exits with `The Bitcoin backend died` (upstream default 60 seconds, which also raises the RPC client timeout to match). Two combinations produce a visible consequence rather than an error: Tor Only with a custom external host drops the host and raises a health check, and the Clams toggle changes the bind addresses.
- **Plugins** selects which of the built-in plugins load, and carries CLBOSS's tuning.
- **Experimental Features** exposes upstream's experimental flags, which are not standardized across implementations and may break between releases. Its dual-funding amounts are written to the `funder-*` options as bare numbers, which the funder plugin reads as satoshis; the lease's `channel-fee-max-base-msat` is the one amount in millisatoshis.

### Watchtower Server, Watchtower Info, Watchtower Client Info

**Watchtower Server** turns this node into a BOLT13 tower for others, which starts the `teosd` daemon and publishes an interface. It also registers and de-registers the towers **this** node subscribes to: a tower removed from the list is abandoned on the next start. Once the client has been enabled, `watchtower-client` stays in the config's `plugin` list even after the last tower is removed — it is the only source of `abandontower`, so removing it would strand the registrations it still holds in `watchtowers_db.sql3`.

Each subscribed tower is stored as the user typed it and parsed by `startos/actions/watchtower/towerUri.ts` into the tower id, host, and port that the `watchtower-client` oneshot passes to `registertower` as three arguments. The host keeps any `https://` prefix, which is what makes the plugin talk TLS to that tower; `lightning-cli` would send a bare IPv4 host as a JSON number, so the host is passed pre-quoted. The same module reconstructs the address `listtowers` reports a tower under, so that an entry written without a port or scheme matches the tower already registered instead of being abandoned and re-registered on every start.

Each tower takes an optional label, stored in `watchtowerLabels` against the tower id parsed from its URI and shown by Watchtower Client Info and the `watchtowers` health check. A label change alone does not restart the node.

- **What it changes:** `watchtowerServer`, `watchtowerClients` and `watchtowerLabels` in `store.json`, and through the first two the daemon chain and the exported interfaces.
- **Cost:** seconds, then a restart.
- **Repeat safety:** safe both ways.

**Watchtower Info** and **Watchtower Client Info** are read-only, available only while running, and each is hidden unless the corresponding side is enabled: the first reports this node's tower identity, the second the towers it is subscribed to.

### Create Rune, Revoke All Runes

**Create Rune** mints an access credential for an external application, with the restrictions you specify. Available only while running; each run produces a new rune and does not affect existing ones.

**Revoke All Runes** invalidates every rune this node has issued **including the web UI's**, which is regenerated automatically on the next start. Run it when a credential may have been exposed. It is not selective — that is the point of it — so anything you have connected must be re-authorized afterwards.

### Display BIP-39 Seed

Shows the seed words backing the on-chain wallet, for disaster recovery. Note what it is not: the seed alone cannot recover channel funds.

- **Visibility:** hidden entirely when no wallet exists yet, and shown as disabled with an explanation on a node whose wallet predates BIP-39 seeds — such a wallet cannot be given one, and moving the funds to a fresh install is the only route.
- **Repeat safety:** read-only.

### Rescan Blockchain

Re-scans the chain for wallet outputs. Run it after a restore, or when an on-chain balance is missing.

- **Input:** a depth from the tip, or an absolute block height written with a leading hyphen.
- **What it changes:** sets the `rescan` request flag, which the next start turns into a `lightningd` argument and then clears.
- **Cost:** hours. `check-synced` stays red for the duration; leave the node and Bitcoin running.
- **Repeat safety:** safe to re-run. Because the flag is only consumed once the node answers RPC, a request survives a failed start rather than being silently dropped.

### Reset UI Password

Sets a new password for the web UI, writing its `config.json`. It does not touch the node, its runes, or any external application's access.

### Delete Gossip Store

Deletes the network gossip database, which the node rebuilds from peers. Run it if gossip is suspected corrupt.

- **Availability:** only while stopped, since the file is open in use.
- **Cost:** the node re-learns the network graph after starting, which takes time and affects routing until it does.
- **Repeat safety:** idempotent.

### Clearnet VPN — hidden

Not user-facing, and raised as a task by a companion package with its tunnel configuration and public address filled in. Its only known uses are the TunnelSats community package and running it by hand with some other WireGuard configuration, which is unsupported. It is not how a node is made reachable or routed: inbound reachability comes from addresses on the node's StartOS interfaces, and outbound traffic leaves through the gateway StartOS selects for it. It stores the companion-managed address separately from `customExternalHosts`; `watchHosts` announces both without overwriting addresses the user configured. It also turns Tor Only off, since Tor Only would suppress the announcement and proxy the clearnet peers the tunnel exists for. Costs a restart. A new configuration replaces the tunnel; an empty one turns it off and drops only the address it had advertised. Safe to repeat.

### Pay Invoice, Receive Payment

Grouped under Payments. **Pay Invoice** pays a BOLT11 invoice from the node's own funds: paste the invoice, whether its amount is stated in it or entered here — an invoice that leaves the amount open requires one, one that states it refuses one — and the most it may spend in routing fees as a percentage. Every payment requires confirmation that the amount and destination were verified. A task-prefilled invoice is decoded before the prompt opens, displays its amount, destination, and description, and cannot be edited; execution rejects an invoice that differs from the reviewed one. It then pays with a 60-second retry window and returns the amount, fee, description, destination and preimage; a failure returns lightningd's reason. Only while running. Not idempotent — running it twice pays twice if the invoice allows it, which a single-use BOLT11 does not. A companion service can raise it as a task with the invoice filled in, so a payment it needs is one reviewed prompt; the node never hands out a rune for it.

**Receive Payment** creates a BOLT11 invoice for this node: an optional amount (none makes an amount-less invoice the payer fills in), an optional description carried in the invoice, and an expiry in hours, default 24. Runs `lightning-cli invoice` under a generated `startos-<uuid>` label; lightningd chooses the route hints. Returns the invoice as text and QR code, plus the payment hash. Only while running. Safe to repeat — each run registers a new invoice and nothing is charged.

### Node Info

Read-only, running only: the node's identity and current state.

### CLBOSS — Status, Ignore On-chain Funds, Resume On-chain Management, Unmanage Peer

Grouped under CLBOSS, running only, and disabled with a reason unless CLBOSS is enabled in Plugins. Each runs one `clboss-*` RPC command and changes nothing outside CLBOSS's own database.

- **CLBOSS Status** summarizes `clboss-status`: version, connectivity, its low/high fee judgment, whether on-chain funds are being ignored and until when, the channel-candidate count, the unmanaged peers with their tags, and the swap totals from `swap_report`. Read-only.
- **Ignore On-chain Funds** runs `clboss-ignore-onchain` for a number of hours (default 24), so on-chain funds can be spent or put into channels by hand. CLBOSS resumes by itself when the time runs out; re-running extends it.
- **Resume On-chain Management** runs `clboss-notice-onchain`. Idempotent.
- **Unmanage Peer** runs `clboss-unmanage` with a node id and any of the `lnfee`, `open`, `close` and `balance` tags; selecting none returns the peer to full management. It replaces that peer's tags rather than adding to them, and CLBOSS Status is where the current set is read back.

## Tasks

The package raises one task after a restore; a companion package can raise the hidden Clearnet VPN action as another.

| Task              | Severity    | Raised when                                                            | Cleared when                                              |
| ----------------- | ----------- | ---------------------------------------------------------------------- | --------------------------------------------------------- |
| Rescan Blockchain | `important` | Immediately after a backup restore                                     | The action runs                                           |
| Clearnet VPN      | `important` | Only when a companion package raises it with a tunnel for this node | The stored configuration matches what the companion package proposes |

The reason is that a restored node reports an **on-chain balance of zero** until the chain is rescanned, and nothing else in the interface explains why. `important` rather than `critical`: the node should keep running — indeed it must, for the rescan to proceed.

## Health Checks

Three checks are always present, with five more for conditional features or recovery states.

| Check                  | Displayed                     | Method                                               | Present                                   |
| ---------------------- | ----------------------------- | ---------------------------------------------------- | ----------------------------------------- |
| `lightningd`           | "RPC Interface"               | `lightning-cli getinfo` succeeds                     | always                                    |
| `cln-application`      | "Web Interface"               | The UI's port is listening                           | always                                    |
| `check-synced`         | "Synced"                      | `getinfo`'s sync warnings, and Bitcoin's block count | always                                    |
| `watchtower-server`    | "TEOS Watchtower Server"      | `teos-cli gettowerinfo` succeeds                     | while the watchtower server is enabled    |
| `watchtowers`          | "Watchtowers"                 | `listtowers` status of every subscribed tower        | while towers are subscribed               |
| `custom-external-host` | "Custom External Host"        | Always fails, with an explanation                    | while Tor Only and a custom host conflict |
| `vpn-tunnel`           | "Clearnet VPN"                | Age of the tunnel's last WireGuard handshake         | while a tunnel is configured  |
| `restored`             | "Backup Restoration Detected" | Always fails, with an explanation                    | after an emergency recovery               |

**`check-synced` distinguishes three states**, which is what makes it worth reading: Bitcoin not yet synced, the node catching up to Bitcoin (reported as a block count against Bitcoin's own), and synced. It fails only when `lightning-cli` itself errors, so a red check here is the node, not the chain.

**`watchtowers` reports the towers this node subscribes to**, by label where one is set. It runs after the registration oneshots, succeeds when every tower is `reachable`, is `loading` while any is `temporary_unreachable` (the client is retrying and queuing appointments), and fails when any is `unreachable`, `misbehaving`, `subscription_error`, or not registered at all — typically an onion tower with Tor not running. Whether other nodes can reach this node's own tower cannot be checked from inside; `watchtower-server` only confirms `teosd` answers.

**`vpn-tunnel` reads the tunnel's last handshake.** `starting` until the first one, `failure` once it is more than three minutes old — WireGuard rekeys about every two minutes under traffic. A failing tunnel does not leak: the routing rules the package installs send clearnet traffic nowhere but the tunnel, and drop it if the tunnel's interface goes away, so it is never sent over the ISP connection. The `vpn` oneshot that brings the tunnel up runs before `lightningd` and blocks it if the tunnel cannot be created.

**Two checks are deliberate permanent failures**, used as a way to say something the interface has nowhere else to put. `custom-external-host` reports that an announced address is being suppressed by Tor Only, and names both settings to change. `restored` reports that an emergency recovery has happened and that the node should be drained and reinstalled rather than kept in service — a state that is not a fault in the running software but is a serious one for the operator.

## Backups and Restore

The `main` volume is copied wholesale — `sdk.Backups.ofVolumes('main')` — but the exclusions are the substance, because **the channel database is deliberately not backed up.**

- **Excluded:** `lightningd.sqlite3` and its write-ahead sidecars, the RPC socket, the gossip store, and the application log.
- **Included:** `hsm_secret`, `config`, `store.json`, the emergency-recovery file, the watchtower's data, and the UI's settings.

Restoring a Lightning node's channel database is dangerous — a stale copy claims a channel state the network has moved past — so this package does not restore one. What comes back is the node's identity and enough to recover funds, not a resumable node.

**What a restore therefore does, automatically:**

1. The emergency-recovery file is copied aside before anything runs. Upstream's own plugin rewrites that file to describe the _current_ channel set, so the restored copy is the last record able to reconstruct the pre-backup channels, and the copy is never touched again.
2. `emergencyrecover` runs, and a permanently-failing health check appears saying what that means: **all channels will be force-closed**, funds swept on-chain, and the node should be drained and reinstalled afterwards rather than kept.
3. Ten thousand wallet addresses are pre-generated. A restored database restarts the address counter at zero, and the node only recognises addresses within a fixed window past the highest known-used index — so without this, a rescan silently misses outputs beyond the first gap. The window this widens applies to every later rescan too.
4. The [Rescan Blockchain](#tasks) task is raised, because until it runs the on-chain balance reads zero.

## Limitations and Differences

1. **A restore is a recovery, not a resumption.** Channels are force-closed by design; plan to sweep the funds and reinstall.
2. **The channel database is excluded from backups**, deliberately.
3. **CLNrest is served as plaintext by the node**, with TLS added at the edge for LAN and clearnet only.
4. **gRPC cannot be reached through a StartOS TLS listener**, terminating or passthrough, because the plugin authenticates clients with their own certificates and its own certificate names only `cln` and `localhost`.
5. **A custom external host is incompatible with Tor Only** and is dropped while both are set.
6. **The watchtower is not configurable.** Its ports, bind addresses, and subscription parameters are fixed.
7. **Plugins are those built into the image.** Adding another means changing the image, not dropping a file on the volume.
8. **No riscv64 build**, and on hardware without a native image the aarch64 build runs emulated.
9. **An `hsm_secret` protected by a passphrase cannot be used.** `hsm-passphrase` (formerly `encrypted-hsm`) prompts on a terminal at startup, which the service does not have. A legacy encrypted secret must be decrypted with `lightning-hsmtool decrypt` before it is copied in.

---

## Quick Reference for AI Consumers

```yaml
package_id: c-lightning
image: ./Dockerfile # on debian:bookworm-slim; plus ghcr.io/elementsproject/cln-application
architectures:
  - x86_64
  - aarch64
subcontainers:
  - lightning-sub # lightningd, teosd, and every oneshot; the one to attach to
  - cln-application-sub # the web UI
volumes:
  main: /root/.lightning
file_models:
  - /root/.lightning/config
  - /root/.lightning/store.json
  - /root/.lightning/data/app/config.json
  - /root/.lightning/.teos/teos.toml
  - /root/.lightning/vpn/wg0.conf # generated from store.json's clearnetVpn on every start
startos_managed_env_vars:
  - TOWERS_DATA_DIR # lightningd
  - BITCOIN_NETWORK # web UI
  - LIGHTNING_DATA_DIR # web UI
  - APP_PROTOCOL # web UI
  - APP_HOST # web UI
  - APP_PORT # web UI
  - APP_CONFIG_FILE # web UI
  - APP_LOG_FILE # web UI
  - LIGHTNING_VARS_FILE # web UI
  - LIGHTNING_WS_PORT # web UI
  - LIGHTNING_REST_PORT # web UI
  - LIGHTNING_REST_PROTOCOL # web UI
  - LIGHTNING_GRPC_PORT # web UI
dependencies:
  - bitcoind # required; mounted read-only at /mnt/bitcoin
interfaces:
  ui: { type: ui, port: 4500 }
  rpc: { type: api, port: 8080 }
  peer: { type: p2p, port: 9735 }
  grpc: { type: api, port: 2106 } # raw TCP forward; the plugin's own mutual TLS
  clnrest: { type: api, port: 3010 } # when enabled; URL carries the rune
  websocket: { type: api, port: 7272 } # when the Clams websocket is enabled
  watchtower: { type: api, port: 9814 } # when the watchtower server is enabled
actions:
  - config
  - plugins
  - experimental
  - watchtower
  - watchtower-info # hidden unless the server is enabled
  - watchtower-client-info # hidden unless clients are registered
  - createrune
  - revoke-runes
  - display-seed # hidden with no wallet; disabled on a pre-BIP-39 wallet
  - rescan-blockchain
  - reset-password
  - delete-gossip-store # only-stopped
  - node-info
  - clboss-status # only-running; disabled unless CLBOSS is enabled
  - clboss-ignore-onchain # only-running; disabled unless CLBOSS is enabled
  - clboss-notice-onchain # only-running; disabled unless CLBOSS is enabled
  - clboss-unmanage # only-running; disabled unless CLBOSS is enabled
  - pay-invoice # only-running; a companion service may raise it as a task
  - receive-payment # only-running
  - clearnet-vpn # hidden; raised as a task by a companion package
tasks:
  - { action: rescan-blockchain, severity: important } # raised after a restore
  - { action: clearnet-vpn, severity: important } # only when a companion package raises it
health_checks:
  - lightningd # displayed "RPC Interface"
  - cln-application # displayed "Web Interface"
  - check-synced # displayed "Synced"
  - watchtower-server # when the watchtower server is enabled
  - watchtowers # while towers are subscribed; per-tower listtowers status
  - custom-external-host # only while Tor Only conflicts with a custom host
  - vpn-tunnel # displayed "Clearnet VPN"; only while a tunnel is configured; last-handshake age
  - restored # only after an emergency recovery
```


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


## Read-only controller transport proof

The optional `rpc` image-pair fixture tests CLN REST over certificate-verified
HTTPS using a separate restricted rune for each disposable node. The rune
permits only `getinfo` and `listpeerchannels`, with zero parameters. The client
checks the expected node ID and network before requesting channel information,
refuses redirects and write methods, limits response size, and never retries.
Returned reports omit node IDs, credentials and raw RPC errors.

```sh
python3 tests/test_read_only_rpc.py -v
bash scripts/test-image-pair.sh \
  btc-cln:swap-preparation xbt-cln:recovery-test ../bitcoind rpc
```

No image rebuild is required: the launcher mounts the new fixture and client.
Both image nodes run on isolated loopback with fresh regtest wallets. The test
checks trusted HTTPS, rejection of an untrusted certificate, identity/network
mismatches, missing and invalid credentials, disallowed methods and parameters,
and rune revocation. The existing `all` mode retains its four funded swap tests;
run `rpc` separately.

This is a transport compatibility test, not a deployed controller. It creates
no live credentials, changes no StartOS interfaces, and enables no live gates.
The probe rune is deliberately insufficient for swap execution. A later
controller integration must define and test its separate operational authority.


## Dedicated read-only controller credential (26.6.8:7)

Coordinator Preparation now includes Controller Credential Status, Create or
Show Read-only Controller Credential, and Revoke Read-only Controller
Credential. Prepare Coordinator must have succeeded before creation/export.
The creation action requires confirmation and masks the copyable rune. Status
never returns it. Use this credential only over certificate-verified HTTPS;
these actions do not create an endpoint, change the existing CLN REST interface,
or grant swap execution permissions.

The rune permits exactly `getinfo` or `listpeerchannels`, with zero parameters.
Repeated creation returns the same active rune. A durable `creating` record is
written before CLN is called; if the reply is lost, further creation is blocked
for inspection. Do not delete that record to retry. Revocation pins the saved
rune ID and can reconcile a lost reply. Unrelated runes are not revoked.
Revoked credentials are not automatically replaced by this initial version.

The private `controller-read-only.json` record stays on the main volume and is
included in backups. It binds the credential to the node and records intent;
it is not proof that a credential remains valid or revoked after restoring
CLN's database. Preparation is invalidated on restore, and the helper checks
CLN's stored rune and blacklist before export/status/revocation. It refuses a
missing or changed rune and a saved revocation that is no longer effective.
Treat a restored node's credentials as requiring inspection; this patch does
not claim to preserve CLN revocation history through backup restoration.

Validate on the packaging VM before building/installing:

```sh
python3 tests/test_controller_credential.py -v
python3 tests/test_read_only_rpc.py -v
npm run check
npm run build
node scripts/check-btc-bundle.cjs
bash scripts/test-image-pair.sh \
  btc-cln:swap-preparation xbt-cln:recovery-test ../bitcoind rpc
```

The image fixture now also exercises the actual BTC credential helper against
regtest CLN: repeated creation, HTTPS authentication, filtered status, exact
revocation and repeated revocation. It mounts the helper, so no image rebuild
is needed for that test. Building the updated StartOS package does require a
new image; the installed package remains unchanged until then.

## Bounded BTC gate activation (26.6.8:8)

`BTC Swap Gate Status` reports configured versus actually running state. The
package is inert by default. `Enable Bounded BTC Swap Gate` requires explicit
confirmation, successful Coordinator Preparation, the original wallet identity,
a connected normal BTC channel and no pending HTLCs. Restart Core Lightning
manually after enabling, then check status. Do not repeat a channel opening.

This activates the existing pinned `live-pilot-v1` gate: one quote only,
exactly 1,000 BTC sats for 2,000 XBT sats, with incoming CLTV bounds of
288–2016 blocks. This is a development test ratio, not a market price or a
complete cross-chain timing policy. No invoice is published, no credential is
created, and no payment is submitted by these actions. The Swap Controller
still refuses live execution. Existing read-only controller credentials are
unchanged and cannot query this gate; use the local status action.

Gate code stays in the image and is checked against its pinned SHA256.
The journal is stored persistently at `bitcoin/swap-gate/quote_plugin.quotes.json`
on the main volume. Its records and preimages must never be manually removed.
Unrelated incoming payments pass through the live gate unchanged.
Activation is bound to the prepared node ID and hash of the wallet secret;
changed secrets, source bytes, symlinks and pre-existing unowned journals are
refused. There is no disable/reset action that could abandon a held payment.

Backups retain gate journals but exclude activation authority. Restore writes
`btc-gate-restored.json` and removes activation before normal service startup;
re-enabling a restored gate is blocked. This does not make a stale node backup
safe for resuming live channels or swaps. Existing emergency channel recovery
semantics remain unchanged.

Validation: `tests/test_gate.py` exercises opt-in, identity and restore barriers,
inert startup, runtime status and pinned plugin protocol persistence/replay.
Set `BTC_GATE_TEST_SOURCE` to the pinned image's `quote_plugin.py` when running
that test. The protocol test simulates hook messages; it is not a funded live
swap or proof of cross-chain timing safety.

## BTC gate observation credential

The BTC package 26.6.8:9 adds **Create or Show BTC Gate Observation Credential**,
**BTC Gate Credential Status**, and **Revoke BTC Gate Observation Credential**.
This separate rune permits only parameterless `getinfo` and `xbt-pilot-info`.
The existing monitor rune remains limited to `getinfo` and `listpeerchannels`.
Creation requires coordinator preparation and an active BTC gate. Lost creation
replies remain blocked; revocation targets only this rune and its derivatives.

In Swap Controller 0.1.0:7, use **Pair BTC Gate Observation** and paste that rune.
The saved BTC HTTPS endpoint and CA are reused; both paired node identities are
verified before saving. The credential is bound to the pairing generation, omitted
from controller backups and removed on restore. Replacing node pairing requires
pairing gate observation again. Status never exports the rune or endpoint.

**Live Swap Readiness** freshly verifies the BTC identity and `live-pilot-v1` gate
profile/count. This reports BTC observation only: XBT gate activation remains
unverified, live execution stays disabled, and restore barriers remain intact.
A successful observation does not prove liquidity, fee or cross-chain timing policy.


## Dedicated swap inspection credential (26.6.8:10)

Use **Create or Show BTC Inspection Credential** under Coordinator
Preparation to mint or reveal the separate read-only preflight rune. Explicit
confirmation is required. Its exact method allowlist is `decode`, `getinfo`,
`listfunds`, `listpeerchannels`, and `listsendpays`; it has no payment, gate,
channel-management or credential-management authority. These reads expose
wallet, channel and payment history information, so keep the rune private.
The existing monitor and gate observer credentials retain their scopes.

Paste this masked rune only into the Swap Controller live inspection form.
Creation requires coordinator preparation but does not activate any gate.
Repeating creation returns the same active rune. Status never reveals it.
Revoke targets only this rune ID and derivatives. A lost creation reply leaves
a durable creating record and cannot automatically mint another rune. Revoked
or interrupted credentials require separate inspection, not file deletion.

The private receipt `controller-inspection-read-only.json` and lock are
excluded from backups; the receipt is removed on restore. This does not revoke
an externally retained rune on a still-running original node. Inspection grants
no execution authority, and existing gate restore barriers remain in effect.


## Hash-bound forward recovery release

The packaged gate adapter adds xbt-release-bound with named payment_hash and
preimage parameters. Both must be canonical 32-byte hex values, and SHA256 of
the preimage must equal the supplied hash. Invalid input returns a fixed error
without entering release or changing the journal. Valid input enters the original
pinned gate's release path in the same process: the existing held-HTLC lookup,
durable resolution write and hook response ordering are retained. No source pin
or existing journal format changes. The adapter verifies the pinned gate hash.

The legacy xbt-release RPC remains available for compatibility. New dedicated
post-close recovery runes must allow only xbt-release-bound for the intended
payment_hash, not the legacy RPC. The adapter alone does not restrict old runes
or enable controller live execution. Activation and restore barriers are unchanged.

The local bound-release tests exercise the pinned gate's actual journal, invalid
requests, valid resolution and restart replay. Rebuild the BTC Docker image for
funded validation; no StartOS install or version bump is part of this checkpoint.

## Explicit forward pilot authority

This candidate adds **Authorize BTC Forward Pilot**. It authorizes one immutable
contract prepared by Swap Controller 0.1.0:12: 1,000 BTC sats in and 2,000 XBT sats
out, using the existing direct channels. Installing this version does not grant
authority or start a payment. The image-owned pilot plugin remains inert until
this local action is explicitly confirmed.

Paste the complete reviewed contract JSON into the action. Confirm the node
identities, channel funding pins and recipient with the controller review, then
return the displayed pilot ID and masked rune to the controller. The rune only
permits `swap-pilot-observe` and `swap-pilot-step` for this exact contract. The
node-side implementation fixes the amounts, recipient, route, original payment
attempt and permitted channel/gate operations; it exposes no generic RPC proxy.
An XBT grant can spend the contract's 2,000 sats. A BTC grant can publish its
invoice, resolve its bound gate, or force-close its selected channel for deadline
protection. These are execution credentials, separate from inspection credentials.

There is one contract slot per node. Repeating authorization for the identical
contract returns the same credential; another contract is refused. An expired
or interrupted enrollment needs inspection, not deletion of the journal or
blind replacement. Unknown mutation replies are reconciled from original node
evidence; an intent without sufficient evidence blocks further submission.

The authority record is private and excluded from backups. Restore creates a
persistent pilot barrier, alongside the existing gate barrier. It cannot resume
old execution or be cleared by re-pairing. Keep both nodes and Swap Controller
running until completion. A forced close can cost more than the pilot amount.

Validation for this candidate includes local unit/action/build checks. Its new
funded pilot matrix must pass on the packaging VM before installation and live
approval. Regtest uses a fixture-only currency adapter; that adapter is never
included in service images and does not prove live-chain timing safety.

## Core Lightning 26.06.9 security update

This revision carries the upstream 26.06.9 security update, including channel
reestablishment, shutdown HTLC deadlines, splicing, onchaind, gossip throttling,
rune authorization and persistent configuration hardening. The BTC package
uses the signed release binaries. The XBT package retains its existing fork,
network identity and database lineage and builds with a checksum-pinned source
overlay of the 26.06.9 fixes; it is not a downgrade to the stable BTC binary.
Swap/gate Python source pins are unchanged. Existing channels use the same
persistent data. Do not replace XBT with an unmodified Bitcoin CLN package.

The CLBOSS Auto Close packaging fix is also included: its configuration is
written as `clboss-auto-close=true` rather than a bare flag. Existing values are
normalized by the regular config writer. Start SDK remains 2.0.9.

The security build must pass its image checks and the funded pilot matrix
before pilot approval. The customer VM's separate XBT daemon also needs the
updated XBT binary; updating the StartOS coordinator does not update that VM.

Upstream release: https://github.com/ElementsProject/lightning/releases/tag/v26.06.9
StartOS SDK-2 release: https://github.com/Start9Labs/cln-startos/releases/tag/v26.6.9_0

## Bounded repeat-swap grant

**Enable Repeat Swap Grant** creates a reusable controller credential pinned to one connected channel, for 1–10 fixed 1,000 BTC sat → 2,000 XBT sat enrollments (default 5). New enrollment expires after 24 hours. Copy this credential into the controller's **Pair Repeat Swap Grants** action once. Leave New grant off to retrieve the same credential without renewing its budget. Explicit replacement requires all previous enrollments to be terminal.

Each enrolled contract consumes a slot, including failed or expired swaps. **Pause New Swap Enrollments** stops new contracts while preserving recovery for already enrolled contracts. The credential cannot issue arbitrary node RPCs. Deadline protection can force-close the pinned BTC channel and incur on-chain fees. Restore barriers remain enforced.

The first pilot record and prior quote history are preserved. Repeat contracts have separate durable records; exact retries reuse their original slot. Restart the BTC coordinator after first enabling repeat mode if requested. The controller then offers invoice-only preparation, explicit confirmation, and swap history. Candidate funded regtests must pass before installation.


### Routed forward swap candidate

Enable Repeat Swap Grant now has an explicit **Allow routed swaps** option,
off by default. Existing direct grants keep their original scope. After all old
swaps finish, select New grant to change modes. An empty channel field in routed
mode snapshots up to eight currently connected, normal, idle local channels;
new channels are never added automatically. Grant expiry, slot consumption,
pause and restore barriers retain their previous behavior.

The fixed swap remains 1,000 BTC sats for 2,000 XBT sats. The XBT coordinator may
spend at most 10 additional XBT sats in routing fees, with a maximum of four hops
and 80 blocks total outgoing CLTV. The final hop receives exactly 2,000 sats with
40 blocks CLTV. There is one payment part and one outgoing attempt, with no
payment retry or replanning after approval. Only invoice-bound read-only planning
is added to the restricted session wrapper; no raw RPC authority is granted.

The BTC invoice advertises eligible approved receiving channels using the peer's
observed fee and CLTV policy. Private-channel route hints expose those channels
to the payer, who still needs a reachable path to a hinted peer. The accepted
incoming HTLC selects the actual approved channel. Its funding identity, HTLC ID
and expiry are durably recorded before outgoing submission; deadline protection
can close only that original channel. An unapproved channel or changed funding
blocks outgoing submission. Existing mutation intents remain observe-only after
an uncertain reply.

The route conversion helper is vendored unchanged from
`tools/blake2b/reverse_route.py` at source commit
`81ba4099a63e5a0e83f55cead53c54f2a1b3c1fe`. The new wrapper and contract validation
apply the fixed forward-swap limits independently. Public routes and bounded
BOLT11 route hints are supported; multipath, blinded routing, automatic retries
and reverse routed swaps are outside this candidate.

Local regression tests cover the new bindings and preserve direct repeat flows.
Funded six-node validation is provided by the controller's `--routed` harness;
its execution on the packaging VM is required before installing this candidate.


Private incoming BTC route hints follow CLN's SCID-alias rules: negotiated
alias channels require the peer's remote alias; a missing alias is not replaced
with the funding SCID. Legacy private channels prefer an available remote alias.
The approved funding pin and the actual incoming HTLC binding remain unchanged.
The funded routed fixture checks the advertised alias before paying and reports
the payer's error directly if it exits before the gate accepts its HTLC.

### Grant renewal after a completed swap channel closes

A routed grant snapshots its channel pins when created. Supplying a short channel
ID restricts that snapshot to that channel; leaving the field empty includes up
to eight currently normal, connected, idle local channels. Adding or closing
channels does not modify an existing grant. Finish current swaps, explicitly
replace the affected coordinator grant, and pair the replacement credential.

Historical completion no longer requires the original channel to remain normal.
The node still checks the saved contract, outcome, exact funding pin and incoming
HTLC binding. For retained non-normal channels it additionally verifies the
original HTLC's terminal wallet state using local `listhtlcs`; missing or
ambiguous evidence blocks renewal. Once CLN archives a fully resolved channel,
`listclosedchannels` must match every original pin field. Original journals are
never rebound or cleared. A recorded deadline close, unresolved outcome, changed
binding/funding, or restore barrier still blocks renewal. These local reads do
not expand remote rune permissions. Unpaid retirement must remain unbound.
