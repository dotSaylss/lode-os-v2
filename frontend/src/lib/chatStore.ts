// Chat threads for the chat-first home (`/`).
//
// The conversation with Lode IS the product surface now, so threads persist
// across visits (localStorage) and are scoped to the active workspace — June's
// chats never bleed into the label's. Each thread keeps its ADK session_id so
// reopening a chat resumes the same multi-turn session on the backend.

import { writable, get } from 'svelte/store';

export type RouteHint = { page: string; label: string; reason?: string };
export type TraceStep = { kind: string; label: string; detail?: string };
export type ChatMsg = {
	id: number;
	role: 'user' | 'lode';
	text: string;
	hint?: RouteHint;
	tier?: 'fast' | 'reasoning';
	trace?: TraceStep[];
};
export type ChatThread = {
	id: string;
	persona: string;
	title: string;
	sessionId: string | null;
	messages: ChatMsg[];
	updatedAt: number;
};

const KEY = 'lode_chats_v1';

export const threads = writable<ChatThread[]>([]);
export const activeThreadId = writable<string | null>(null);

let initialized = false;

/** Load persisted threads once on the client; safe to call repeatedly. */
export function initChats() {
	if (initialized || typeof localStorage === 'undefined') return;
	initialized = true;
	try {
		const raw = localStorage.getItem(KEY);
		if (raw) threads.set(JSON.parse(raw));
	} catch {}
	threads.subscribe((all) => {
		try {
			localStorage.setItem(KEY, JSON.stringify(all));
		} catch {}
	});
}

export function createThread(persona: string): ChatThread {
	// Reuse an existing empty thread for this workspace instead of stacking
	// blank ones every time New chat is pressed.
	const existing = get(threads).find((t) => t.persona === persona && t.messages.length === 0);
	if (existing) {
		activeThreadId.set(existing.id);
		return existing;
	}
	const t: ChatThread = {
		id: `t${Date.now()}`,
		persona,
		title: 'New chat',
		sessionId: null,
		messages: [],
		updatedAt: Date.now()
	};
	threads.update((all) => [t, ...all]);
	activeThreadId.set(t.id);
	return t;
}

export function appendMessage(threadId: string, msg: ChatMsg) {
	threads.update((all) =>
		all.map((t) => {
			if (t.id !== threadId) return t;
			const title =
				t.title === 'New chat' && msg.role === 'user'
					? msg.text.length > 52
						? msg.text.slice(0, 52).trimEnd() + '…'
						: msg.text
					: t.title;
			return { ...t, title, messages: [...t.messages, msg], updatedAt: Date.now() };
		})
	);
}

export function setSession(threadId: string, sessionId: string) {
	threads.update((all) =>
		all.map((t) => (t.id === threadId ? { ...t, sessionId } : t))
	);
}

/** Recent threads for a workspace, newest first. */
export function recentFor(all: ChatThread[], persona: string, limit = 4): ChatThread[] {
	return all
		.filter((t) => t.persona === persona && t.messages.length > 0)
		.sort((a, b) => b.updatedAt - a.updatedAt)
		.slice(0, limit);
}

/** Wipe every thread on this device (Settings → Clear chat history). */
export function clearAllThreads() {
	threads.set([]);
	activeThreadId.set(null);
	try {
		localStorage.removeItem(KEY);
	} catch {}
}

export function threadById(id: string | null): ChatThread | undefined {
	if (!id) return undefined;
	return get(threads).find((t) => t.id === id);
}
