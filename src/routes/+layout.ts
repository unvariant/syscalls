import type { PageLoad } from './$types';
export const prerender = true;

export const load: PageLoad = async ({ fetch, params }) => {
	// TODO: load latest version is params.version is undefined
	params.version = "v5.0";
	const res = await fetch(`/${params.version}/info.json`);
	const arches = await res.json();
	for (const [arch, abilist] of Object.entries<string[]>(arches)) {
		arches[arch] = abilist.map((abi) => `${arch}-${abi}`);
	}
	return { arches };
};
