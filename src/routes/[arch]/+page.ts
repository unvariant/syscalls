import type { PageLoad } from './$types';
export const prerender = true;

export const load: PageLoad = async ({ fetch, params }) => {
  const res = await fetch(`/json/${params.arch}.json`);
  return await res.json();
};
