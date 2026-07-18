import { defineConfig } from 'cypress';

export default defineConfig({
	e2e: {
		baseUrl: process.env.CYPRESS_BASE_URL,
		specPattern: 'tests/e2e/**/*.cy.ts',
		supportFile: 'tests/e2e/credits/support.ts'
	}
});
