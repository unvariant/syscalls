<script lang="ts">
    export let data;
</script>

<table>
    {#each data.syscalls as { nr, abi, name, entrypoint }}
        <tr>
            <td>{nr}</td>
            <td>{abi}</td>
            <td>{name}</td>
            <td>{entrypoint}</td>
            <td>
                {#if data.all.get(name) }
                    {data.all.get(name).args.map(({ type, name }) => `${type} ${name}`) }
                {:else}
                    n/a
                {/if}
            </td>
        </tr>
    {/each}
</table>