import { error } from '@sveltejs/kit';
import type { PageLoad } from './$types';
export const prerender = true;

export const load: PageLoad = async ({ fetch, params }) => {
  const res = await fetch(`/${params.version}/${params.arch}.json`);
  if (res.status !== 200) throw error(404, "Not found") ;
	const result = await res.json();
  result.version = params.version;
  result.arch = params.arch;
  return result;
};
