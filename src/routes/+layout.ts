import type { PageLoad } from './$types';
export const prerender = true;

export const load: PageLoad = async ({ fetch }) => {
	const res = await fetch(`/json/info.json`);
	const arches = await res.json();
	for (const [arch, abilist] of Object.entries<string[]>(arches)) {
		arches[arch] = abilist.map((abi) => `${arch}-${abi}`);
	}
	return { arches };
};
