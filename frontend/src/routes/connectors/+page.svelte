<script lang="ts">
	import Icon from '$lib/components/Icon.svelte';

	let { data } = $props();

	type Connector = {
		id: string;
		name: string;
		category: string;
		tagline: string;
		description: string;
		status: 'connected' | 'available';
		account?: string;
		capabilities: string[];
		tone: string;
		highlight: boolean;
	};

	// Server-loaded catalog. Local "connected" overrides let the demo flip an
	// available connector to connected optimistically (no real OAuth needed).
	const loaded = $derived<Connector[]>(data.connectors ?? []);
	let justConnected = $state<Set<string>>(new Set());

	const connectors = $derived(
		loaded.map((c) =>
			justConnected.has(c.id) ? { ...c, status: 'connected' as const } : c
		)
	);

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

	function openOrb(prompt?: string) {
		window.dispatchEvent(new CustomEvent('lode:open', { detail: { prompt } }));
	}

	function connect(c: Connector) {
		justConnected = new Set(justConnected).add(c.id);
		openOrb(`I just connected ${c.name}. What can you do for me now that it's linked?`);
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
		Connect the platforms your music already lives on, and let Lode reason and act
		across them — one agentic control plane for the whole business.
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
							<button class="cx-connect" onclick={() => connect(c)}>
								<Icon name="plus" size={14} color="var(--sg-700)" /> Connect
							</button>
						</div>
					{/each}
				</div>
			</section>
		{/if}
	{/if}
</div>

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
</style>
