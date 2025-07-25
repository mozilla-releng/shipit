export const SHIPIT_API_URL = process.env.SHIPIT_API_URL;
export const SHIPIT_PUBLIC_API_URL = process.env.SHIPIT_PUBLIC_API_URL;
export const DEPLOYMENT_BRANCH = process.env.DEPLOYMENT_BRANCH;
export const SENTRY_DSN = process.env.SENTRY_DSN || null;

export default require(`./configs/${DEPLOYMENT_BRANCH}`);
