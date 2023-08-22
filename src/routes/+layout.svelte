<script>
    export let data;
</script>

<nav>
    <a href="/">all</a>
    <!-- {#each data.archs as { arch } }
        <a href="/{arch}">{arch}</a>
    {/each} -->
</nav>

<main>
    <slot />
</main>
