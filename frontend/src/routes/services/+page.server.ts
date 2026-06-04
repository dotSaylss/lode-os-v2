import type { PageServerLoad } from './$types';

const BACKEND = 'http://localhost:8002';

export const load: PageServerLoad = async ({ fetch }) => {
    try {
        const res = await fetch(`${BACKEND}/api/v1/services/providers`);
        if (res.ok) {
            const providers = await res.json();
            return { providers };
        }
    } catch (e) {
        console.error('Failed to fetch providers from FastAPI', e);
    }

    return { providers: [] };
};
