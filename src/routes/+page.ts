import { error } from '@sveltejs/kit';
import type { PageLoad } from './$types';
export const prerender = true;

export const load: PageLoad = async ({ fetch, params }) => {
	const ver = await fetch(`/versions.json`);
	const versions = await ver.json();
	const latest = Object.values(versions)[0][0];
  const arch = "x86-64";

  const res = await fetch(`/${latest}/${arch}.json`);
  if (res.status !== 200) error(404, "Not found");
  const result = await res.json();
  result.version = latest;
  result.arch = arch;

  const regs = await fetch(`/registers.json`);
  const allregs = await regs.json();
  result.registers = allregs[arch];

  return result;
};
