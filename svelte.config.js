import adapterStatic from '@sveltejs/adapter-static';
import adapterAuto from '@sveltejs/adapter-auto';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';
import { preprocessMeltUI } from '@melt-ui/pp';
import sequence from "svelte-sequential-preprocessor";
import * as path from "node:path";
import * as fs from "node:fs/promises";

const cwd = path.resolve(".");
const version_groups = JSON.parse(await fs.readFile(`static/versions.json`));
const versions = Object.values(version_groups).flat();
const routes = ["/"];
for (const version of versions) {
	const info = JSON.parse(await fs.readFile(`static/${version}/info.json`));
	for (const [arch, abilist] of Object.entries(info)) {
		for (const abi of abilist) {
			routes.push(`/${version}/${arch}-${abi}`);
		}
	}
}

/** @type {import('@sveltejs/kit').Config} */
const config = {
	// Consult https://kit.svelte.dev/docs/integrations#preprocessors
	// for more information about preprocessors
	preprocess: sequence([vitePreprocess(), preprocessMeltUI()]) ,

	kit: {
		adapter: adapterStatic({
			// default options are shown. On some platforms
			// these options are set automatically — see below
			pages: '_build',
			assets: '_build',
			fallback: undefined,
			precompress: false,
			strict: true,
		}),
		// adapter: adapterAuto({}),
		prerender: {
			entries: routes,
		}
	}
};

export default config;
