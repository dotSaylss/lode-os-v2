<script lang="ts">
	import { fade, scale } from 'svelte/transition';
	import { invalidateAll } from '$app/navigation';
	import { api } from '$lib/api';
	import Icon from '$lib/components/Icon.svelte';

	let { data } = $props();

	type CapSchema = { key: string; label: string; description: string };
	type Connector = {
		id: string;
		name: string;
		category: string;
		tagline: string;
		description: string;
		status: 'connected' | 'available';
		account?: string;
		capabilities: string[];
		capabilities_schema: CapSchema[];
		tone: string;
		highlight: boolean;
	};

	// Server-loaded catalog; connection state is persisted server-side, so the
	// list refreshes via invalidateAll() after the connect flow completes.
	const connectors = $derived<Connector[]>(data.connectors ?? []);

	let activeCategory = $state<string>('all');

	const CATEGORY_LABELS: Record<string, string> = {
		creation: 'Creation',
		royalties: 'Royalties',
		sync_licensing: 'Sync Licensing',
		distribution: 'Distribution',
		rights_org: 'Rights Orgs'
	};
	const label = (cat: string) => CATEGORY_LABELS[cat] ?? cat;

	const AV_TONE: Record<string, string> = {
		sage: 'av-sage',
		terra: 'av-terra',
		slate: 'av-slate',
		amber: 'av-amber'
	};
	const avTone = (t: string) => AV_TONE[t] ?? 'av-slate';
	const initial = (name: string) => name.charAt(0).toUpperCase();

	const categories = $derived([
		'all',
		...Array.from(new Set(connectors.map((c) => c.category)))
	]);

	const visible = $derived(
		activeCategory === 'all'
			? connectors
			: connectors.filter((c) => c.category === activeCategory)
	);
	const connected = $derived(visible.filter((c) => c.status === 'connected'));
	const available = $derived(visible.filter((c) => c.status === 'available'));
	const connectedCount = $derived(connectors.filter((c) => c.status === 'connected').length);

	// ── Connect flow (consent-style authorization wizard) ────────────────────
	// Mirrors connecting a third-party tool to an assistant: review the access
	// being requested → authorize → land connected with safe permission
	// defaults (reads allowed, platform-changing actions need approval).
	type WizardStep = 'consent' | 'connecting' | 'done';
	let wizard = $state<{
		connector: Connector;
		step: WizardStep;
		account: string;
		error: string;
	} | null>(null);

	function openConnect(c: Connector) {
		wizard = { connector: c, step: 'consent', account: 'Lode Records', error: '' };
	}

	function closeWizard() {
		if (wizard?.step === 'connecting') return;
		wizard = null;
	}

	// Permission each scope will start at, per the backend's consent defaults.
	const seededPermission = (key: string) =>
		key.startsWith('auto_')
			? 'Denied'
			: key.startsWith('read_') || key.startsWith('track_')
				? 'Allowed'
				: 'Needs approval';

	async function authorize() {
		if (!wizard) return;
		wizard.step = 'connecting';
		wizard.error = '';
		// Hold the handshake on screen long enough to read, even on localhost.
		const minDelay = new Promise((r) => setTimeout(r, 1400));
		try {
			const res = await fetch(api(`/api/v1/connectors/${wizard.connector.id}/connect`), {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ account: wizard.account || 'Lode Records' })
			});
			await minDelay;
			if (!res.ok) throw new Error('connect failed');
			wizard.step = 'done';
			await invalidateAll();
		} catch {
			wizard.step = 'consent';
			wizard.error = 'The connection could not be completed. Is the backend running?';
		}
	}
</script>

