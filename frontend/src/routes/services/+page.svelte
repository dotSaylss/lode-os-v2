<script lang="ts">
	import { tick } from 'svelte';
	import { slide } from 'svelte/transition';
	import MatchmakerChat from '$lib/components/MatchmakerChat.svelte';
	import Icon from '$lib/components/Icon.svelte';
	import { pendingAsk, clearPending } from '$lib/lodeStore';

	let { data } = $props();

	type Provider = {
		id: string;
		name: string;
		category: string;
		specialty: string;
		genres: string[];
		rating: number;
		reviews: number;
		turnaround: string;
		rate: string;
		location: string;
		verified: boolean;
		bio: string;
	};

	const providers: Provider[] = $derived(data.providers ?? []);

	let chat = $state<MatchmakerChat | null>(null);
	let brief = $state('');
	let activeCategory = $state<string>('all');

	// The matchmaker panel (with its grounding-evidence panel) stays hidden until
	// a brief is submitted or the orb hands off — then it reveals full-width in
	// place, where the cited providers + web sources render at full size.
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
		if (pending && pending.page === '/services') {
			clearPending();
			revealPanel().then(() => chat?.send(pending.prompt));
		}
	});

	const CATEGORY_LABELS: Record<string, string> = {
		mixing: 'Mixing',
		mastering: 'Mastering',
		cover_art: 'Cover Art',
		vocal_production: 'Vocal Production',
		sync_licensing: 'Sync Licensing',
		music_video: 'Music Video',
		promotion: 'Promotion',
		session_musician: 'Session Players'
	};

	// Muted, on-brand tones per category (sage / terra / slate / amber — never loud).
	const CATEGORY_TONE: Record<string, string> = {
		mixing: 'tone-slate',
		mastering: 'tone-sage',
		cover_art: 'tone-terra',
		vocal_production: 'tone-sage',
		sync_licensing: 'tone-slate',
		music_video: 'tone-amber',
		promotion: 'tone-terra',
		session_musician: 'tone-sage'
	};

	const AVATAR_TONE: Record<string, string> = {
		mixing: 'av-slate',
		mastering: 'av-sage',
		cover_art: 'av-terra',
		vocal_production: 'av-sage',
		sync_licensing: 'av-slate',
		music_video: 'av-terra',
		promotion: 'av-terra',
		session_musician: 'av-sage'
	};

	const label = (cat: string) => CATEGORY_LABELS[cat] ?? cat;
	const tone = (cat: string) => CATEGORY_TONE[cat] ?? 'tone-neutral';
	const avTone = (cat: string) => AVATAR_TONE[cat] ?? 'av-slate';
	const initials = (name: string) =>
		name
			.split(' ')
			.map((p) => p[0])
			.join('')
			.slice(0, 2)
			.toUpperCase();

	const categories = $derived(['all', ...Array.from(new Set(providers.map((p) => p.category)))]);

	const visibleProviders = $derived(
		activeCategory === 'all' ? providers : providers.filter((p) => p.category === activeCategory)
	);

	async function runBrief() {
		const text = brief.trim();
		if (!text) return;
		await revealPanel();
		chat?.send(text);
		brief = '';
	}

	const examples = [
		'I need my track mixed, mastered, and cover art for a lo-fi hip-hop single.',
		'Assemble a team for a pop single: vocals, mix, master, and a music video.',
		'Find me a mastering engineer, and check the live web for current going rates in 2026.'
	];
</script>

