import {
	supportsImageEditing,
	type ImageAdvancedField,
	type ImageAspectRatio,
	type ImageGenerationModel
} from '$lib/utils/image-generation';
import type { ImageCreationDraft } from '$lib/utils/image-generation-batches';
import {
	resolveDraftReferenceImage,
	type ReferenceImage
} from '$lib/components/images/imageReferenceFiles';

export const resolveDraftModel = (
	draft: ImageCreationDraft,
	withReference: boolean,
	primaryModels: ImageGenerationModel[],
	allModels: ImageGenerationModel[]
): ImageGenerationModel | undefined => {
	const requested = primaryModels.find(
		(model) => model.id === draft.modelId || model.editModel === draft.modelId
	);
	if (!withReference || (requested && supportsImageEditing(requested, allModels))) return requested;
	return primaryModels.find((model) => supportsImageEditing(model, allModels));
};

export const prepareImageDraft = async (
	draft: ImageCreationDraft,
	token: string,
	primaryModels: ImageGenerationModel[],
	allModels: ImageGenerationModel[],
	previousCreationName: string
) => {
	const referenceImageUrl = draft.referenceImageUrl
		? await resolveDraftReferenceImage(draft.referenceImageUrl, token)
		: null;
	const referenceImages: ReferenceImage[] = referenceImageUrl
		? [{ url: referenceImageUrl, name: previousCreationName }]
		: [];
	return {
		referenceImages,
		targetModel: resolveDraftModel(draft, Boolean(referenceImageUrl), primaryModels, allModels)
	};
};

const optionalNumber = (field: ImageAdvancedField | null, value: number | null | undefined) =>
	field && value !== null && value !== undefined ? String(value) : '';

export const imageDraftFieldValues = (
	draft: ImageCreationDraft,
	options: {
		aspectRatios: ImageAspectRatio[];
		resolutions: string[];
		qualities: string[];
		outputFormats: string[];
		negativePromptField: ImageAdvancedField | null;
		stepsField: ImageAdvancedField | null;
		seedField: ImageAdvancedField | null;
		guidanceScaleField: ImageAdvancedField | null;
		strengthField: ImageAdvancedField | null;
	}
) => ({
	aspectRatio:
		draft.aspectRatio && options.aspectRatios.includes(draft.aspectRatio)
			? draft.aspectRatio
			: null,
	resolution:
		draft.resolution && options.resolutions.includes(draft.resolution) ? draft.resolution : null,
	quality: draft.quality && options.qualities.includes(draft.quality) ? draft.quality : null,
	outputFormat:
		draft.outputFormat && options.outputFormats.includes(draft.outputFormat)
			? draft.outputFormat
			: null,
	negativePrompt: options.negativePromptField ? (draft.negativePrompt ?? '') : '',
	steps: optionalNumber(options.stepsField, draft.steps),
	seed: optionalNumber(options.seedField, draft.seed),
	guidanceScale: optionalNumber(options.guidanceScaleField, draft.guidanceScale),
	strength: optionalNumber(options.strengthField, draft.strength),
	prompt: draft.prompt ?? ''
});
