import type { PageServerLoad } from './$types';
import { api } from '$lib/api';

const emptyForecast = {
    total_recoverable: 0,
    artists_with_gaps: 0,
    categories: [] as Array<{
        type: string;
        label: string;
        artists_affected: number;
        recoverable: number;
        recovery_months: number;
    }>,
    forecast: [] as Array<{ month: number; cumulative_recovered: number }>
};

export const load: PageServerLoad = async ({ fetch }) => {
    let portfolio = {
        label_profile: { id: '', name: 'Label', total_artists: 0 },
        total_artists: 0,
        total_ytd: 0,
        total_uncollected: 0,
        neighboring_rights_artists: 0,
        neighboring_rights_uncollected: 0,
        artists: []
    };
    let forecast = emptyForecast;

    try {
        const res = await fetch(api('/api/v1/label/portfolio'));
        if (res.ok) {
            portfolio = await res.json();
        }
    } catch (e) {
        console.error('Failed to fetch label portfolio from FastAPI', e);
    }

    try {
        const res = await fetch(api('/api/v1/label/forecast'));
        if (res.ok) {
            forecast = await res.json();
        }
    } catch (e) {
        console.error('Failed to fetch label forecast from FastAPI', e);
    }

    return { portfolio, forecast };
};
