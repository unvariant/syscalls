import { error } from '@sveltejs/kit';
import type { LayoutLoad } from './$types';
export const prerender = true;

export const load: LayoutLoad = async ({ fetch }) => {
  const res = await fetch(`/json/info.json`);
  return {
    "arches": await res.json(),
  };
};
