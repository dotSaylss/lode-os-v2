import type { PageServerLoad } from './$types';
import { api } from '$lib/api';

export const load: PageServerLoad = async ({ fetch }) => {
    try {
        const res = await fetch(api('/api/v1/label/portfolio'));
        if (res.ok) {
            const data = await res.json();
            return { portfolio: data };
        }
    } catch (e) {
        console.error('Failed to fetch label portfolio from FastAPI', e);
    }

    // Fallback if the backend is not running.
    return {
        portfolio: {
            label_profile: { id: '', name: 'Label', total_artists: 0 },
            total_artists: 0,
            total_ytd: 0,
            total_uncollected: 0,
            neighboring_rights_artists: 0,
            neighboring_rights_uncollected: 0,
            artists: []
        }
    };
};
