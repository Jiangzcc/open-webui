/// <reference types="cypress" />

export {};

type CreditAdjustment = {
	direction: 'increase' | 'decrease';
	amount: number;
	reasonCode: 'offline_recharge' | 'promotion_gift' | 'manual_refund';
};

const PNG_BASE64 =
	'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScL9wgAAAABJRU5ErkJggg==';
const TEXT_TO_IMAGE_PRICE = {
	service_type: 'image',
	resource_id: 'dall-e-2',
	action: 'text-to-image',
	base_price: '5',
	rules: { schema_version: 1, dimensions: [{ key: 'image_count', kind: 'quantity' }] },
	enabled: true
};
const IMAGE_TO_IMAGE_PRICE = {
	...TEXT_TO_IMAGE_PRICE,
	action: 'image-to-image'
};
const UI_ONLY_PRICE = {
	serviceType: 'image',
	resourceId: 'ui-multidimensional-e2e',
	action: 'text-to-image',
	basePrice: '3'
};

const authHeaders = (token: string) => ({ Authorization: `Bearer ${token}` });
const creditsApiUrl = Cypress.env('API_URL') || 'http://127.0.0.1:8080';

const requestCredits = <T>(options: Partial<Cypress.RequestOptions>) =>
	cy.request<T>({
		...options,
		failOnStatusCode: false
	} as Cypress.RequestOptions);

const expectSuccess = <T>(response: Cypress.Response<T>) => {
	expect(response.status, JSON.stringify(response.body)).to.be.within(200, 299);
	return response.body;
};

const createPrice = (token: string, price: object) =>
	requestCredits({
		method: 'POST',
		url: `${creditsApiUrl}/api/v1/credits/admin/prices`,
		headers: authHeaders(token),
		body: price
	}).then(expectSuccess);

const adjustCredits = (token: string, userId: string, adjustment: CreditAdjustment) =>
	requestCredits({
		method: 'POST',
		url: `${creditsApiUrl}/api/v1/credits/admin/accounts/${encodeURIComponent(userId)}/adjustments`,
		headers: authHeaders(token),
		body: {
			direction: adjustment.direction,
			amount: adjustment.amount,
			reason_code: adjustment.reasonCode
		}
	}).then(expectSuccess);

const currentBalance = (token: string) =>
	requestCredits<{ balance: number }>({
		method: 'GET',
		url: `${creditsApiUrl}/api/v1/credits/me`,
		headers: authHeaders(token)
	}).then(expectSuccess);

const activateImageBilling = (adminToken: string) =>
	cy
		.then(() => createPrice(adminToken, TEXT_TO_IMAGE_PRICE))
		.then(() => createPrice(adminToken, IMAGE_TO_IMAGE_PRICE));

const openUserMenu = () => cy.get('button[aria-label="User menu"]').click();

const uploadReferenceImage = () =>
	cy.get('input[type="file"]').selectFile({
		contents: Cypress.Buffer.from(PNG_BASE64, 'base64'),
		fileName: 'reference.png',
		mimeType: 'image/png'
	});

const createPriceThroughAdminUi = () => {
	cy.contains('button', 'Credit prices').click();
	cy.contains('New credit price').should('be.visible');
	cy.get('input').eq(0).clear().type(UI_ONLY_PRICE.serviceType);
	cy.get('input').eq(1).clear().type(UI_ONLY_PRICE.resourceId);
	cy.get('input').eq(2).clear().type(UI_ONLY_PRICE.action);
	cy.get('input').eq(3).clear().type(UI_ONLY_PRICE.basePrice);
	cy.contains('option', 'quantity').parent('select').select('quantity');
	cy.get('input[placeholder="Dimension key"]').type('image_count');
	cy.contains('button', 'Save').click();
	cy.contains(UI_ONLY_PRICE.resourceId).should('be.visible');
};

