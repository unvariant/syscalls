import type { PageLoad } from './$types';
export const prerender = true;

export const load: PageLoad = async ({ fetch, params }) => {
	const ver = await fetch(`/versions.json`);
	const versions = await ver.json();
	const latest = Object.values(versions)[0][0];
	
	const version = params.version || latest;
	const myarch = params.arch || "x86-64";

	const res = await fetch(`/${version}/info.json`);
	const arches = await res.json();
	for (const [arch, abilist] of Object.entries<string[]>(arches)) {
		arches[arch] = abilist.map((abi) => `${arch}-${abi}`);
	}
	return { arches, versions, latest, version, arch: myarch };
};
