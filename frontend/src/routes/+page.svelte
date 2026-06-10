<script lang="ts">
	/**
	 * The chat-first home. The conversation with Lode is the product's focal
	 * point (think Claude chat): one calm thread, agent observability inline —
	 * which specialist was consulted (A2A), what context was read (MCP tools),
	 * which Gemini tier answered — and route cards into the deeper workspace
	 * views (Today / Catalog / Services / Connectors) when the full detail
	 * deserves a full-width page.
	 */
	import { tick, onMount } from 'svelte';
	import { fade } from 'svelte/transition';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { handoffTo } from '$lib/lodeStore';
	import {
		threads,
		activeThreadId,
		initChats,
		createThread,
		appendMessage,
		setSession,
		recentFor,
		type ChatThread,
		type ChatMsg,
		type RouteHint
	} from '$lib/chatStore';
	import Icon from '$lib/components/Icon.svelte';

	let { data } = $props();
	const persona = $derived<string>(data.activePersona ?? 'june');
	const personaName = $derived<string>(
		(data.personas ?? []).find((p: { id: string }) => p.id === persona)?.name ?? 'there'
	);

	// Per-workspace voice: greeting name, one-line promise, starter prompts.
	const PERSONA_UI: Record<string, { first: string; vp: string; suggestions: string[] }> = {
		june: {
			first: 'June',
			vp: "I watch every royalty source you're connected to, find the money you're owed, and file what's missing.",
			suggestions: [
				'Where am I losing money?',
				'Draft my SoundExchange registration',
				'Who can master my next single?',
				'What did I earn this year?'
			]
		},
		label: {
			first: 'Lode Records',
			vp: 'Ask across the whole roster — catalog audits, bulk registrations, recovery forecasts, sync pitches.',
			suggestions: [
				"What's our biggest catalog opportunity?",
				'Which artists should we register first?',
				'Forecast the recovery for the top five',
				"Pitch the roster into this week's sync briefs"
			]
		},
		kai: {
			first: 'Kai',
			vp: 'Your library, rights, and licensing talk to each other here — ask me to move a track from playlist to paycheck.',
			suggestions: [
				"Pitch my Sync Ready playlist into this week's briefs",
				'Which of my tracks fits a film brief?',
				'Who can mix my next drop?',
				'Is Suno connected to my library?'
			]
		}
	};
	const ui = $derived(PERSONA_UI[persona] ?? PERSONA_UI.june);

	const greeting = () => {
		const h = new Date().getHours();
		return h < 12 ? 'Good morning' : h < 18 ? 'Good afternoon' : 'Good evening';
	};

	// Next-step actions offered under an answer, keyed by where the concierge
	// routed — so the conversation keeps moving after the first ask.
	const FOLLOWUPS: Record<string, string[]> = {
		'/today': ['Draft the SoundExchange registration for me', 'How did you find this money?'],
		'/label': ['Which artists should we register first?', 'Forecast the recovery for the top five'],
		'/services': ['Set up an intro with the top match', 'What would mastering cost me?'],
		'/connectors/disco': ['Draft the pitch for the best brief', 'Forecast the placement fees']
	};
	const followupsFor = (hint?: RouteHint): string[] => (hint ? (FOLLOWUPS[hint.page] ?? []) : []);

	let input = $state('');
	let isTyping = $state(false);
	let scroller: HTMLDivElement | undefined = $state();
	let composerEl: HTMLTextAreaElement | undefined = $state();

	const active = $derived<ChatThread | undefined>(
		$threads.find((t) => t.id === $activeThreadId && t.persona === persona)
	);
	const inThread = $derived(!!active && active.messages.length > 0);
	const recents = $derived(recentFor($threads, persona));

	// Starter prompts rotate through the composer's placeholder; Tab accepts one.
	let suggestionIdx = $state(0);

	onMount(() => {
		initChats();
		composerEl?.focus();
		const rotate = setInterval(() => (suggestionIdx = (suggestionIdx + 1) % ui.suggestions.length), 3800);
		return () => clearInterval(rotate);
	});

	async function scrollDown() {
		await tick();
		if (scroller) scroller.scrollTop = scroller.scrollHeight;
	}

	function autogrow() {
		if (!composerEl) return;
		composerEl.style.height = 'auto';
		composerEl.style.height = Math.min(composerEl.scrollHeight, 180) + 'px';
		composerEl.style.overflowY = composerEl.scrollHeight > 180 ? 'auto' : 'hidden';
	}

	function onComposerKey(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			send(input);
		} else if (e.key === 'Tab' && !input.trim()) {
			e.preventDefault();
			input = ui.suggestions[suggestionIdx];
			autogrow();
		}
	}

	async function send(text: string) {
		const q = text.trim();
		if (!q || isTyping) return;
		const thread = active ?? createThread(persona);
		appendMessage(thread.id, { id: Date.now(), role: 'user', text: q });
		input = '';
		await tick();
		autogrow();
		isTyping = true;
		scrollDown();

		try {
			const res = await fetch(api('/api/v1/ask'), {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ message: q, session_id: thread.sessionId })
			});
			if (!res.ok) throw new Error('bad response');
			const payload = await res.json();
			if (payload.session_id) setSession(thread.id, payload.session_id);
			appendMessage(thread.id, {
				id: Date.now() + 1,
				role: 'lode',
				text: payload.response,
				hint: payload.route_hint ?? undefined,
				tier: payload.tier ?? undefined,
				trace: payload.trace ?? undefined
			});
		} catch {
			appendMessage(thread.id, {
				id: Date.now() + 1,
				role: 'lode',
				text: "I'm having trouble reaching the workspace right now. Make sure the API server is running."
			});
		} finally {
			isTyping = false;
			scrollDown();
		}
	}

	// Last user prompt — handed to the destination page so it can replay the
	// question and surface its full-width trace / evidence in place.
	function lastUserPrompt(): string {
		const msgs = active?.messages ?? [];
		for (let i = msgs.length - 1; i >= 0; i--) {
			if (msgs[i].role === 'user') return msgs[i].text;
		}
		return '';
	}

	function follow(hint: RouteHint) {
		const prompt = lastUserPrompt();
		if (prompt) handoffTo(hint.page, prompt);
		goto(hint.page);
	}

	function openThread(t: ChatThread) {
		activeThreadId.set(t.id);
		scrollDown();
	}

	const stepIcon = (kind: string) => (kind === 'handoff' ? 'arrow-left-right' : 'plug');
