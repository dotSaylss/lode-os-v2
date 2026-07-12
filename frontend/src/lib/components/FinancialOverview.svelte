<script lang="ts">
	let { context } = $props();

	const formatCurrency = (amount: number) =>
		new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);
</script>

<div class="fin-card">
	<div class="fin-head">
		<span class="eyebrow">Year to date earnings</span>
		<span class="fin-artist">{context?.artist_profile?.name || 'Artist'}</span>
	</div>

	<p class="figure-lg fin-amount">{formatCurrency(context?.artist_profile?.ytd_earnings || 0)}</p>

	<div class="fin-sources">
		<span class="eyebrow fin-sources-label">Connected revenue sources</span>
		<div class="fin-source-row">
			{#each context?.connected_sources || [] as source}
				<span class="v3-track">
					<span
						class="fin-dot {source.status === 'connected' || source.status === 'active'
							? 'on'
							: 'off'}"
					></span>
					{source.name}
				</span>
			{/each}
		</div>
	</div>
</div>

<style>
	.fin-card {
		background: var(--paper-0);
		border: 1px solid var(--paper-200);
		border-radius: var(--r-2xl);
		box-shadow: var(--v3-sh-md);
		padding: 30px 32px;
		display: flex;
		flex-direction: column;
		height: 100%;
	}
	.fin-head {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 14px;
	}
	.fin-artist {
		font-size: 12px;
		font-weight: 500;
		color: var(--ink-500);
		background: var(--paper-100);
		border-radius: var(--r-pill);
		padding: 5px 13px;
	}
	.fin-amount {
		font-size: 52px;
		letter-spacing: -0.03em;
		color: var(--ink-900);
		margin: 0 0 28px;
	}
	.fin-sources {
		margin-top: auto;
	}
	.fin-sources-label {
		display: block;
		margin-bottom: 12px;
	}
	.fin-source-row {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
	}
	.fin-dot {
		width: 7px;
		height: 7px;
		border-radius: 50%;
	}
	.fin-dot.on {
		background: var(--sg-500);
	}
	.fin-dot.off {
		background: var(--amber-500);
	}
	/* Mobile: the large mono figure can be wider than the card; scale it down
	   and stack the head so the artist pill never collides with the eyebrow. */
	@media (max-width: 640px) {
		.fin-card {
			padding: 22px 18px;
		}
		.fin-head {
			flex-direction: column;
			align-items: flex-start;
			gap: 8px;
		}
		.fin-amount {
			font-size: clamp(30px, 11vw, 52px);
			overflow-wrap: anywhere;
		}
	}
</style>
