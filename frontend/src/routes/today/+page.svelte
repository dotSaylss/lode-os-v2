<script lang="ts">
	import FinancialOverview from '$lib/components/FinancialOverview.svelte';
	import ActionItems from '$lib/components/ActionItems.svelte';
	import LibraryCard from '$lib/components/LibraryCard.svelte';

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
			<p class="v3-vp">Lode reasons across everything you've connected, surfaces what deserves your attention, and files what's missing when you say go.</p>
		</div>
		<div class="v3-header-recovered">
			<span>Year to date</span>
			<b>{fmt(ctx?.artist_profile?.ytd_earnings)}</b>
		</div>
	</header>

	<div class="dash-stack">
		<ActionItems
			context={ctx}
			onRecover={() => openOrb('Recover my unclaimed neighboring rights. Draft the SoundExchange registration.')}
		/>
		<LibraryCard
			context={ctx}
			onPitch={(track: { title: string; playlist: string }) =>
				openOrb(
					`Use "${track.title}" from my Untitled "${track.playlist}" playlist and draft a Disco pitch for the best-matching brief.`
				)}
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
