// Single source of truth for the backend API base URL.
//
// Local dev: the FastAPI backend runs on :8000. In production set PUBLIC_API_BASE
// (browser) and optionally PUBLIC_API_BASE_SSR (server-side loads through a proxy)
// at build/run time to the deployed backend URL.
import { browser } from '$app/environment';
import { env } from '$env/dynamic/public';

export const API_BASE =
	(browser ? env.PUBLIC_API_BASE : env.PUBLIC_API_BASE_SSR || env.PUBLIC_API_BASE) ||
	'http://localhost:8000';

/** Build a full API URL from a path like "/api/providers". */
export const api = (path: string) => `${API_BASE}${path}`;
