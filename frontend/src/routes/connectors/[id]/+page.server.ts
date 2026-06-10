import type { PageServerLoad } from './$types';
import { error } from '@sveltejs/kit';
import { api } from '$lib/api';

export const load: PageServerLoad = async ({ fetch, params }) => {
	try {
		const res = await fetch(api(`/api/v1/connectors/${params.id}`));
		if (res.ok) {
			const detail = await res.json();
			return { connector: detail.connector, config: detail.config };
		}
		if (res.status === 404) {
			throw error(404, 'Connector not found');
		}
	} catch (e) {
		// Re-throw SvelteKit errors; otherwise fall through to a soft failure.
		if (e && typeof e === 'object' && 'status' in e) throw e;
		console.error('Failed to fetch connector detail from FastAPI', e);
	}

	throw error(503, 'Could not reach the connectors backend. Is it running?');
};
