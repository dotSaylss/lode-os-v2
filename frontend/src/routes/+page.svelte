<script lang="ts">
	import FinancialOverview from '$lib/components/FinancialOverview.svelte';
	import ActionItems from '$lib/components/ActionItems.svelte';

	let { data } = $props();

	const ctx = $derived(data.artistContext);
	const fmt = (n: number) =>
		new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n || 0);

	// The orb is the single point of contact with the assistant. The "Recover"
	// action opens it (pre-loaded) rather than scrolling to an inline chat.
	function openOrb(prompt?: string) {
		window.dispatchEvent(new CustomEvent('lode:open', { detail: { prompt } }));
	}
</script>

<div class="v3-stage dash">
	<header class="v3-header">
		<div>
			<span class="v3-date">Overview</span>
			<h1>Good morning, {ctx?.artist_profile?.name ?? 'there'}</h1>
			<p class="v3-vp">For artists — Lode watches every royalty source you're connected to, finds the money you're owed, and files what's missing.</p>
		</div>
		<div class="v3-header-recovered">
			<span>Year to date</span>
			<b>{fmt(ctx?.artist_profile?.ytd_earnings)}</b>
		</div>
	</header>

	<div class="dash-stack">
		<ActionItems
			context={ctx}
			onRecover={() => openOrb('Recover my unclaimed neighboring rights — draft the SoundExchange registration.')}
		/>
		<FinancialOverview context={ctx} />
	</div>
</div>

<style>
	.dash-stack {
		display: flex;
		flex-direction: column;
		gap: 28px;
	}
</style>
