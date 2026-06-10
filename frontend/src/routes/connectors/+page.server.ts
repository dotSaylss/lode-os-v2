import type { PageServerLoad } from './$types';
import { api } from '$lib/api';

export const load: PageServerLoad = async ({ fetch }) => {
    try {
        const res = await fetch(api('/api/v1/connectors'));
        if (res.ok) {
            const connectors = await res.json();
            return { connectors };
        }
    } catch (e) {
        console.error('Failed to fetch connectors from FastAPI', e);
    }

    return { connectors: [] };
};
