import { api } from '$lib/api';
import type { PageServerLoad } from './$types';

// Settings shows the live connection list; personas arrive via the layout data.
export const load: PageServerLoad = async ({ fetch }) => {
	try {
		const res = await fetch(api('/api/v1/connectors'));
		if (!res.ok) return { connectors: [] };
		return { connectors: await res.json() };
	} catch {
		return { connectors: [] };
	}
};
