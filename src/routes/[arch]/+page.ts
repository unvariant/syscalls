import { error } from '@sveltejs/kit';
import type { PageLoad } from './$types';
export const prerender = true;

export const load: PageLoad = async ({ fetch, params }) => {
  const res = await fetch(`/json/${params.arch}.json`);
  if (res.status !== 200) throw error(404, "Not found") ;
	return await res.json();
};
