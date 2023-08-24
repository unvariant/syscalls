import { error } from '@sveltejs/kit';
import type { PageLoad } from './$types';
export const prerender = true;

export const load: PageLoad = async ({ fetch }) => {
	const res = await fetch(`/json/info.json`);
	return {
		arches: await res.json()
	};
};
