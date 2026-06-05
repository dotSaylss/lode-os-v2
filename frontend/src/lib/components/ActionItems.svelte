<script lang="ts">
	import Icon from '$lib/components/Icon.svelte';

	let { context, onRecover }: { context: any; onRecover?: () => void } = $props();

	let missingAmount = $derived(context?.neighboring_rights?.estimated_missing || 0);
	let isRegistered = $derived(context?.neighboring_rights?.registered ?? true);

	const fmt = (n: number) =>
		new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n);
</script>

{#if !isRegistered}
	<section class="v3-focus">
		<div class="v3-focus-head">
			<span class="v3-focus-eyebrow"><span class="v3-focus-dot"></span> Recommended next</span>
			<span class="v3-focus-progress">Neighboring rights · SoundExchange</span>
		</div>

		<p class="v3-focus-line">
			I found <em>{fmt(missingAmount)}</em> in unclaimed neighboring rights on your catalog. I've
			drafted the SoundExchange registration — want me to file it?
		</p>

		<div class="v3-focus-foot">
			<div class="v3-focus-amount">
				<b>{fmt(missingAmount)}</b>
				<span>recoverable</span>
			</div>
			<div class="v3-focus-actions">
				<button class="v3-act" type="button" onclick={() => onRecover?.()}>
					<Icon name="check" size={17} color="#fff" /> Recover
				</button>
			</div>
		</div>
	</section>
{:else}
	<section class="v3-focus done">
		<div class="v3-focus-checkmark"><Icon name="check" size={26} color="var(--sg-600)" /></div>
		<p class="v3-focus-empty">
			Nothing needs you right now.<br /><span>I'll keep listening — you'll know the moment
				something moves.</span>
		</p>
	</section>
{/if}