describe('credits image-billing flow', () => {
	let admin: Cypress.SessionUser;
	let user: Cypress.SessionUser;

	before(() => {
		cy.creditsAdmin()
			.then((resolvedAdmin) => {
				admin = resolvedAdmin;
				return cy.creditsUser();
			})
			.then((resolvedUser) => {
				user = resolvedUser;
				return activateImageBilling(admin.token);
			});
	});

	beforeEach(() => {
		cy.resetFakeProvider();
		cy.setFakeProviderMode('success');
	});

	it('lets an administrator configure multi-dimensional prices and award user credits', () => {
		cy.loginAs(admin);
		cy.visit('/admin/credits?lang=en-US');
		createPriceThroughAdminUi();

		cy.contains('button', 'Credit accounts').click();
		cy.get('input[placeholder="Search by name or email"]').type(user.email);
		cy.contains(user.email).should('be.visible');
		cy.contains('button', 'Adjust').click();
		cy.contains('Credit adjustment').should('be.visible');
		cy.get('input[placeholder="0"]').clear().type('25');
		cy.get('select').last().select('promotion_gift');
		cy.contains('button', 'Adjust credits').click();
		cy.contains('button', 'Confirm').click();
		cy.contains('Credit adjustment').should('not.exist');

		cy.contains('button', 'Credit ledger').click();
		cy.contains('promotion_gift').should('be.visible');
	});

	it('shows the awarded balance and text-to-image quote before a successful generation', () => {
		cy.loginAs(user);
		openUserMenu();
		cy.contains('Credits').parent().should('contain', '25');
		cy.visit('/images?lang=en-US');
		cy.get('textarea[aria-label="Image prompt"]').type('a local E2E image');
		cy.get('[data-credit-quote-status="ready"]')
			.should('contain', 'Estimated credits')
			.and('contain', '5');
		cy.get('button[aria-label="Generate"]').should('be.enabled');
	});

	it('debites credits and records a successful text-to-image usage', () => {
		cy.loginAs(user);
		cy.visit('/images?lang=en-US');
		cy.get('textarea[aria-label="Image prompt"]').type('a successful local E2E image');
		cy.get('[data-credit-quote-status="ready"]').should('be.visible');
		cy.get('button[aria-label="Generate"]').click();
		cy.get('button[aria-label="Preview generated image"]').should('be.visible');
		cy.fakeProviderCalls().its('by_action.text-to-image').should('equal', 1);
		currentBalance(user.token).its('balance').should('equal', 20);
	});

	it('debites credits and records a successful image-to-image usage', () => {
		cy.loginAs(user);
		cy.visit('/images?lang=en-US');
		uploadReferenceImage();
		cy.get('textarea[aria-label="Image prompt"]').type('a local edited E2E image');
		cy.get('[data-credit-quote-status="ready"]').should('be.visible');
		cy.get('button[aria-label="Edit Image"]').click();
		cy.get('button[aria-label="Preview generated image"]').should('be.visible');
		cy.fakeProviderCalls().its('by_action.image-to-image').should('equal', 1);
		currentBalance(user.token).its('balance').should('equal', 15);
	});

	it('keeps the debit and reports failed usage when the provider fails', () => {
		cy.setFakeProviderMode('failure');
		cy.loginAs(user);
		cy.visit('/images?lang=en-US');
		cy.get('textarea[aria-label="Image prompt"]').type('a provider failure image');
		cy.get('[data-credit-quote-status="ready"]').should('be.visible');
		cy.get('button[aria-label="Generate"]').click();
		cy.contains('Image provider request failed').should('be.visible');
		cy.fakeProviderCalls().its('by_action.text-to-image').should('equal', 1);
		currentBalance(user.token).its('balance').should('equal', 10);

		openUserMenu();
		cy.contains('Credits').click();
		cy.contains('Generation failed; credits were charged according to the pricing rule').should(
			'be.visible'
		);
	});

	it('does not call the provider when the user lacks sufficient credits', () => {
		adjustCredits(admin.token, user.id, {
			direction: 'decrease',
			amount: 10,
			reasonCode: 'offline_recharge'
		});
		cy.loginAs(user);
		cy.visit('/images?lang=en-US');
		cy.get('textarea[aria-label="Image prompt"]').type('an unaffordable image');
		cy.get('[data-credit-quote-status="insufficient"]').should('contain', 'Insufficient credits');
		cy.get('button[aria-label="Generate"]').should('be.disabled');
		cy.fakeProviderCalls().its('total').should('equal', 0);
	});

	it('creates an independent positive ledger entry for a manual refund', () => {
		adjustCredits(admin.token, user.id, {
			direction: 'increase',
			amount: 5,
			reasonCode: 'manual_refund'
		});
		cy.loginAs(user);
		openUserMenu();
		cy.contains('Credits').click();
		cy.contains('manual_refund').should('be.visible');
		cy.get('td').contains('+5').should('be.visible');
	});
});
