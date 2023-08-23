import type { PageLoad } from './$types';
export const prerender = true;

export const load: PageLoad = async ({ fetch }) => {
  const res = await fetch('/json/x86-64.json');
  return await res.json();
};
