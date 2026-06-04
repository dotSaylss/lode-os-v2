import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch }) => {
    try {
        const res = await fetch('http://localhost:8000/api/v1/artist/context');
        if (res.ok) {
            const data = await res.json();
            return { artistContext: data };
        }
    } catch (e) {
        console.error('Failed to fetch from FastAPI', e);
    }
    
    // Return empty fallback if backend is not running
    return {
        artistContext: {
            artist_profile: { name: 'Unknown', ytd_earnings: 0 },
            connected_sources: [],
            neighboring_rights: { registered: false, estimated_missing: 0 }
        }
    };
};
