<script lang="ts">
	import FinancialOverview from '$lib/components/FinancialOverview.svelte';
	import ActionItems from '$lib/components/ActionItems.svelte';
	import AgentChat from '$lib/components/AgentChat.svelte';

	let { data } = $props();

	const ctx = $derived(data.artistContext);
	const fmt = (n: number) =>
		new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n || 0);

	let chatColumn: HTMLDivElement | undefined = $state();

	function focusChat() {
		chatColumn?.scrollIntoView({ behavior: 'smooth', block: 'start' });
		chatColumn?.querySelector('input')?.focus();
	}
</script>

<div class="v3-stage-wide dash">
	<header class="v3-header">
		<div>
			<span class="v3-date">Overview</span>
			<h1>Good morning, {ctx?.artist_profile?.name ?? 'there'}</h1>
		</div>
		<div class="v3-header-recovered">
			<span>Year to date</span>
			<b>{fmt(ctx?.artist_profile?.ytd_earnings)}</b>
		</div>
	</header>

	<div class="dash-grid">
		<div class="dash-main">
			<ActionItems context={ctx} onRecover={focusChat} />
			<FinancialOverview context={ctx} />
		</div>

		<div class="dash-chat" bind:this={chatColumn}>
			<AgentChat />
		</div>
	</div>
</div>

<style>
	.dash {
		max-width: 1180px;
	}
	.dash-grid {
		display: grid;
		grid-template-columns: 1fr;
		gap: 24px;
	}
	@media (min-width: 1024px) {
		.dash-grid {
			grid-template-columns: 1.5fr 1fr;
			align-items: stretch;
			min-height: 560px;
		}
	}
	.dash-main {
		display: flex;
		flex-direction: column;
		gap: 24px;
	}
	.dash-chat {
		min-height: 520px;
		display: flex;
	}
	.dash-chat :global(.chat-card) {
		flex: 1;
	}
</style>
