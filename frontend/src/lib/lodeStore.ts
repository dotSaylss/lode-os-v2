// Orb → page handoff.
//
// The floating Lode orb is the single point of contact with the assistant.
// When it answers a question whose rich detail lives on a specific page (the
// label A2A trace, the services grounding evidence), it navigates there and
// drops a "pending prompt" here. The destination page reads it on mount,
// reveals its agent panel, and replays the prompt so the full-width signal
// (trace / evidence) renders in place. One-shot: reading clears it.

import { writable } from 'svelte/store';

export type PendingAsk = { page: string; prompt: string } | null;

export const pendingAsk = writable<PendingAsk>(null);

/** Orb calls this when it wants a page to open + replay a prompt. */
export function handoffTo(page: string, prompt: string) {
	pendingAsk.set({ page, prompt });
}

/** A page calls this once it has consumed the pending ask, so it fires only once. */
export function clearPending() {
	pendingAsk.set(null);
}

// Sidebar preference. Owned here (not in the layout) so the Settings page can
// drive it and the rail reacts live.
const RAIL_KEY = 'lode_rail_locked';

export const railLocked = writable<boolean>(false);

/** Read the persisted preference once on the client; safe to call repeatedly. */
export function initRailLock() {
	if (typeof localStorage === 'undefined') return;
	try {
		railLocked.set(localStorage.getItem(RAIL_KEY) === '1');
	} catch {}
}

export function setRailLocked(v: boolean) {
	railLocked.set(v);
	try {
		localStorage.setItem(RAIL_KEY, v ? '1' : '0');
	} catch {}
}
