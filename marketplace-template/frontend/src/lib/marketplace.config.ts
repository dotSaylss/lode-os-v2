// Marketplace UI configuration — the frontend mirror of backend/config.py.
//
// Re-theme the template by editing this file: the page copy, the category
// labels, and the muted per-category tones. Keep CATEGORY_LABELS keys in sync
// with the backend's CATEGORIES keys (the `category` field on each provider).

export const MARKETPLACE = {
	name: 'Sound Collective',
	// Page header.
	eyebrow: 'Services',
	title: "Bring your song to life",
	subtitle:
		"Vetted collaborators matched to your song's needs, with the evidence behind every match.",
	// Brief composer.
	briefLabel: "Describe your song's needs",
	briefPlaceholder:
		'e.g. I need my track mixed, mastered, and cover art for a lo-fi hip-hop single.',
	briefCta: 'Find my team',
	// Matchmaker chat header.
	matchmakerName: 'Matchmaker',
	matchmakerTagline: 'grounded in the vetted marketplace'
};

export const CATEGORY_LABELS: Record<string, string> = {
	mixing: 'Mixing',
	mastering: 'Mastering',
	cover_art: 'Cover Art',
	vocal_production: 'Vocal Production',
	sync_licensing: 'Sync Licensing',
	music_video: 'Music Video',
	promotion: 'Promotion',
	session_musician: 'Session Players'
};

// Muted, on-brand tones per category (sage / terra / slate / amber — never loud).
export const CATEGORY_TONE: Record<string, string> = {
	mixing: 'tone-slate',
	mastering: 'tone-sage',
	cover_art: 'tone-terra',
	vocal_production: 'tone-sage',
	sync_licensing: 'tone-slate',
	music_video: 'tone-amber',
	promotion: 'tone-terra',
	session_musician: 'tone-sage'
};

export const AVATAR_TONE: Record<string, string> = {
	mixing: 'av-slate',
	mastering: 'av-sage',
	cover_art: 'av-terra',
	vocal_production: 'av-sage',
	sync_licensing: 'av-slate',
	music_video: 'av-terra',
	promotion: 'av-terra',
	session_musician: 'av-sage'
};

export const categoryLabel = (cat: string) =>
	CATEGORY_LABELS[cat] ?? cat.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
export const categoryTone = (cat: string) => CATEGORY_TONE[cat] ?? 'tone-neutral';
export const avatarTone = (cat: string) => AVATAR_TONE[cat] ?? 'av-slate';
