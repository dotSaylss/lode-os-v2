import type { PageServerLoad } from './$types';
import { api } from '$lib/api';

export const load: PageServerLoad = async ({ fetch }) => {
	try {
		const res = await fetch(api('/api/providers'));
		if (res.ok) {
			const providers = await res.json();
			return { providers };
		}
	} catch (e) {
		console.error('Failed to fetch providers from the backend', e);
	}
	return { providers: [] };
};
