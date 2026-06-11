<script lang="ts">
	import { tick } from 'svelte';
	import { slide } from 'svelte/transition';
	import LabelAgentChat from '$lib/components/LabelAgentChat.svelte';
	import Icon from '$lib/components/Icon.svelte';
	import { pendingAsk, clearPending } from '$lib/lodeStore';

	type Gap = { type: string; organization: string };
	type Artist = {
		id: string;
		name: string;
		ytd_earnings: number;
		total_uncollected: number;
		gaps: Gap[];
	};

	let { data } = $props();
	let p = $derived(data.portfolio as any);
	let forecast = $derived(data.forecast as any);

	// Forecast curve geometry for the inline SVG sparkline.
	let curve = $derived.by(() => {
		const pts = forecast?.forecast ?? [];
		const max = forecast?.total_recoverable || 1;
		if (pts.length === 0) return { line: '', area: '', last: { x: 0, y: 100 } };
		const W = 100,
			H = 100;
		const coords = pts.map((d: { cumulative_recovered: number }, i: number) => {
			const x = pts.length > 1 ? (i / (pts.length - 1)) * W : 0;
			const y = H - (d.cumulative_recovered / max) * H;
			return { x, y };
		});
		const line = coords
			.map((c: { x: number; y: number }, i: number) => `${i === 0 ? 'M' : 'L'}${c.x.toFixed(2)},${c.y.toFixed(2)}`)
			.join(' ');
		const area = `${line} L${W},${H} L0,${H} Z`;
		return { line, area, last: coords[coords.length - 1] };
	});

	let chat = $state<LabelAgentChat>();

	// The agent panel (with its A2A trace) stays out of the way until the orb
	// hands off a question or the user runs the bulk action — then it reveals
	// full-width in place, where the handoff trace renders at full size.
	let panelOpen = $state(false);
	let panelEl: HTMLDivElement | undefined = $state();

	async function revealPanel() {
		panelOpen = true;
		await tick();
		panelEl?.scrollIntoView({ behavior: 'smooth', block: 'start' });
	}

	// React to an orb handoff even when we're already on this route (goto to the
	// current path won't remount, so onMount alone would miss it). One-shot.
	$effect(() => {
		const pending = $pendingAsk;
		if (pending && pending.page === '/label') {
			clearPending();
			revealPanel().then(async () => {
				if (!chat) await tick(); // one more flush in case the bind hasn't resolved
				chat?.ask(pending.prompt);
			});
		}
	});

	const fmt = (n: number) =>
		new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD',
			maximumFractionDigits: 0
		}).format(n || 0);
	const fmtCents = (n: number) =>
		new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n || 0);

	// Roster sorted by biggest uncollected opportunity first.
	let roster = $derived(
		[...((p?.artists as Artist[]) || [])].sort(
			(a, b) => (b.total_uncollected || 0) - (a.total_uncollected || 0)
		)
	);

	// Muted category tones (sage / amber / clay / slate — never loud).
	const gapTone = (type: string) => {
		switch (type) {
			case 'neighboring_rights':
				return 'tone-clay';
			case 'unclaimed_mechanicals':
				return 'tone-amber';
			case 'sync_unmatched':
				return 'tone-slate';
			case 'pro_blackbox':
				return 'tone-sage';
			default:
				return 'tone-neutral';
		}
	};

	async function bulkRegister() {
		await revealPanel();
		chat?.ask(
			`Register all ${p.neighboring_rights_artists} artists missing neighboring rights to recover ${fmt(p.neighboring_rights_uncollected)}. Draft the bulk SoundExchange registration now.`
		);
	}

	const initials = (name: string) =>
		name
			.split(' ')
			.map((w: string) => w[0])
			.join('')
			.slice(0, 2);
</script>

