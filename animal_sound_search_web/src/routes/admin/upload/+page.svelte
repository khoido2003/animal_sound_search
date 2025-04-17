<script lang="ts">
    import Button from '$lib/components/Button.svelte';
    import { createUploader } from '$lib/utils/uploadthing';
    import { UploadButton } from '@uploadthing/svelte';
    import type { OurFileRouter } from '$lib/server/uploadthing';

    interface Sound {
        fileName: string;
        species: string;
    }

    let sound: Sound = {
        fileName: '',
        species: ''
    };
    let error: string = '';
    let success: string = '';
    let uploadedAudioUrl: string = '';
    let isSubmitting: boolean = false;

    // Handle upload via UploadThing
    const uploader = createUploader('audioUploader', {
        onClientUploadComplete: async (res: any) => {
            if (res && res.length > 0) {
                uploadedAudioUrl = res[0].url;
                sound.fileName = res[0].name; // Set fileName to uploaded file's name
                success = 'Audio uploaded successfully! Please fill out species and submit.';
            }
        },
        onUploadError: (err: Error) => {
            error = `Upload failed: ${err.message}`;
        },
        onUploadBegin: () => {
            success = 'Uploading audio...';
            error = ''; // Clear previous errors
        }
    });

    // Handle submission to Python server
    async function submitToPythonServer() {
        if (!sound.species) {
            error = 'Please fill out the species field.';
            return;
        }

        isSubmitting = true;
        error = '';
        success = 'Submitting data to server...';

        try {
            const response = await fetch('http://localhost:5000/api/process-sound', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    fileName: sound.fileName,
                    species: sound.species,
                    url: uploadedAudioUrl
                })
            });

            if (response.ok) {
                success = 'Audio processed and stored successfully!';
                sound = { fileName: '', species: '' }; // Reset form
                uploadedAudioUrl = '';
            } else {
                const data = await response.json();
                error = data.error || 'Failed to process audio';
            }
        } catch (err) {
            error = 'Error communicating with Python server';
        } finally {
            isSubmitting = false;
        }
    }
</script>

<main class="container mx-auto px-4 py-8 bg-retroCream min-h-screen">
    <section class="max-w-3xl mx-auto">
        <h1 class="font-pixel text-3xl text-retroGray mb-6 text-center animate-pulse">
            Add New Animal Sound
        </h1>

        {#if error}
            <div class="bg-retroCoral text-retroCream p-4 rounded-lg mb-6 font-pixel">{error}</div>
        {/if}
        {#if success}
            <div class="bg-retroTeal text-retroCream p-4 rounded-lg mb-6 font-pixel">{success}</div>
        {/if}

        <div class="bg-white p-6 rounded-lg border-4 border-retroBlack shadow-[4px_4px_0_#26A69A] mb-6">
            <h2 class="font-pixel text-xl text-retroGray mb-4">Upload Audio</h2>
            <div class="mb-4">
                <label class="font-pixel text-retroGray block mb-2">File Name</label>
                <input
                    type="text"
                    bind:value={sound.fileName}
                    placeholder="e.g., lion_001.wav"
                    required
                    readonly={uploadedAudioUrl !== ''}                     class="w-full p-2 border-2 border-retroGray bg-retroCream font-pixel text-retroBlack rounded"
                />
            </div>
            <div class="mb-4">
                <label class="font-pixel text-retroGray block mb-2">Species</label>
                <input
                    type="text"
                    bind:value={sound.species}
                    placeholder="e.g., Lion"
                    required
                    class="w-full p-2 border-2 border-retroGray bg-retroCream font-pixel text-retroBlack rounded"
                />
            </div>
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
                        onClick={() => navigator.clipboard.writeText(uploadedAudioUrl).then(() => success = 'URL copied!')}
                    >
                        Copy URL
                    </Button>
                </div>
            {/if}
            {#if uploadedAudioUrl && sound.species}
                <div class="mt-4">
                    <Button
                        variant="primary"
                        subClass="bg-retroCoral text-retroCream hover:bg-retroTeal font-pixel"
                        onClick={submitToPythonServer}
                        disabled={isSubmitting}
                    >
                        {isSubmitting ? 'Submitting...' : 'Submit to Server'}
                    </Button>
                </div>
            {/if}
        </div>
    </section>
</main>

<style>
    .font-pixel {
        font-family: 'Jura', sans-serif;
    }
</style>
