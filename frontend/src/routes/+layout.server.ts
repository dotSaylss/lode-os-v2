import type { LayoutServerLoad } from './$types';
import { api } from '$lib/api';

// The active demo workspace (persona) scopes the whole app — nav, data,
// connectors, and what the agents see. Loaded here so every page and the
// rail switcher agree, and refreshed via invalidateAll() after switching.
export const load: LayoutServerLoad = async ({ fetch }) => {
	try {
		const res = await fetch(api('/api/v1/personas'));
		if (res.ok) {
			const data = await res.json();
			return { personas: data.personas ?? [], activePersona: data.active ?? 'june' };
		}
	} catch (e) {
		console.error('Failed to fetch personas from FastAPI', e);
	}
	return { personas: [], activePersona: 'june' };
};