<div class="v3-stage-wide">
	<header class="v3-header">
		<div>
			<span class="v3-date">Catalog</span>
			<h1>{p.label_profile?.name ?? 'Label'} catalog</h1>
			<p class="v3-vp">For labels &amp; managers — Lode audits the whole roster at once, then hands bulk recovery to an execution agent you approve.</p>
		</div>
		<div class="v3-header-recovered">
			<span>{p.total_artists} artists managed</span>
			<b>{fmt(p.total_ytd)} YTD</b>
		</div>
	</header>

	<!-- Hero opportunity + KPI row -->
	<div class="lab-grid lab-hero-grid">
		<section class="v3-focus lab-hero">
			<div class="v3-focus-head">
				<span class="v3-focus-eyebrow"><span class="v3-focus-dot"></span> Total uncollected across catalog</span>
				<span class="v3-focus-progress">{p.total_artists} artists scanned</span>
			</div>
			<p class="figure-lg lab-hero-amount">{fmt(p.total_uncollected)}</p>
			<p class="lead lab-hero-sub">
				The single biggest lever: <strong>{p.neighboring_rights_artists} artists</strong> missing
				neighboring rights worth <strong>{fmt(p.neighboring_rights_uncollected)}</strong>.
			</p>
			<div class="v3-focus-foot">
				<div class="v3-focus-amount">
					<b>{fmt(p.neighboring_rights_uncollected)}</b>
					<span>in one bulk action</span>
				</div>
				<button class="v3-act" type="button" onclick={bulkRegister}>
					<Icon name="check" size={17} color="#fff" /> Bulk register {p.neighboring_rights_artists} artists
				</button>
			</div>
		</section>

		<div class="lab-kpis">
			<div class="lab-kpi">
				<span class="eyebrow">Roster YTD earnings</span>
				<p class="figure-lg">{fmt(p.total_ytd)}</p>
			</div>
			<div class="lab-kpi">
				<span class="eyebrow">Artists under management</span>
				<p class="figure-lg">{p.total_artists}</p>
				<p class="lab-kpi-note">{p.neighboring_rights_artists} with open registration gaps</p>
			</div>
		</div>
	</div>

	<!-- Revealable agent panel: holds the live A2A trace when invoked -->
	{#if panelOpen}
		<div class="lab-panel" bind:this={panelEl} transition:slide={{ duration: 280 }}>
			<LabelAgentChat bind:this={chat} />
		</div>
	{/if}

	<!-- Recovery forecast + per-category gap breakdown -->
	{#if forecast?.categories?.length}
		<div class="lab-grid lab-forecast-grid">
			<section class="lab-card lab-breakdown">
				<div class="lab-card-head">
					<span class="eyebrow">Gap breakdown by category</span>
					<span class="lab-pill">{forecast.artists_with_gaps} artists with gaps</span>
				</div>
				<div class="lab-bars">
					{#each forecast.categories as c (c.type)}
						<div class="lab-bar">
							<div class="lab-bar-head">
								<span class="lab-tag {gapTone(c.type)}">{c.label}</span>
								<span class="lab-bar-meta">{c.artists_affected} artists · ~{c.recovery_months}mo</span>
								<span class="mono lab-bar-amount">{fmt(c.recoverable)}</span>
							</div>
							<div class="lab-track">
								<div
									class="lab-fill"
									style="width: {Math.max(2, (c.recoverable / forecast.total_recoverable) * 100)}%"
								></div>
							</div>
						</div>
					{/each}
				</div>
			</section>

			<section class="lab-card lab-forecast">
				<span class="eyebrow">12-month recovery forecast</span>
				<p class="figure-lg lab-forecast-total">{fmt(forecast.total_recoverable)}</p>
				<p class="lab-forecast-note">projected recovered if bulk registration starts now</p>
				<div class="lab-spark">
					<svg viewBox="0 0 100 100" preserveAspectRatio="none">
						<defs>
							<linearGradient id="fc-grad" x1="0" y1="0" x2="0" y2="1">
								<stop offset="0%" stop-color="#577D63" stop-opacity="0.22" />
								<stop offset="100%" stop-color="#577D63" stop-opacity="0" />
							</linearGradient>
						</defs>
						<path d={curve.area} fill="url(#fc-grad)" />
						<path
							d={curve.line}
							fill="none"
							stroke="#577D63"
							stroke-width="1.5"
							vector-effect="non-scaling-stroke"
							stroke-linejoin="round"
							stroke-linecap="round"
						/>
					</svg>
				</div>
				<div class="lab-spark-axis">
					<span>Now</span><span>Month 6</span><span>Month 12</span>
				</div>
			</section>
		</div>
	{/if}

	<!-- Roster table (full width) -->
	<section class="lab-card lab-roster">
		<div class="lab-card-head">
			<span class="eyebrow">Catalog roster</span>
			<span class="lab-pill">sorted by opportunity</span>
		</div>
		<div class="lab-table-scroll">
			<table class="lab-table">
				<thead>
					<tr>
						<th>Artist</th>
						<th class="num">YTD</th>
						<th class="gaps">Gaps</th>
						<th class="num">Uncollected</th>
					</tr>
				</thead>
				<tbody>
					{#each roster as a (a.id)}
						<tr>
							<td>
								<div class="lab-artist">
									<span class="lab-avatar">{initials(a.name)}</span>
									<span class="lab-artist-name">{a.name}</span>
								</div>
							</td>
							<td class="num mono lab-ytd">{fmt(a.ytd_earnings)}</td>
							<td class="gaps">
								{#if a.gaps.length === 0}
									<span class="lab-clear"><span class="lab-clear-dot"></span> All clear</span>
								{:else}
									<div class="lab-gap-row">
										{#each a.gaps as g}
											<span class="lab-tag {gapTone(g.type)}">{g.organization}</span>
										{/each}
									</div>
								{/if}
							</td>
							<td class="num mono">
								{#if a.total_uncollected > 0}
									<span class="lab-uncollected">{fmtCents(a.total_uncollected)}</span>
								{:else}
									<span class="lab-dash">—</span>
								{/if}
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	</section>
</div>

<style>
	.lab-grid {
		display: grid;
		grid-template-columns: 1fr;
		gap: 22px;
		margin-bottom: 22px;
	}
	@media (min-width: 1024px) {
		.lab-hero-grid {
			grid-template-columns: 2fr 1fr;
		}
		.lab-forecast-grid {
			grid-template-columns: 2fr 1fr;
		}
	}

	.lab-panel {
		margin-bottom: 22px;
		height: 560px;
	}

	.lab-hero {
		margin-bottom: 0;
	}
	.lab-hero-amount {
		font-size: 52px;
		letter-spacing: -0.03em;
		color: var(--clay-600);
		margin: 4px 0 12px;
	}
	.lab-hero-sub {
		margin: 0 0 4px;
	}
	.lab-hero-sub strong {
		color: var(--ink-900);
		font-weight: 600;
	}

	.lab-kpis {
		display: flex;
		flex-direction: column;
		gap: 22px;
	}
	.lab-card,
	.lab-kpi {
		background: var(--paper-0);
		border: 1px solid var(--paper-200);
		border-radius: var(--r-2xl);
		box-shadow: var(--v3-sh-sm);
	}
	.lab-kpi {
		padding: 22px 24px;
		flex: 1;
		display: flex;
		flex-direction: column;
		justify-content: center;
	}
	.lab-kpi .figure-lg {
		margin: 8px 0 0;
		font-size: 34px;
	}
	.lab-kpi-note {
		margin: 4px 0 0;
		font-size: 12px;
		color: var(--ink-muted);
	}

	.lab-card {
		padding: 26px 28px;
		margin-bottom: 22px;
		min-width: 0;
	}
	@media (max-width: 520px) {
		.lab-card {
			padding: 20px 18px;
		}
	}
	.lab-card-head {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 18px;
	}
	.lab-pill {
		font-size: 11px;
		font-weight: 500;
		color: var(--ink-500);
		background: var(--paper-100);
		border-radius: var(--r-pill);
		padding: 5px 12px;
	}

	/* category bars */
	.lab-bars {
		display: flex;
		flex-direction: column;
		gap: 18px;
	}
	.lab-bar-head {
		display: flex;
		align-items: center;
		gap: 10px;
		margin-bottom: 7px;
	}
	.lab-bar-meta {
		font-size: 11.5px;
		color: var(--ink-muted);
		flex: 1;
	}
	.lab-bar-amount {
		font-size: 13.5px;
		color: var(--ink-900);
	}
	.lab-track {
		height: 8px;
		width: 100%;
		border-radius: var(--r-pill);
		background: var(--paper-100);
		overflow: hidden;
	}
	.lab-fill {
		height: 100%;
		border-radius: var(--r-pill);
		background: linear-gradient(90deg, var(--sg-300), var(--sg-500));
	}

	/* forecast */
	.lab-forecast {
		display: flex;
		flex-direction: column;
	}
	.lab-forecast-total {
		margin: 6px 0 0;
		font-size: 30px;
	}
	.lab-forecast-note {
		margin: 2px 0 14px;
		font-size: 12px;
		color: var(--ink-muted);
	}
	.lab-spark {
		flex: 1;
		min-height: 120px;
		position: relative;
	}
	.lab-spark svg {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
	}
	.lab-spark-axis {
		display: flex;
		justify-content: space-between;
		margin-top: 8px;
		font-size: 11px;
		color: var(--ink-muted);
		font-family: var(--font-mono);
	}

	/* tags */
	.lab-tag {
		display: inline-flex;
		align-items: center;
		font-size: 11px;
		font-weight: 500;
		border-radius: var(--r-sm);
		padding: 3px 9px;
		border: 1px solid transparent;
		white-space: nowrap;
	}
	.tone-clay {
		background: var(--clay-50);
		color: var(--clay-600);
		border-color: #efd9d1;
	}
	.tone-amber {
		background: var(--amber-50);
		color: var(--amber-600);
		border-color: #efe2cc;
	}
	.tone-slate {
		background: var(--slate-50);
		color: var(--slate-600);
		border-color: var(--slate-100);
	}
	.tone-sage {
		background: var(--sg-50);
		color: var(--sg-700);
		border-color: var(--sg-100);
	}
	.tone-neutral {
		background: var(--paper-100);
		color: var(--ink-500);
		border-color: var(--paper-200);
	}

	/* roster table — pans horizontally on narrow screens instead of pushing
	   the whole page wide. */
	.lab-table-scroll {
		overflow: auto;
		max-height: 540px;
	}
	.lab-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 14px;
	}
	.lab-table thead th {
		position: sticky;
		top: 0;
		background: var(--paper-0);
		text-align: left;
		font-size: 10.5px;
		font-weight: 600;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: var(--ink-muted);
		padding: 10px 8px;
		border-bottom: 1px solid var(--paper-200);
	}
	.lab-table th.num,
	.lab-table td.num {
		text-align: right;
	}
	.lab-table th.gaps {
		padding-left: 20px;
	}
	.lab-table tbody tr {
		border-bottom: 1px solid var(--paper-100);
		transition: background 0.14s;
	}
	.lab-table tbody tr:hover {
		background: var(--paper-50);
	}
	.lab-table td {
		padding: 12px 8px;
	}
	.lab-artist {
		display: flex;
		align-items: center;
		gap: 11px;
	}
	.lab-avatar {
		width: 30px;
		height: 30px;
		border-radius: 50%;
		background: var(--sg-50);
		color: var(--sg-700);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 11px;
		font-weight: 700;
		flex: none;
	}
	.lab-artist-name {
		font-weight: 500;
		color: var(--ink-900);
	}
	.lab-ytd {
		color: var(--ink-500);
		font-size: 13px;
	}
	.lab-gap-row {
		display: flex;
		flex-wrap: wrap;
		gap: 5px;
		padding-left: 20px;
	}
	.lab-table td.gaps {
		padding-left: 8px;
	}
	.lab-clear {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		font-size: 12px;
		font-weight: 500;
		color: var(--sg-600);
		padding-left: 20px;
	}
	.lab-clear-dot {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		background: var(--sg-400);
	}
	.lab-uncollected {
		font-weight: 600;
		color: var(--clay-600);
		font-size: 13px;
	}
	.lab-dash {
		color: var(--paper-300);
	}
</style>