</script>

<div class="v3-chat">
	{#if !inThread}
		<!-- Empty state: the greeting IS the front door. -->
		<div class="v3-chat-hero">
			<img src="/logo-mark.svg" alt="" width="44" height="44" class="v3-chat-mark" />
			<h1>{greeting()}, {ui.first}.</h1>
			<p class="v3-chat-vp">{ui.vp}</p>

			<form
				class="v3-chat-composer hero"
				onsubmit={(e) => {
					e.preventDefault();
					send(input);
				}}
			>
				<textarea
					bind:this={composerEl}
					bind:value={input}
					rows="1"
					placeholder={ui.suggestions[suggestionIdx]}
					oninput={autogrow}
					onkeydown={onComposerKey}
				></textarea>
				{#if !input.trim()}
					<span class="v3-chat-tab" aria-hidden="true">Tab</span>
				{/if}
				<button class="v3-chat-send" type="submit" disabled={!input.trim() || isTyping} aria-label="Send">
					<Icon name="arrow-up" size={18} color="#fff" />
				</button>
			</form>

			<div class="v3-chat-chips">
				{#each ui.suggestions as s}
					<button class="v3-chat-chip" type="button" onclick={() => send(s)}>{s}</button>
				{/each}
			</div>

			{#if recents.length}
				<div class="v3-chat-recents">
					<span class="v3-chat-recents-head">Recent</span>
					{#each recents as t (t.id)}
						<button class="v3-chat-recent" type="button" onclick={() => openThread(t)}>
							<Icon name="clock" size={14} color="var(--ink-muted)" />
							<span>{t.title}</span>
						</button>
					{/each}
				</div>
			{/if}

			<p class="v3-chat-stack">Gemini 2.5 Flash + Pro &middot; ADK multi-agent &middot; MCP connectors</p>
		</div>
	{:else}
		<!-- Active conversation. -->
		<div class="v3-chat-thread" bind:this={scroller}>
			<div class="v3-chat-scroll">
				{#each active!.messages as m (m.id)}
					{#if m.role === 'user'}
						<div class="v3-chat-msg user"><p>{m.text}</p></div>
					{:else}
						<div class="v3-chat-msg lode">
							<img src="/logo-mark.svg" alt="" width="28" height="28" class="v3-chat-avatar" />
							<div class="v3-chat-body">
								{#if m.trace?.length}
									<div class="v3-chat-trace">
										{#each m.trace as step}
											<span class="v3-chat-step">
												<Icon name={stepIcon(step.kind)} size={12} color="var(--sg-600)" />
												{step.label}
											</span>
										{/each}
									</div>
								{/if}
								<p class="v3-chat-text">{m.text}</p>
								{#if m.tier}
									<span class="v3-chat-tier">
										<Icon name={m.tier === 'fast' ? 'zap' : 'sparkles'} size={11} color="currentColor" />
										{m.tier === 'fast' ? 'Gemini 2.5 Flash · fast tier' : 'Gemini 2.5 Pro · reasoning tier'}
									</span>
								{/if}
								{#if m.hint}
									<button class="v3-chat-route" type="button" onclick={() => follow(m.hint!)}>
										<span class="v3-chat-route-text">
											<b>Open {m.hint.label}</b>
											{#if m.hint.reason}<span>The full detail — {m.hint.reason} — renders there.</span>{/if}
										</span>
										<Icon name="arrow-right" size={16} color="var(--sg-700)" />
									</button>
									{#if followupsFor(m.hint).length}
										<div class="v3-chat-followups">
											{#each followupsFor(m.hint) as f}
												<button class="v3-chat-followup" type="button" onclick={() => send(f)}>{f}</button>
											{/each}
										</div>
									{/if}
								{/if}
							</div>
						</div>
					{/if}
				{/each}
				{#if isTyping}
					<div in:fade class="v3-chat-msg lode">
						<img src="/logo-mark.svg" alt="" width="28" height="28" class="v3-chat-avatar" />
						<div class="typing"><span></span><span></span><span></span></div>
					</div>
				{/if}
			</div>
		</div>

		<div class="v3-chat-dock">
			<form
				class="v3-chat-composer"
				onsubmit={(e) => {
					e.preventDefault();
					send(input);
				}}
			>
				<textarea
					bind:this={composerEl}
					bind:value={input}
					rows="1"
					placeholder="Ask Lode anything about {personaName}'s music business…"
					oninput={autogrow}
					onkeydown={onComposerKey}
				></textarea>
				<button class="v3-chat-send" type="submit" disabled={!input.trim() || isTyping} aria-label="Send">
					<Icon name="arrow-up" size={18} color="#fff" />
				</button>
			</form>
		</div>
	{/if}
</div>
