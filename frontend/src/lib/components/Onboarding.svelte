<script lang="ts">
	/**
	 * First-run / demo-opener onboarding. Guided and ambient: Lode introduces
	 * itself, you connect the workspace's real sources, it reads them and
	 * surfaces its first find, then hands into the workspace.
	 *
	 * Real wiring: step 1 lists the persona's actual connector catalog
	 * (GET /api/v1/connectors); newly selected platforms are connected through
	 * the same endpoint the connect wizard uses; the final slide's findings come
	 * from a live backend scan over the same data the agents read, with a
	 * deterministic fallback so the first impression never stalls.
	 */
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import Icon from '$lib/components/Icon.svelte';

	let {
		onEnter,
		persona = 'june',
		personaName = ''
	}: { onEnter?: () => void; persona?: string; personaName?: string } = $props();

	// The label workspace is a company name; people get their first name.
	const firstName = $derived(
		persona === 'label' ? personaName : (personaName.split(' ')[0] ?? '')
	);

	type Source = {
		id: string;
		name: string;
		category: string;
		status: 'connected' | 'available';
		tone: string;
	};

	const CATEGORY_LABELS: Record<string, string> = {
		creation: 'Creation',
		collaboration: 'Library & collab',
		royalties: 'Royalties',
		sync_licensing: 'Sync licensing',
		distribution: 'Distribution',
		rights_org: 'Rights org'
	};
	const categoryLabel = (c: string) => CATEGORY_LABELS[c] ?? c;

	// Offline fallback: if the API is unreachable, the flow still reads well.
	const FALLBACK_SOURCES: Source[] = [
		{ id: 'distrokid', name: 'DistroKid', category: 'distribution', status: 'available', tone: 'terra' },
		{ id: 'spotify_artists', name: 'Spotify for Artists', category: 'royalties', status: 'available', tone: 'sage' },
		{ id: 'ascap', name: 'ASCAP', category: 'rights_org', status: 'available', tone: 'slate' },
		{ id: 'soundexchange', name: 'SoundExchange', category: 'rights_org', status: 'available', tone: 'sage' }
	];

	let step = $state(0);
	let sources = $state<Source[]>([]);
	let sourcesLive = $state(false); // true once the real catalog loaded
	let selected = $state<Record<string, boolean>>({});
	let scanning = $state(true);
	let findings = $state('');
	let headline = $state('');

	const FALLBACK_FINDINGS: Record<string, { message: string; headline: string }> = {
		june: {
			message:
				'With your sources connected I can already see $2,400 in unclaimed neighboring rights waiting at SoundExchange. The most valuable next step is teed up for you.',
			headline: '$2,400'
		},
		kai: {
			message:
				'Your library and your licensing are talking to each other now. I found sync-ready tracks that fit live briefs on Disco, and $310 in digital royalties you have not claimed yet.',
			headline: '$310'
		},
		label: {
			message:
				'Across your 50-artist roster I can already see six figures in uncollected royalties, with the biggest bulk registration ready to go. The recovery queue is ordered by value.',
			headline: 'six figures'
		}
	};

	onMount(() => {
		const ctrl = new AbortController();
		const giveUp = setTimeout(() => ctrl.abort(), 2500);
		fetch(api('/api/v1/connectors'), { signal: ctrl.signal })
			.then((r) => (r.ok ? r.json() : Promise.reject()))
			.then((list: Source[]) => {
				sources = list;
				sourcesLive = true;
				selected = Object.fromEntries(
					list.filter((s) => s.status === 'available').map((s) => [s.id, false])
				);
			})
			.catch(() => {
				sources = FALLBACK_SOURCES;
				selected = Object.fromEntries(FALLBACK_SOURCES.map((s) => [s.id, true]));
			})
			.finally(() => clearTimeout(giveUp));
		return () => ctrl.abort();
	});

	const toggle = (s: Source) => {
		if (s.status === 'connected') return;
		selected = { ...selected, [s.id]: !selected[s.id] };
	};

	const connectedCount = $derived(sources.filter((s) => s.status === 'connected').length);
	const newIds = $derived(
		sources.filter((s) => s.status === 'available' && selected[s.id]).map((s) => s.id)
	);
	const isOn = (s: Source) => s.status === 'connected' || !!selected[s.id];

	function beginScan() {
		// Persist the new connections through the same endpoint the connect
		// wizard uses; the scan animation covers the round trips. Connected
		// platforms are never re-posted (that would reseed their permissions).
		if (sourcesLive && newIds.length) {
			const account = personaName || 'Lode';
			void Promise.allSettled(
				newIds.map((id) =>
					fetch(api(`/api/v1/connectors/${id}/connect`), {
						method: 'POST',
						headers: { 'Content-Type': 'application/json' },
						body: JSON.stringify({ account })
					})
				)
			);
		}
		step = 2;
	}

	$effect(() => {
		if (step !== 2) return;
		scanning = true;
		const ids = [...sources.filter((s) => s.status === 'connected').map((s) => s.id), ...newIds];
		const pacing = new Promise((r) => setTimeout(r, 1900));
		const timeout = new Promise<null>((r) => setTimeout(() => r(null), 4000));
		const scan = fetch(api('/api/v1/onboarding/scan'), {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ connector_ids: ids })
		})
			.then((r) => (r.ok ? r.json() : null))
			.catch(() => null);
		let cancelled = false;
		Promise.all([Promise.race([scan, timeout]), pacing]).then(([res]) => {
			if (cancelled) return;
			const fb = FALLBACK_FINDINGS[persona] ?? FALLBACK_FINDINGS.june;
			findings = res?.message ?? fb.message;
			headline = res?.headline ?? fb.headline;
			scanning = false;
		});
		return () => {
			cancelled = true;
		};
	});

	// Split the findings around the headline figure so it can be emphasized
	// without rendering raw HTML.
	const findingsParts = $derived.by(() => {
		if (!headline || !findings.includes(headline)) return null;
		const i = findings.indexOf(headline);
		return {
			before: findings.slice(0, i),
			em: headline,
			after: findings.slice(i + headline.length)
		};
	});

	function enter() {
		onEnter?.();
	}
