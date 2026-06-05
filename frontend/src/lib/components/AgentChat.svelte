<script lang="ts">
	import { fade, slide } from 'svelte/transition';
	import { api } from '$lib/api';
	import Icon from '$lib/components/Icon.svelte';

	let messages = $state([
		{
			id: 1,
			role: 'agent',
			content:
				"I've looked over June Freedom's profile and noticed missing neighboring rights. Want me to draft a registration to ASCAP or SoundExchange to claim the estimated $2,400?"
		}
	]);
	let inputMessage = $state('');
	let isTyping = $state(false);

	async function sendMessage() {
		if (!inputMessage.trim()) return;
		const userMsg = inputMessage;
		messages = [...messages, { id: Date.now(), role: 'user', content: userMsg }];
		inputMessage = '';
		isTyping = true;

		try {
			const res = await fetch(api('/api/v1/chat'), {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ message: userMsg })
			});

			if (res.ok) {
				const data = await res.json();
				messages = [...messages, { id: Date.now() + 1, role: 'agent', content: data.response }];
			} else {
				throw new Error('Backend responded with an error');
			}
		} catch (error) {
			messages = [
				...messages,
				{
					id: Date.now() + 1,
					role: 'agent',
					content:
						"I'm having trouble reaching the agent backend right now. Make sure the API server is running."
				}
			];
		} finally {
			isTyping = false;
		}
	}
</script>

<div class="chat-card">
	<div class="chat-head">
		<img src="/logo-mark.svg" alt="" width="30" height="30" />
		<div class="chat-head-meta">
			<b>Lode</b>
			<span><span class="chat-live"></span> Orchestrator · ADK 2.0</span>
		</div>
	</div>

	<div class="chat-thread">
		{#each messages as msg (msg.id)}
			<div in:slide={{ duration: 280 }} class="v3-orb-bubble {msg.role === 'user' ? 'user' : 'lode'}">
				<p>{msg.content}</p>
			</div>
		{/each}
		{#if isTyping}
			<div in:fade class="v3-orb-bubble lode">
				<div class="typing"><span></span><span></span><span></span></div>
			</div>
		{/if}
	</div>

	<form
		class="v3-orb-composer chat-composer"
		onsubmit={(e) => {
			e.preventDefault();
			sendMessage();
		}}
	>
		<input bind:value={inputMessage} placeholder="Ask Lode about your royalties…" />
		<button class="v3-orb-send" type="submit" disabled={!inputMessage.trim()} aria-label="Send">
			<Icon name="arrow-up" size={16} color="#fff" />
		</button>
	</form>
</div>

<style>
	.chat-card {
		display: flex;
		flex-direction: column;
		height: 100%;
		background: var(--paper-0);
		border: 1px solid var(--paper-200);
		border-radius: var(--r-2xl);
		box-shadow: var(--v3-sh-md);
		overflow: hidden;
	}
	.chat-head {
		display: flex;
		align-items: center;
		gap: 11px;
		padding: 16px 18px;
		border-bottom: 1px solid var(--paper-200);
		background: linear-gradient(180deg, var(--sg-50), var(--paper-0));
	}
	.chat-head-meta b {
		display: block;
		font-size: 14px;
		font-weight: 700;
		color: var(--ink-900);
	}
	.chat-head-meta span {
		display: flex;
		align-items: center;
		gap: 6px;
		font-size: 11.5px;
		color: var(--ink-muted);
		margin-top: 1px;
	}
	.chat-live {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		background: var(--sg-500);
	}
	.chat-thread {
		flex: 1;
		overflow-y: auto;
		padding: 18px;
		display: flex;
		flex-direction: column;
		gap: 12px;
		min-height: 0;
	}
	.chat-composer {
		margin: 14px;
	}
</style>
