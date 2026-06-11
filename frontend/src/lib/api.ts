// Single source of truth for the backend API base URL.
//
// Local dev: the FastAPI/ADK backend runs on :8000. In production (Cloud Run),
// set PUBLIC_API_BASE at build/run time to the deployed backend URL. Using the
// dynamic public env avoids a hard build-time requirement when it's unset.
//
// PUBLIC_API_BASE_SSR optionally overrides the base for server-side loads —
// needed when the browser reaches the backend through a proxy hostname the
// node process can't (e.g. mobile review over Tailscale: the phone hits the
// tailnet URL while SSR talks to the backend over loopback).
import { browser } from '$app/environment';
import { env } from '$env/dynamic/public';

export const API_BASE =
	(browser ? env.PUBLIC_API_BASE : env.PUBLIC_API_BASE_SSR || env.PUBLIC_API_BASE) ||
	'http://localhost:8000';

/** Build a full API URL from a path like "/api/v1/chat". */
export const api = (path: string) => `${API_BASE}${path}`;