<div class="v3-stage-wide">
	<header class="v3-header">
		<div>
			<span class="v3-date">Connectors</span>
			<h1>Your music runs on connections</h1>
		</div>
		<div class="v3-header-recovered">
			<span>Linked platforms</span>
			<b>{connectedCount} connected</b>
		</div>
	</header>

	<p class="cx-thesis">
		For everyone making new money from a catalog — connect the platforms your music
		already lives on, set what Lode may do on each, and let it reason and act across
		them. One agentic control plane for the whole business.
	</p>

	<!-- The closed loop: the story that makes the connectors more than a list. -->
	<section class="cx-loop">
		<div class="cx-loop-node">
			<span class="cx-loop-ico av-sage">S</span>
			<div>
				<b>Suno</b>
				<span>creates the music</span>
			</div>
		</div>
		<span class="cx-loop-arrow"><Icon name="arrow-right" size={18} color="var(--ink-muted)" /></span>
		<div class="cx-loop-node">
			<span class="cx-loop-ico av-amber">M</span>
			<div>
				<b>Mogul</b>
				<span>holds the catalog &amp; money</span>
			</div>
		</div>
		<span class="cx-loop-arrow"><Icon name="arrow-right" size={18} color="var(--ink-muted)" /></span>
		<div class="cx-loop-node">
			<span class="cx-loop-ico av-terra">D</span>
			<div>
				<b>Disco</b>
				<span>places it for new revenue</span>
			</div>
		</div>
	</section>

	<!-- Filter bar -->
	<div class="cx-filters">
		{#each categories as cat}
			<button
				class="cx-filter {activeCategory === cat ? 'active' : ''}"
				onclick={() => (activeCategory = cat)}
			>
				{cat === 'all' ? 'All' : label(cat)}
			</button>
		{/each}
	</div>

	{#if connectors.length === 0}
		<div class="cx-empty">No connectors loaded. Is the backend running?</div>
	{:else}
		{#if connected.length}
			<section class="cx-group">
				<div class="cx-group-head">
					<span class="eyebrow">Connected</span>
					<span class="cx-pill">{connected.length}</span>
				</div>
				<div class="cx-grid">
					{#each connected as c (c.id)}
						<!-- Slim card: the whole card is the affordance → opens config. -->
						<a class="cx-card cx-card-link {c.highlight ? 'is-hero' : ''}" href="/connectors/{c.id}">
							<span class="cx-dot" title="Connected"></span>
							<span class="cx-logo {avTone(c.tone)}">{initial(c.name)}</span>
							<div class="cx-body">
								<div class="cx-name-row">
									<span class="cx-name">{c.name}</span>
									{#if c.highlight}
										<span class="cx-flag"><Icon name="gem" size={11} color="var(--terra-600)" /> New niche</span>
									{/if}
								</div>
								<p class="cx-tagline">{c.tagline}</p>
							</div>
							<span class="cx-chev"><Icon name="chevron-right" size={18} color="var(--ink-muted)" /></span>
						</a>
					{/each}
				</div>
			</section>
		{/if}

		{#if available.length}
			<section class="cx-group">
				<div class="cx-group-head">
					<span class="eyebrow">Available</span>
					<span class="cx-pill">{available.length}</span>
				</div>
				<div class="cx-grid">
					{#each available as c (c.id)}
						<div class="cx-card">
							<span class="cx-dot cx-dot-off" title="Not connected"></span>
							<span class="cx-logo {avTone(c.tone)}">{initial(c.name)}</span>
							<div class="cx-body">
								<div class="cx-name-row">
									<span class="cx-name">{c.name}</span>
								</div>
								<p class="cx-tagline">{c.tagline}</p>
							</div>
							<button class="cx-connect" onclick={() => openConnect(c)}>
								<Icon name="plus" size={14} color="var(--sg-700)" /> Connect
							</button>
						</div>
					{/each}
				</div>
			</section>
		{/if}
	{/if}
</div>

{#if wizard}
	{@const w = wizard}
	<div
		class="wiz-backdrop"
		transition:fade={{ duration: 150 }}
		onclick={(e) => e.target === e.currentTarget && closeWizard()}
		onkeydown={(e) => e.key === 'Escape' && closeWizard()}
		role="presentation"
	>
		<div
			class="wiz"
			transition:scale={{ duration: 180, start: 0.95 }}
			role="dialog"
			aria-modal="true"
			aria-label="Connect {w.connector.name}"
		>
			{#if w.step === 'consent'}
				<div class="wiz-head">
					<span class="wiz-logo {avTone(w.connector.tone)}">{initial(w.connector.name)}</span>
					<div>
						<h2>Connect {w.connector.name}</h2>
						<p>Lode is requesting access to your {w.connector.name} account</p>
					</div>
				</div>

				<label class="wiz-account">
					<span>Account</span>
					<input bind:value={w.account} placeholder="Account name" />
				</label>

				<div class="wiz-scopes">
					<span class="eyebrow">Lode will be able to</span>
					{#each w.connector.capabilities_schema as cap (cap.key)}
						<div class="wiz-scope">
							<span class="wiz-scope-ico"><Icon name="check" size={13} color="var(--sg-600)" /></span>
							<div class="wiz-scope-text">
								<b>{cap.label}</b>
								<span>{cap.description}</span>
							</div>
							<span class="wiz-scope-perm {seededPermission(cap.key) === 'Allowed' ? 'ok' : ''}">
								{seededPermission(cap.key)}
							</span>
						</div>
					{/each}
				</div>

				<p class="wiz-note">
					You can change what Lode may do — and when it must ask you first — anytime in the
					connector's settings. Authorization is simulated in this demo; no real credentials
					are exchanged.
				</p>

				{#if w.error}
					<p class="wiz-error">{w.error}</p>
				{/if}

				<div class="wiz-actions">
					<button class="wiz-cancel" onclick={closeWizard}>Cancel</button>
					<button class="wiz-go" onclick={authorize}>
						<Icon name="plug" size={15} color="#fff" /> Authorize {w.connector.name}
					</button>
				</div>
			{:else if w.step === 'connecting'}
				<div class="wiz-busy">
					<span class="wiz-spinner"></span>
					<b>Connecting to {w.connector.name}…</b>
					<span>Opening a secure session and exchanging tokens</span>
				</div>
			{:else}
				<div class="wiz-done">
					<span class="wiz-done-ico"><Icon name="circle-check" size={30} color="var(--sg-600)" /></span>
					<h2>{w.connector.name} connected</h2>
					<p>
						Connected as <b>{w.account || 'Lode Records'}</b>. Reads are allowed; actions that
						change anything on {w.connector.name} will ask for your approval first.
					</p>
					<div class="wiz-actions center">
						<button class="wiz-cancel" onclick={closeWizard}>Done</button>
						<a class="wiz-go" href="/connectors/{w.connector.id}" onclick={closeWizard}>
							Review permissions <Icon name="arrow-right" size={14} color="#fff" />
						</a>
					</div>
				</div>
			{/if}
		</div>
	</div>
{/if}

<style>
	.cx-thesis {
		margin: -6px 0 4px;
		max-width: 60ch;
		font-size: 15px;
		line-height: 1.6;
		color: var(--ink-500);
	}

	/* Closed-loop strip */
	.cx-loop {
		display: flex;
		align-items: center;
		gap: 10px;
		flex-wrap: wrap;
		padding: 16px 18px;
		background: var(--paper-0);
		border: 1px solid var(--paper-200);
		border-radius: var(--r-xl);
		box-shadow: var(--v3-sh-sm);
	}
	.cx-loop-node {
		display: flex;
		align-items: center;
		gap: 11px;
		flex: 1;
		min-width: 180px;
	}
	.cx-loop-ico {
		flex: none;
		width: 38px;
		height: 38px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 15px;
		font-weight: 700;
	}
	.cx-loop-node b {
		display: block;
		font-size: 14px;
		font-weight: 600;
		color: var(--ink-900);
	}
	.cx-loop-node span {
		font-size: 12px;
		color: var(--ink-muted);
	}
	.cx-loop-arrow {
		display: flex;
		align-items: center;
	}
	@media (max-width: 720px) {
		.cx-loop-arrow {
			transform: rotate(90deg);
			margin: 0 auto;
		}
	}

	/* Filters */
	.cx-filters {
		display: flex;
		flex-wrap: wrap;
		gap: 7px;
	}
	.cx-filter {
		font-size: 12px;
		font-weight: 600;
		padding: 6px 13px;
		border-radius: var(--r-pill);
		border: 1px solid var(--paper-200);
		background: var(--paper-0);
		color: var(--ink-500);
		transition: all 0.14s;
	}
	.cx-filter:hover {
		border-color: var(--sg-200);
		color: var(--ink-900);
	}
	.cx-filter.active {
		background: var(--sg-500);
		border-color: var(--sg-500);
		color: #fff;
	}

	.cx-group-head {
		display: flex;
		align-items: center;
		gap: 9px;
		margin: 4px 0 14px;
	}
	.cx-pill {
		font-size: 11px;
		font-weight: 600;
		color: var(--ink-500);
		background: var(--paper-100);
		border-radius: var(--r-pill);
		padding: 2px 9px;
	}

	.cx-grid {
		display: grid;
		grid-template-columns: 1fr;
		gap: 12px;
	}
	@media (min-width: 720px) {
		.cx-grid {
			grid-template-columns: 1fr 1fr;
		}
	}

	/* Slim card: dot · logo · name+tagline · trailing affordance */
	.cx-card {
		position: relative;
		display: flex;
		align-items: center;
		gap: 14px;
		padding: 16px 18px;
		background: var(--paper-0);
		border: 1px solid var(--paper-200);
		border-radius: var(--r-lg);
		box-shadow: var(--v3-sh-xs);
		text-decoration: none;
		transition: box-shadow 0.16s, border-color 0.16s, transform 0.16s;
	}
	.cx-card-link:hover {
		box-shadow: var(--v3-sh-md);
		border-color: var(--paper-300);
		transform: translateY(-2px);
	}
	.cx-card-link:hover .cx-chev {
		transform: translateX(2px);
	}
	.cx-card.is-hero {
		border-color: var(--terra-200);
		background: linear-gradient(110deg, var(--terra-50) 0%, var(--paper-0) 60%);
	}
	.cx-card.is-hero:hover {
		border-color: var(--terra-300);
	}

	.cx-dot {
		flex: none;
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: var(--sg-500);
		box-shadow: 0 0 0 3px var(--sg-50);
	}
	.cx-dot-off {
		background: var(--paper-300);
		box-shadow: 0 0 0 3px var(--paper-100);
	}

	.cx-logo {
		flex: none;
		width: 40px;
		height: 40px;
		border-radius: var(--r-sm);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 16px;
		font-weight: 700;
	}
	.av-sage {
		background: var(--sg-100);
		color: var(--sg-700);
	}
	.av-terra {
		background: var(--terra-100);
		color: var(--terra-600);
	}
	.av-slate {
		background: var(--slate-100);
		color: var(--slate-600);
	}
	.av-amber {
		background: var(--amber-50);
		color: var(--amber-600);
	}

	.cx-body {
		min-width: 0;
		flex: 1;
	}
	.cx-name-row {
		display: flex;
		align-items: center;
		gap: 8px;
	}
	.cx-name {
		font-size: 15px;
		font-weight: 600;
		color: var(--ink-900);
	}
	.cx-flag {
		display: inline-flex;
		align-items: center;
		gap: 3px;
		font-size: 10px;
		font-weight: 600;
		color: var(--terra-600);
		background: var(--terra-50);
		border: 1px solid var(--terra-200);
		padding: 2px 7px;
		border-radius: var(--r-pill);
	}
	.cx-tagline {
		margin: 3px 0 0;
		font-size: 12.5px;
		line-height: 1.45;
		color: var(--ink-500);
		overflow: hidden;
		text-overflow: ellipsis;
		display: -webkit-box;
		-webkit-line-clamp: 1;
		line-clamp: 1;
		-webkit-box-orient: vertical;
	}

	.cx-chev {
		flex: none;
		display: flex;
		align-items: center;
		transition: transform 0.16s;
	}

	.cx-connect {
		flex: none;
		display: inline-flex;
		align-items: center;
		gap: 5px;
		font-size: 12.5px;
		font-weight: 600;
		color: var(--sg-700);
		background: var(--sg-50);
		border: 1px solid var(--sg-100);
		padding: 7px 13px;
		border-radius: var(--r-sm);
		transition: all 0.14s;
	}
	.cx-connect:hover {
		background: var(--sg-100);
		border-color: var(--sg-200);
	}

	.cx-empty {
		padding: 24px;
		text-align: center;
		border: 1px dashed var(--paper-300);
		border-radius: var(--r-lg);
		font-size: 14px;
		color: var(--ink-muted);
	}

	.v3-stage-wide > * + * {
		margin-top: 22px;
	}

	/* ── Connect wizard ──────────────────────────────────────────────────── */
	.wiz-backdrop {
		position: fixed;
		inset: 0;
		z-index: 80;
		background: color-mix(in oklab, var(--ink-900) 26%, transparent);
		backdrop-filter: blur(3px);
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 24px;
	}
	.wiz {
		width: 460px;
		max-width: 100%;
		max-height: calc(100vh - 48px);
		overflow-y: auto;
		background: var(--paper-0);
		border: 1px solid var(--paper-200);
		border-radius: var(--r-xl);
		box-shadow: var(--v3-sh-xl);
		padding: 26px 26px 22px;
	}

	.wiz-head {
		display: flex;
		align-items: center;
		gap: 14px;
	}
	.wiz-logo {
		flex: none;
		width: 46px;
		height: 46px;
		border-radius: var(--r-md);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 19px;
		font-weight: 700;
	}
	.wiz-head h2 {
		margin: 0;
		font-size: 18px;
		font-weight: 600;
		color: var(--ink-900);
	}
	.wiz-head p {
		margin: 3px 0 0;
		font-size: 12.5px;
		color: var(--ink-500);
	}

	.wiz-account {
		display: flex;
		flex-direction: column;
		gap: 5px;
		margin-top: 18px;
	}
	.wiz-account span {
		font-size: 11px;
		font-weight: 600;
		letter-spacing: 0.03em;
		text-transform: uppercase;
		color: var(--ink-muted);
	}
	.wiz-account input {
		font-size: 13.5px;
		color: var(--ink-900);
		background: var(--paper-50);
		border: 1px solid var(--paper-200);
		border-radius: var(--r-sm);
		padding: 9px 12px;
		outline: none;
		transition: border-color 0.15s;
	}
	.wiz-account input:focus {
		border-color: var(--sg-300);
	}

	.wiz-scopes {
		margin-top: 18px;
		display: flex;
		flex-direction: column;
		gap: 2px;
	}
	.wiz-scopes .eyebrow {
		margin-bottom: 8px;
	}
	.wiz-scope {
		display: flex;
		align-items: flex-start;
		gap: 10px;
		padding: 9px 0;
		border-top: 1px solid var(--paper-100);
	}
	.wiz-scope:first-of-type {
		border-top: none;
	}
	.wiz-scope-ico {
		flex: none;
		width: 22px;
		height: 22px;
		border-radius: 50%;
		background: var(--sg-50);
		display: flex;
		align-items: center;
		justify-content: center;
		margin-top: 1px;
	}
	.wiz-scope-text {
		flex: 1;
		min-width: 0;
	}
	.wiz-scope-text b {
		display: block;
		font-size: 13px;
		font-weight: 600;
		color: var(--ink-900);
	}
	.wiz-scope-text span {
		font-size: 12px;
		line-height: 1.4;
		color: var(--ink-500);
	}
	.wiz-scope-perm {
		flex: none;
		font-size: 10.5px;
		font-weight: 600;
		color: var(--amber-600);
		background: var(--amber-50);
		border-radius: var(--r-pill);
		padding: 3px 9px;
		margin-top: 2px;
	}
	.wiz-scope-perm.ok {
		color: var(--sg-700);
		background: var(--sg-50);
	}

	.wiz-note {
		margin: 16px 0 0;
		font-size: 11.5px;
		line-height: 1.5;
		color: var(--ink-muted);
	}
	.wiz-error {
		margin: 12px 0 0;
		font-size: 12.5px;
		color: var(--terra-600);
	}

	.wiz-actions {
		display: flex;
		justify-content: flex-end;
		gap: 10px;
		margin-top: 20px;
	}
	.wiz-actions.center {
		justify-content: center;
	}
	.wiz-cancel {
		font-size: 13.5px;
		font-weight: 600;
		color: var(--ink-500);
		background: transparent;
		border: 1px solid var(--paper-200);
		padding: 10px 16px;
		border-radius: var(--r-md);
		cursor: pointer;
		transition: all 0.14s;
	}
	.wiz-cancel:hover {
		border-color: var(--sg-200);
		color: var(--ink-900);
	}
	.wiz-go {
		display: inline-flex;
		align-items: center;
		gap: 7px;
		font-size: 13.5px;
		font-weight: 600;
		color: #fff;
		background: var(--sg-500);
		border: none;
		padding: 10px 17px;
		border-radius: var(--r-md);
		cursor: pointer;
		text-decoration: none;
		transition: background 0.15s;
	}
	.wiz-go:hover {
		background: var(--sg-600);
	}

	.wiz-busy {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 10px;
		padding: 34px 8px 30px;
		text-align: center;
	}
	.wiz-busy b {
		font-size: 15px;
		font-weight: 600;
		color: var(--ink-900);
	}
	.wiz-busy > span:last-child {
		font-size: 12.5px;
		color: var(--ink-muted);
	}
	.wiz-spinner {
		width: 26px;
		height: 26px;
		border-radius: 50%;
		border: 3px solid var(--sg-100);
		border-top-color: var(--sg-500);
		animation: wiz-spin 0.8s linear infinite;
		margin-bottom: 6px;
	}
	@keyframes wiz-spin {
		to {
			transform: rotate(360deg);
		}
	}

	.wiz-done {
		text-align: center;
		padding: 10px 6px 4px;
	}
	.wiz-done-ico {
		display: inline-flex;
		width: 54px;
		height: 54px;
		border-radius: 50%;
		background: var(--sg-50);
		align-items: center;
		justify-content: center;
	}
	.wiz-done h2 {
		margin: 14px 0 0;
		font-size: 18px;
		font-weight: 600;
		color: var(--ink-900);
	}
	.wiz-done p {
		margin: 8px auto 0;
		max-width: 38ch;
		font-size: 13px;
		line-height: 1.55;
		color: var(--ink-500);
	}
	.wiz-done p b {
		color: var(--ink-900);
		font-weight: 600;
	}
</style>
