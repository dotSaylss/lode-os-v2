<script lang="ts">
	/**
	 * Floating "Lode" orb — the ambient workspace presence.
	 * Phase A: launcher (pulsing orb + hint). Phase B upgrades the panel into
	 * the omniscient concierge (posts to /api/v1/ask, renders route-hints).
	 */
	import Icon from '$lib/components/Icon.svelte';

	let pinned = $state(false);
</script>

<div class="v3-orb-wrap" class:pinned>
	<div class="v3-orb-panel">
		<div class="v3-orb-head">
			<img src="/logo-mark.svg" alt="" width="26" height="26" />
			<div class="v3-orb-meta">
				<b>Lode</b>
				<span><span class="v3-orb-live"></span> Listening across your workspace</span>
			</div>
			<button class="v3-ico-btn sm" type="button" title={pinned ? 'Unpin' : 'Keep open'} onclick={() => (pinned = !pinned)}>
				<Icon name={pinned ? 'pin-off' : 'pin'} size={15} color="var(--ink-500)" />
			</button>
		</div>

		<div class="v3-orb-thread">
			<div class="v3-orb-bubble lode">
				<p>I'm watching your royalties, catalog, and the services around your music. Ask me anything &mdash; I'll take you to the right place.</p>
			</div>
		</div>

		<div class="v3-orb-composer">
			<input placeholder="Ask Lode…" disabled />
			<button class="v3-orb-send" type="button" disabled>
				<Icon name="arrow-up" size={16} color="#fff" />
			</button>
		</div>
	</div>

	<button class="v3-orb" type="button" aria-label="Open Lode">
		<img src="/logo-mark.svg" alt="" width="30" height="30" />
		<span class="v3-orb-hint">Lode is listening</span>
	</button>
</div>