</script>

<div class="v3-onb">
	<div class="v3-onb-dots">
		{#each [0, 1, 2] as i}
			<span class="v3-onb-dot {i === step ? 'active' : ''} {i < step ? 'done' : ''}"></span>
		{/each}
	</div>

	{#if step === 0}
		<div class="v3-onb-stage">
			<img class="v3-onb-mark" src="/logo-mark.svg" alt="" width="56" height="56" />
			<span class="v3-onb-eyebrow">LodeOS</span>
			<p class="v3-onb-line">
				Hi{firstName ? `, ${firstName}` : ''}. I'm Lode, the reasoning layer between the points you
				care about: where your work is made, where it earns, and where it goes next. Point me at
				them and I'll connect the dots.
			</p>
			<button class="v3-onb-cta" onclick={() => (step = 1)}>
				Get started <Icon name="arrow-right" size={17} color="#fff" />
			</button>
		</div>
	{:else if step === 1}
		<div class="v3-onb-stage wide">
			<span class="v3-onb-eyebrow">Step 1 · Connect</span>
			<h2 class="v3-onb-h">Where does your work live?</h2>
			<p class="v3-onb-sub">
				{#if connectedCount > 0}
					Your connected platforms are already in. Add more anytime; the more I can see, the more I
					can do across them.
				{:else}
					Connect a source or two to start. You can add the rest anytime; the more I can see, the
					more I can do across them.
				{/if}
			</p>
			<div class="v3-onb-grid">
				{#each sources as s (s.id)}
					<button
						class="v3-onb-source {isOn(s) ? 'on' : ''}"
						disabled={s.status === 'connected'}
						onclick={() => toggle(s)}
					>
						<span class="onb-tile tile-{s.tone}">{s.name.slice(0, 1)}</span>
						<div class="v3-onb-source-meta">
							<b>{s.name}</b>
							<span>{s.status === 'connected' ? 'Connected' : categoryLabel(s.category)}</span>
						</div>
						<span class="v3-onb-source-check">
							{#if isOn(s)}
								<Icon name="check" size={16} color="#fff" />
							{:else}
								<Icon name="plus" size={16} color="var(--ink-500)" />
							{/if}
						</span>
					</button>
				{/each}
			</div>
			<button class="v3-onb-cta" onclick={beginScan}>
				{newIds.length > 0
					? `Connect ${newIds.length} ${newIds.length === 1 ? 'source' : 'sources'}`
					: 'Continue'}
				<Icon name="arrow-right" size={17} color="#fff" />
			</button>
		</div>
	{:else}
		<div class="v3-onb-stage">
			{#if scanning}
				<div class="v3-onb-scan"><img src="/logo-mark.svg" alt="" width="44" height="44" /></div>
				<p class="v3-onb-line sm">Reading your sources<span class="v3-onb-ell">…</span></p>
				<span class="v3-onb-scan-note"
					>Reading sources · matching catalog · checking registrations</span
				>
			{:else}
				<div class="v3-onb-found"><Icon name="coins" size={26} color="var(--sg-600)" /></div>
				<p class="v3-onb-line">
					{#if findingsParts}
						{findingsParts.before}<em>{findingsParts.em}</em>{findingsParts.after}
					{:else}
						{findings}
					{/if}
				</p>
				<button class="v3-onb-cta" onclick={enter}>
					Enter workspace <Icon name="arrow-right" size={17} color="#fff" />
				</button>
			{/if}
		</div>
	{/if}

	{#if step > 0}
		<button class="v3-onb-back" onclick={() => (step = step - 1)}>
			<Icon name="arrow-left" size={16} color="var(--ink-500)" /> Back
		</button>
	{/if}
</div>

<style>
	.onb-tile {
		width: 38px;
		height: 38px;
		border-radius: 11px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: 700;
		font-size: 17px;
		flex: none;
	}
	.tile-sage {
		background: var(--sg-100);
		color: var(--sg-700);
	}
	.tile-terra {
		background: var(--terra-100);
		color: var(--terra-600);
	}
	.tile-slate {
		background: var(--slate-100);
		color: var(--slate-600);
	}
	.tile-amber {
		background: var(--amber-50);
		color: var(--amber-600);
	}
	.v3-onb-source:disabled {
		cursor: default;
	}
</style>
