<script lang="ts">
	/**
	 * First-run / demo-opener onboarding. Guided and ambient: Lode introduces
	 * itself, you connect sources, it "reads" them and surfaces its first find,
	 * then hands into the workspace. Pure presentation — no backend wiring.
	 */
	import { onMount } from 'svelte';
	import Icon from '$lib/components/Icon.svelte';

	let { onEnter }: { onEnter?: () => void } = $props();

	type Source = { id: string; name: string; desc: string; mono: string; tone: 'sage' | 'terra' | 'slate' };

	const sources: Source[] = [
		{ id: 'distrokid', name: 'DistroKid', desc: 'Distribution', mono: 'D', tone: 'terra' },
		{ id: 'spotify', name: 'Spotify', desc: 'Streaming & analytics', mono: 'S', tone: 'sage' },
		{ id: 'ascap', name: 'ASCAP', desc: 'Performing rights', mono: 'A', tone: 'slate' },
		{ id: 'soundexchange', name: 'SoundExchange', desc: 'Neighboring rights', mono: 'S', tone: 'sage' }
	];

	let step = $state(0);
	let selected = $state<Record<string, boolean>>(
		Object.fromEntries(sources.map((s) => [s.id, true]))
	);
	let scanning = $state(true);

	const toggle = (id: string) => (selected = { ...selected, [id]: !selected[id] });
	const count = $derived(Object.values(selected).filter(Boolean).length);

	$effect(() => {
		if (step === 2) {
			scanning = true;
			const t = setTimeout(() => (scanning = false), 1900);
			return () => clearTimeout(t);
		}
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
				“Hi, I'm Lode. Point me at where your music lives, and I'll quietly start finding the money
				that's slipped through the cracks.”
			</p>
			<button class="v3-onb-cta" onclick={() => (step = 1)}>
				Get started <Icon name="arrow-right" size={17} color="#fff" />
			</button>
		</div>
	{:else if step === 1}
		<div class="v3-onb-stage wide">
			<span class="v3-onb-eyebrow">Step 1 · Connect</span>
			<h2 class="v3-onb-h">Where does your music live?</h2>
			<p class="v3-onb-sub">
				Connect a source or two to start. You can add the rest anytime — the more I can see, the more
				I can recover.
			</p>
			<div class="v3-onb-grid">
				{#each sources as s (s.id)}
					<button class="v3-onb-source {selected[s.id] ? 'on' : ''}" onclick={() => toggle(s.id)}>
						<span class="onb-tile tile-{s.tone}">{s.mono}</span>
						<div class="v3-onb-source-meta"><b>{s.name}</b><span>{s.desc}</span></div>
						<span class="v3-onb-source-check">
							{#if selected[s.id]}
								<Icon name="check" size={16} color="#fff" />
							{:else}
								<Icon name="plus" size={16} color="var(--ink-500)" />
							{/if}
						</span>
					</button>
				{/each}
			</div>
			<button class="v3-onb-cta" disabled={count === 0} onclick={() => (step = 2)}>
				Connect {count > 0 ? count : ''} {count === 1 ? 'source' : 'sources'}
				<Icon name="arrow-right" size={17} color="#fff" />
			</button>
		</div>
	{:else}
		<div class="v3-onb-stage">
			{#if scanning}
				<div class="v3-onb-scan"><img src="/logo-mark.svg" alt="" width="44" height="44" /></div>
				<p class="v3-onb-line sm">Reading your catalog<span class="v3-onb-ell">…</span></p>
				<span class="v3-onb-scan-note"
					>Matching ISRCs · reconciling statements · checking registrations</span
				>
			{:else}
				<div class="v3-onb-found"><Icon name="sparkles" size={26} color="var(--sg-600)" /></div>
				<p class="v3-onb-line">
					“Already found <em>$2,400</em> in unclaimed neighboring rights — and a few more things
					worth your time. I've teed up the most valuable one.”
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
</style>