<div class="v3-stage-wide">
	<header class="v3-header">
		<div>
			<span class="v3-date">Services</span>
			<h1>Bring your song to life</h1>
		</div>
		<div class="v3-header-recovered">
			<span>Vetted marketplace</span>
			<b>{providers.length} providers</b>
		</div>
	</header>

	<div class="svc-stack">
		<!-- Brief composer -->
		<section class="svc-card svc-brief">
			<span class="eyebrow">Describe your song's needs</span>
			<form
				onsubmit={(e) => {
					e.preventDefault();
					runBrief();
				}}
			>
				<textarea
					bind:value={brief}
					rows="3"
					placeholder="e.g. I need my track mixed, mastered, and cover art for a lo-fi hip-hop single."
				></textarea>
				<div class="svc-brief-foot">
					<div class="svc-examples">
						{#each examples as ex}
							<button type="button" class="v3-orb-chip" onclick={() => (brief = ex)}>
								{ex.length > 40 ? ex.slice(0, 40) + '…' : ex}
							</button>
						{/each}
					</div>
					<button type="submit" class="v3-act" disabled={!brief.trim()}>
						Find my team <Icon name="arrow-right" size={16} color="#fff" />
					</button>
				</div>
			</form>
		</section>

		<!-- Revealable matchmaker panel: holds the grounding evidence when invoked -->
		{#if panelOpen}
			<div class="svc-panel" bind:this={panelEl} transition:slide={{ duration: 280 }}>
				<MatchmakerChat bind:this={chat} />
			</div>
		{/if}

		<!-- Marketplace -->
		<section class="svc-card">
				<div class="svc-card-head">
					<span class="eyebrow">Vetted marketplace</span>
					<span class="svc-pill">{providers.length} providers</span>
				</div>

				<div class="svc-filters">
					{#each categories as cat}
						<button
							class="svc-filter {activeCategory === cat ? 'active' : ''}"
							onclick={() => (activeCategory = cat)}
						>
							{cat === 'all' ? 'All' : label(cat)}
						</button>
					{/each}
				</div>

				{#if visibleProviders.length === 0}
					<div class="svc-empty">No providers loaded. Is the backend running?</div>
				{:else}
					<div class="svc-providers">
						{#each visibleProviders as p (p.id)}
							<div class="svc-prov">
								<div class="svc-prov-top">
									<span class="svc-avatar {avTone(p.category)}">{initials(p.name)}</span>
									<div class="svc-prov-id">
										<div class="svc-prov-name-row">
											<span class="svc-prov-name">{p.name}</span>
											{#if p.verified}
												<Icon name="badge-check" size={15} color="var(--sg-500)" />
											{/if}
										</div>
										<span class="svc-tag {tone(p.category)}">{label(p.category)}</span>
									</div>
									<div class="svc-rating">
										<span class="svc-rating-val"><Icon name="star" size={13} color="var(--amber-500)" /> {p.rating}</span>
										<span class="svc-reviews">{p.reviews} reviews</span>
									</div>
								</div>

								<p class="svc-specialty">{p.specialty}</p>

								<div class="svc-genres">
									{#each p.genres.slice(0, 3) as g}
										<span class="svc-genre">{g}</span>
									{/each}
								</div>

								<div class="svc-prov-foot">
									<span class="mono svc-rate">{p.rate}</span>
									<span class="svc-turnaround">{p.turnaround}</span>
								</div>
							</div>
						{/each}
					</div>
				{/if}
			</section>
	</div>
</div>

<style>
	.svc-stack {
		display: flex;
		flex-direction: column;
		gap: 22px;
	}
	.svc-panel {
		height: 600px;
	}
	.svc-card {
		background: var(--paper-0);
		border: 1px solid var(--paper-200);
		border-radius: var(--r-2xl);
		box-shadow: var(--v3-sh-sm);
		padding: 26px 28px;
	}
	.svc-brief textarea {
		width: 100%;
		margin-top: 12px;
		background: var(--paper-50);
		border: 1px solid var(--paper-200);
		border-radius: var(--r-lg);
		padding: 14px 16px;
		font-family: var(--font-sans);
		font-size: 15px;
		line-height: 1.5;
		color: var(--ink-900);
		resize: none;
		outline: none;
		transition: border-color 0.15s;
	}
	.svc-brief textarea:focus {
		border-color: var(--sg-300);
	}
	.svc-brief textarea::placeholder {
		color: var(--ink-muted);
	}
	.svc-brief-foot {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 16px;
		margin-top: 14px;
		flex-wrap: wrap;
	}
	.svc-examples {
		display: flex;
		flex-wrap: wrap;
		gap: 7px;
		flex: 1;
	}
	.svc-card-head {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 16px;
	}
	.svc-pill {
		font-size: 11px;
		font-weight: 500;
		color: var(--ink-500);
		background: var(--paper-100);
		border-radius: var(--r-pill);
		padding: 5px 12px;
	}
	.svc-filters {
		display: flex;
		flex-wrap: wrap;
		gap: 7px;
		margin-bottom: 18px;
	}
	.svc-filter {
		font-size: 12px;
		font-weight: 600;
		padding: 6px 13px;
		border-radius: var(--r-pill);
		border: 1px solid var(--paper-200);
		background: var(--paper-0);
		color: var(--ink-500);
		transition: all 0.14s;
	}
	.svc-filter:hover {
		border-color: var(--sg-200);
		color: var(--ink-900);
	}
	.svc-filter.active {
		background: var(--sg-500);
		border-color: var(--sg-500);
		color: #fff;
	}
	.svc-empty {
		padding: 24px;
		text-align: center;
		border: 1px dashed var(--paper-300);
		border-radius: var(--r-lg);
		font-size: 14px;
		color: var(--ink-muted);
	}
	.svc-providers {
		display: grid;
		grid-template-columns: 1fr;
		gap: 14px;
	}
	@media (min-width: 640px) {
		.svc-providers {
			grid-template-columns: 1fr 1fr;
		}
	}
	@media (min-width: 1024px) {
		.svc-providers {
			grid-template-columns: 1fr 1fr 1fr;
		}
	}
	.svc-prov {
		display: flex;
		flex-direction: column;
		padding: 18px;
		background: var(--paper-50);
		border: 1px solid var(--paper-200);
		border-radius: var(--r-lg);
		transition: box-shadow 0.15s, border-color 0.15s;
	}
	.svc-prov:hover {
		box-shadow: var(--v3-sh-sm);
		border-color: var(--paper-300);
	}
	.svc-prov-top {
		display: flex;
		align-items: flex-start;
		gap: 12px;
	}
	.svc-avatar {
		flex: none;
		width: 42px;
		height: 42px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 13px;
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
	.svc-prov-id {
		min-width: 0;
		flex: 1;
	}
	.svc-prov-name-row {
		display: flex;
		align-items: center;
		gap: 6px;
	}
	.svc-prov-name {
		font-size: 15px;
		font-weight: 600;
		color: var(--ink-900);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.svc-tag {
		display: inline-block;
		margin-top: 5px;
		font-size: 10.5px;
		font-weight: 500;
		padding: 2px 9px;
		border-radius: var(--r-pill);
	}
	.tone-sage {
		background: var(--sg-50);
		color: var(--sg-700);
	}
	.tone-terra {
		background: var(--terra-50);
		color: var(--terra-600);
	}
	.tone-slate {
		background: var(--slate-50);
		color: var(--slate-600);
	}
	.tone-amber {
		background: var(--amber-50);
		color: var(--amber-600);
	}
	.tone-neutral {
		background: var(--paper-100);
		color: var(--ink-500);
	}
	.svc-rating {
		text-align: right;
		flex: none;
	}
	.svc-rating-val {
		display: inline-flex;
		align-items: center;
		gap: 3px;
		font-size: 13px;
		font-weight: 600;
		color: var(--ink-900);
		font-family: var(--font-mono);
	}
	.svc-reviews {
		display: block;
		font-size: 10.5px;
		color: var(--ink-muted);
		margin-top: 2px;
	}
	.svc-specialty {
		margin: 13px 0 0;
		font-size: 13px;
		line-height: 1.5;
		color: var(--ink-700);
	}
	.svc-genres {
		display: flex;
		flex-wrap: wrap;
		gap: 5px;
		margin-top: 12px;
	}
	.svc-genre {
		font-size: 10.5px;
		font-weight: 500;
		color: var(--ink-500);
		background: var(--paper-100);
		padding: 2px 8px;
		border-radius: var(--r-xs);
	}
	.svc-prov-foot {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-top: 14px;
		padding-top: 12px;
		border-top: 1px solid var(--paper-200);
	}
	.svc-rate {
		font-size: 13px;
		color: var(--ink-900);
	}
	.svc-turnaround {
		font-size: 12px;
		color: var(--ink-muted);
	}
</style>
