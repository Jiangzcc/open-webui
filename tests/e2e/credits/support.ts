/// <reference types="cypress" />

export {};

type SessionUser = {
	id: string;
	email: string;
	name: string;
	role: 'admin' | 'user';
	token: string;
};

type CreditPrice = {
	id: string;
	service_type: string;
	resource_id: string;
	action: string;
};

type ProviderCalls = {
	mode: 'success' | 'failure';
	total: number;
	by_action: Partial<Record<'text-to-image' | 'image-to-image', number>>;
};

const API_URL = Cypress.env('API_URL') || 'http://127.0.0.1:8080';
const PROVIDER_URL = Cypress.env('PROVIDER_URL') || 'http://127.0.0.1:18080';
const RUN_ID = Cypress.env('CREDITS_E2E_RUN_ID') || `${Date.now()}`;
const ADMIN = {
	name: 'Credits E2E Admin',
	email: `credits-e2e-admin-${RUN_ID}@example.test`,
	password: 'CreditsE2E-admin-123!'
};
const USER = {
	name: 'Credits E2E User',
	email: `credits-e2e-user-${RUN_ID}@example.test`,
	password: 'CreditsE2E-user-123!'
};

const authHeaders = (token: string) => ({ Authorization: `Bearer ${token}` });

const requestJson = <T>(options: Partial<Cypress.RequestOptions>) =>
	cy.request<T>({
		...options,
		failOnStatusCode: false
	} as Cypress.RequestOptions);

const expectSuccessful = <T>(response: Cypress.Response<T>) => {
	expect(response.status, JSON.stringify(response.body)).to.be.within(200, 299);
	return response.body;
};

type SignupAccount = {
	name: string;
	email: string;
	password: string;
};

const signup = (account: SignupAccount) =>
	requestJson<SessionUser>({
		method: 'POST',
		url: `${API_URL}/api/v1/auths/signup`,
		body: account
	}).then((response) => {
		if (response.status === 400 && JSON.stringify(response.body).includes('already registered')) {
			return signin(account);
		}
		return expectSuccessful(response);
	}) as Cypress.Chainable<SessionUser>;

const signin = (account: SignupAccount) =>
	requestJson<SessionUser>({
		method: 'POST',
		url: `${API_URL}/api/v1/auths/signin`,
		body: { email: account.email, password: account.password }
	}).then(expectSuccessful);

const listCreditPrices = (admin: SessionUser) =>
	requestJson<CreditPrice[]>({
		method: 'GET',
		url: `${API_URL}/api/v1/credits/admin/prices`,
		headers: authHeaders(admin.token)
	}).then(expectSuccessful);

const TEST_PRICE_RESOURCE_IDS = new Set(['dall-e-2', 'ui-multidimensional-e2e']);

const removeExistingPrices = (admin: SessionUser) =>
	listCreditPrices(admin).then((prices) =>
		cy
			.wrap(
				prices.filter(
					(price) =>
						price.service_type === 'image' &&
						TEST_PRICE_RESOURCE_IDS.has(price.resource_id) &&
						price.action === 'text-to-image'
				)
			)
			.each((price) =>
				requestJson({
					method: 'DELETE',
					url: `${API_URL}/api/v1/credits/admin/prices/${encodeURIComponent((price as unknown as CreditPrice).id)}`,
					headers: authHeaders(admin.token)
				}).then(expectSuccessful)
			)
	);

const disableSignup = (admin: SessionUser) =>
	requestJson({
		method: 'POST',
		url: `${API_URL}/api/v1/configs/import`,
		headers: authHeaders(admin.token),
		body: { config: { 'ui.enable_signup': false } }
	}).then(expectSuccessful);

const enableSignup = (admin: SessionUser) =>
	requestJson({
		method: 'POST',
		url: `${API_URL}/api/v1/configs/import`,
		headers: authHeaders(admin.token),
		body: { config: { 'ui.enable_signup': true } }
	}).then(expectSuccessful);

const createUser = (admin: SessionUser) =>
	enableSignup(admin)
		.then(() => signup(USER))
		.then((user) => {
			if (user.role === 'user') return user;
			return requestJson({
				method: 'POST',
				url: `${API_URL}/api/v1/users/${encodeURIComponent(user.id)}/update`,
				headers: authHeaders(admin.token),
				body: { role: 'user' }
			}).then(() => signin(USER));
		})
		.then((user) => disableSignup(admin).then(() => user));

const login = (user: SessionUser) => {
	cy.visit('/?lang=en-US', {
		onBeforeLoad(window) {
			window.localStorage.setItem('token', user.token);
			window.localStorage.setItem('locale', 'en-US');
		}
	});
};

const provider = {
	reset: () =>
		requestJson<ProviderCalls>({ method: 'POST', url: `${PROVIDER_URL}/__reset` }).then(
			expectSuccessful
		),
	setMode: (mode: ProviderCalls['mode']) =>
		requestJson<ProviderCalls>({
			method: 'POST',
			url: `${PROVIDER_URL}/__mode`,
			body: { mode }
		}).then(expectSuccessful),
	calls: () =>
		requestJson<ProviderCalls>({ method: 'GET', url: `${PROVIDER_URL}/__calls` }).then(
			expectSuccessful
		)
};

declare global {
	namespace Cypress {
		interface SessionUser {
			id: string;
			email: string;
			name: string;
			role: 'admin' | 'user';
			token: string;
		}

		interface ProviderCalls {
			mode: 'success' | 'failure';
			total: number;
			by_action: Partial<Record<'text-to-image' | 'image-to-image', number>>;
		}

		interface Chainable {
			creditsAdmin(): Chainable<SessionUser>;
			creditsUser(): Chainable<SessionUser>;
			loginAs(user: SessionUser): Chainable<void>;
			resetFakeProvider(): Chainable<ProviderCalls>;
			setFakeProviderMode(mode: ProviderCalls['mode']): Chainable<ProviderCalls>;
			fakeProviderCalls(): Chainable<ProviderCalls>;
		}
	}
}

Cypress.Commands.add('creditsAdmin', () => signup(ADMIN) as Cypress.Chainable<SessionUser>);
Cypress.Commands.add(
	'creditsUser',
	() =>
		cy
			.creditsAdmin()
			.then((admin) =>
				removeExistingPrices(admin).then(() => createUser(admin))
			) as Cypress.Chainable<SessionUser>
);
Cypress.Commands.add('loginAs', (user) => cy.then(() => login(user)) as Cypress.Chainable<void>);
Cypress.Commands.add('resetFakeProvider', () => provider.reset());
Cypress.Commands.add('setFakeProviderMode', (mode) => provider.setMode(mode));
Cypress.Commands.add('fakeProviderCalls', () => provider.calls());
