<script lang="ts">
    import Button from '$lib/components/Button.svelte';
    import { createUploader } from '$lib/utils/uploadthing';
    import { UploadButton } from '@uploadthing/svelte';

    interface SearchResult {
        fileName: string;
        species: string;
        url: string;
        similarity: number;
    }

    let uploadedAudioUrl: string = '';
    let error: string = '';
    let success: string = '';
    let isSearching: boolean = false;
    let results: SearchResult[] = [];

    // Handle upload via UploadThing
    const uploader = createUploader('audioUploader', {
        onClientUploadComplete: async (res: any) => {
            if (res && res.length > 0) {
                uploadedAudioUrl = res[0].url;
                success = 'Audio uploaded successfully! Click to search for similar sounds.';
                error = '';
            }
        },
        onUploadError: (err: Error) => {
            error = `Upload failed: ${err.message}`;
            uploadedAudioUrl = '';
            success = '';
        },
        onUploadBegin: () => {
            success = 'Uploading audio...';
            error = '';
        }
    });

    // Handle search request to Python server
    async function searchSimilarSounds() {
        if (!uploadedAudioUrl) {
            error = 'Please upload an audio file first.';
            return;
        }

        isSearching = true;
        error = '';
        success = 'Searching for similar sounds...';

        try {
            const response = await fetch('http://localhost:5000/api/search-sounds', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url: uploadedAudioUrl })
            });

            if (response.ok) {
                const data = await response.json();
                if (data.results) {
                    results = data.results;
                    success = 'Search complete! Here are the top 3 similar sounds.';
                } else {
                    error = data.error || 'No similar sounds found';
                    results = [];
                }
            } else {
                const data = await response.json();
                error = data.error || 'Failed to search for similar sounds';
                results = [];
            }
        } catch (err) {
            error = 'Error communicating with Python server';
            results = [];
        } finally {
            isSearching = false;
        }
    }
</script>

<main class="container mx-auto px-4 py-8 bg-retroCream min-h-screen">
    <section class="max-w-3xl mx-auto">
        <h1 class="font-pixel text-3xl text-retroGray mb-6 text-center animate-pulse">
            Find Similar Animal Sounds
        </h1>

        {#if error}
            <div class="bg-retroCoral text-retroCream p-4 rounded-lg mb-6 font-pixel">{error}</div>
        {/if}
        {#if success}
            <div class="bg-retroTeal text-retroCream p-4 rounded-lg mb-6 font-pixel">{success}</div>
        {/if}

        <div class="bg-white p-6 rounded-lg border-4 border-retroBlack shadow-[4px_4px_0_#26A69A] mb-6">
            <h2 class="font-pixel text-xl text-retroGray mb-4">Upload Audio</h2>
            <UploadButton
                {uploader}
                class="ut-button bg-retroBlue text-retroCream hover:bg-retroCoral font-pixel px-3 py-1.5 rounded-md text-xs cursor-pointer"
            >
                <span slot="button-content" let:state>
                    {state.isUploading ? 'Uploading...' : 'Upload Audio'}
                </span>
            </UploadButton>
            {#if uploadedAudioUrl}
                <div class="mt-4">
                    <p class="font-pixel text-retroGray">Uploaded Audio URL:</p>
                    <input
                        type="text"
                        value={uploadedAudioUrl}
                        readonly
                        class="w-full p-2 border-2 border-retroGray bg-retroCream font-pixel text-retroBlack rounded mb-2"
                    />
                    <Button
                        variant="secondary"
                        subClass="bg-retroPlum text-retroCream hover:bg-retroPurple"
                        onClick={() => navigator.clipboard.writeText(uploadedAudioUrl).then(() => (success = 'URL copied!'))}
                    >
                        Copy URL
                    </Button>
                </div>
            {/if}
            {#if uploadedAudioUrl}
                <div class="mt-4">
                    <Button
                        variant="primary"
                        subClass="bg-retroCoral text-retroCream hover:bg-retroTeal font-pixel"
                        onClick={searchSimilarSounds}
                        disabled={isSearching}
                    >
                        {isSearching ? 'Searching...' : 'Find Similar Sounds'}
                    </Button>
                </div>
            {/if}
        </div>

        {#if results.length > 0}
            <div class="bg-white p-6 rounded-lg border-4 border-retroBlack shadow-[4px_4px_0_#26A69A]">
                <h2 class="font-pixel text-xl text-retroGray mb-4">Top 3 Similar Sounds</h2>
                {#each results as result}
                    <div class="border-2 border-retroGray p-4 rounded-lg mb-4">
                        <p class="font-pixel text-retroBlack"><strong>File:</strong> {result.fileName}</p>
                        <p class="font-pixel text-retroBlack"><strong>Species:</strong> {result.species}</p>
                        <p class="font-pixel text-retroBlack">
                            <strong>Similarity:</strong> {(result.similarity * 100).toFixed(2)}%
                        </p>
                        <p class="font-pixel text-retroBlack">
                            <strong>URL:</strong>
                            <a href={result.url} target="_blank" class="text-retroBlue hover:underline">Listen</a>
                        </p>
                    </div>
                {/each}
            </div>
        {/if}
    </section>
</main>

<style>
    .font-pixel {
        font-family: 'Jura', sans-serif;
    }
</style>
