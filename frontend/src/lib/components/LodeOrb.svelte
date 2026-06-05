<script lang="ts">
	/**
	 * The omniscient "Lode" orb — a workspace-wide concierge.
	 * Posts to /api/v1/ask, where a ConciergeAgent consults the right domain
	 * specialist and returns an answer + a route_hint. The orb renders the answer
	 * and, when a hint is present, nudges the user to the page where the full
	 * detail (A2A trace, grounding evidence) renders at full width.
	 */
	import { tick } from 'svelte';
	import { fade } from 'svelte/transition';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import Icon from '$lib/components/Icon.svelte';

	type RouteHint = { page: string; label: string; reason?: string };
	type Msg = { id: number; role: 'user' | 'lode'; text: string; hint?: RouteHint };

	let pinned = $state(false);
	let input = $state('');
	let isTyping = $state(false);
	let sessionId = $state<string | null>(null);
	let thread: HTMLDivElement | undefined = $state();

	let messages = $state<Msg[]>([
		{
			id: 1,
			role: 'lode',
			text: "I'm watching your royalties, catalog, and the services around your music. Ask me anything — I'll look into it and take you to the right place."
		}
	]);

	const chips = ['Where am I losing money?', "What's my biggest catalog opportunity?", 'Who can master my track?'];

	async function scrollDown() {
		await tick();
		if (thread) thread.scrollTop = thread.scrollHeight;
	}

	async function send(text: string) {
		const q = text.trim();
		if (!q || isTyping) return;
		messages = [...messages, { id: Date.now(), role: 'user', text: q }];
		input = '';
		isTyping = true;
		scrollDown();

		try {
			const res = await fetch(api('/api/v1/ask'), {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ message: q, session_id: sessionId })
			});
			if (!res.ok) throw new Error('bad response');
			const data = await res.json();
			sessionId = data.session_id ?? sessionId;
			messages = [
				...messages,
				{ id: Date.now() + 1, role: 'lode', text: data.response, hint: data.route_hint ?? undefined }
			];
		} catch {
			messages = [
				...messages,
				{
					id: Date.now() + 1,
					role: 'lode',
					text: "I'm having trouble reaching the workspace right now. Make sure the API server is running."
				}
			];
		} finally {
			isTyping = false;
			scrollDown();
		}
	}

	function follow(hint: RouteHint) {
		pinned = false;
		goto(hint.page);
	}
</script>

<div class="v3-orb-wrap" class:pinned>
	<div class="v3-orb-panel">
		<div class="v3-orb-head">
			<img src="/logo-mark.svg" alt="" width="26" height="26" />
			<div class="v3-orb-meta">
				<b>Lode</b>
				<span><span class="v3-orb-live"></span> Listening across your workspace</span>
			</div>
			<button
				class="v3-ico-btn sm"
				type="button"
				title={pinned ? 'Unpin' : 'Keep open'}
				onclick={() => (pinned = !pinned)}
			>
				<Icon name={pinned ? 'pin-off' : 'pin'} size={15} color="var(--ink-500)" />
			</button>
		</div>

		<div class="v3-orb-thread" bind:this={thread}>
			{#each messages as m (m.id)}
				<div class="v3-orb-bubble {m.role === 'user' ? 'user' : 'lode'}">
					<p>{m.text}</p>
				</div>
				{#if m.role === 'lode' && m.hint}
					<button class="v3-orb-route" type="button" onclick={() => follow(m.hint!)}>
						See this in {m.hint.label}
						<Icon name="arrow-right" size={14} color="var(--sg-700)" />
					</button>
				{/if}
			{/each}
			{#if isTyping}
				<div in:fade class="v3-orb-bubble lode">
					<div class="typing"><span></span><span></span><span></span></div>
				</div>
			{/if}
		</div>

		<div class="v3-orb-chips">
			{#each chips as c}
				<button class="v3-orb-chip" type="button" onclick={() => send(c)}>{c}</button>
			{/each}
		</div>

		<form
			class="v3-orb-composer"
			onsubmit={(e) => {
				e.preventDefault();
				send(input);
			}}
		>
			<input bind:value={input} placeholder="Ask Lode anything…" />
			<button class="v3-orb-send" type="submit" disabled={!input.trim() || isTyping} aria-label="Send">
				<Icon name="arrow-up" size={16} color="#fff" />
			</button>
		</form>
	</div>

	<button class="v3-orb" type="button" aria-label="Open Lode">
		<img src="/logo-mark.svg" alt="" width="30" height="30" />
		<span class="v3-orb-hint">Lode is listening</span>
	</button>
</div>
