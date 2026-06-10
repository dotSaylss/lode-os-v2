<script lang="ts">
	/**
	 * The omniscient "Lode" orb — the single point of contact with the assistant.
	 * Posts to /api/v1/ask, where a ConciergeAgent consults the right domain
	 * specialist and returns an answer + a route_hint. The orb renders the answer
	 * and, when a hint is present, nudges the user to the page where the full
	 * detail (A2A trace, grounding evidence) renders at full width — handing off
	 * the prompt so that page replays it and reveals its panel in place.
	 */
	import { tick, onMount } from 'svelte';
	import { fade, scale } from 'svelte/transition';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { handoffTo } from '$lib/lodeStore';
	import Icon from '$lib/components/Icon.svelte';

	type RouteHint = { page: string; label: string; reason?: string };
	type Msg = { id: number; role: 'user' | 'lode'; text: string; hint?: RouteHint };

	let open = $state(false);
	let pinned = $state(false);
	let input = $state('');
	let isTyping = $state(false);
	let sessionId = $state<string | null>(null);
	let thread: HTMLDivElement | undefined = $state();
	let inputEl: HTMLInputElement | undefined = $state();

	let messages = $state<Msg[]>([
		{
			id: 1,
			role: 'lode',
			text: "I'm watching your royalties, catalog, and the services around your music. Ask me anything — I'll look into it and take you to the right place."
		}
	]);

	// The "Lode is listening" hint shows briefly on load, then gets out of the way.
	let hintArmed = $state(true);

	// Starter prompts rotate through the composer's placeholder; Tab accepts one.
	const suggestions = [
		'Where am I losing money?',
		"What's my biggest catalog opportunity?",
		"Pitch my catalog into this week's sync briefs",
		'Who can master my track?'
	];
	let suggestionIdx = $state(0);

	// Next-step actions offered under an answer, keyed by the destination the
	// concierge routed to — so the conversation keeps moving after the first ask.
	const FOLLOWUPS: Record<string, string[]> = {
		'/': ['Draft the SoundExchange registration for me', 'How did you find this money?'],
		'/label': ['Which artists should we register first?', 'Forecast the recovery for the top five'],
		'/services': ['Set up an intro with the top match', 'What would mastering cost me?'],
		'/connectors/disco': ['Draft the pitch for the best brief', 'Forecast the placement fees']
	};
	const followupsFor = (hint?: RouteHint): string[] =>
		hint ? (FOLLOWUPS[hint.page] ?? []) : [];

	async function scrollDown() {
		await tick();
		if (thread) thread.scrollTop = thread.scrollHeight;
	}

	async function openPanel(prompt?: string) {
		open = true;
		await tick();
		inputEl?.focus();
		if (prompt) send(prompt);
		else scrollDown();
	}

	function closePanel() {
		if (!pinned) open = false;
	}

	onMount(() => {
		const handler = (e: Event) => {
			const detail = (e as CustomEvent).detail ?? {};
			openPanel(detail.prompt);
		};
		window.addEventListener('lode:open', handler);
		const hintTimer = setTimeout(() => (hintArmed = false), 4500);
		const rotate = setInterval(
			() => (suggestionIdx = (suggestionIdx + 1) % suggestions.length),
			3800
		);
		return () => {
			window.removeEventListener('lode:open', handler);
			clearTimeout(hintTimer);
			clearInterval(rotate);
		};
	});

	// Tab accepts the suggested prompt currently showing as the placeholder.
	function acceptSuggestion(e: KeyboardEvent) {
		if (e.key === 'Tab' && !input.trim()) {
			e.preventDefault();
			input = suggestions[suggestionIdx];
		}
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

	// The last thing the user asked — handed to the destination page so it can
	// replay the question and surface the full-width trace / evidence in place.
	function lastUserPrompt(): string {
		for (let i = messages.length - 1; i >= 0; i--) {
			if (messages[i].role === 'user') return messages[i].text;
		}
		return '';
	}

	function follow(hint: RouteHint) {
		const prompt = lastUserPrompt();
		if (prompt) handoffTo(hint.page, prompt);
		pinned = false;
		open = false;
		goto(hint.page);
	}
</script>

<div class="v3-orb-wrap" class:open class:pinned class:hint-armed={hintArmed}>
	{#if open}
		<div class="v3-orb-panel" transition:scale={{ duration: 200, start: 0.92, opacity: 0 }}>
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
				<button class="v3-ico-btn sm" type="button" title="Close" onclick={() => { pinned = false; open = false; }}>
					<Icon name="arrow-right" size={15} color="var(--ink-500)" />
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
						{#if followupsFor(m.hint).length}
							<div class="v3-orb-followups">
								{#each followupsFor(m.hint) as f}
									<button class="v3-orb-followup" type="button" onclick={() => send(f)}>{f}</button>
								{/each}
							</div>
						{/if}
					{/if}
				{/each}
				{#if isTyping}
					<div in:fade class="v3-orb-bubble lode">
						<div class="typing"><span></span><span></span><span></span></div>
					</div>
				{/if}
			</div>

			<form
				class="v3-orb-composer"
				onsubmit={(e) => {
					e.preventDefault();
					send(input);
				}}
			>
				<input
					bind:this={inputEl}
					bind:value={input}
					placeholder={suggestions[suggestionIdx]}
					onkeydown={acceptSuggestion}
				/>
				{#if !input.trim()}
					<span class="v3-orb-tab" aria-hidden="true">Tab</span>
				{/if}
				<button class="v3-orb-send" type="submit" disabled={!input.trim() || isTyping} aria-label="Send">
					<Icon name="arrow-up" size={16} color="#fff" />
				</button>
			</form>
		</div>
	{/if}

	<button class="v3-orb" type="button" aria-label="Open Lode" onclick={() => (open ? closePanel() : openPanel())}>
		<img src="/logo-mark.svg" alt="" width="30" height="30" />
		<span class="v3-orb-hint">Lode is listening</span>
	</button>
</div>
