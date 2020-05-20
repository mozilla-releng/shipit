/* eslint-disable prefer-destructuring */
export const SHIPIT_API_URL = process.env.SHIPIT_API_URL;
export const SHIPIT_PUBLIC_API_URL = process.env.SHIPIT_PUBLIC_API_URL;
export const TASKCLUSTER_ROOT_URL = process.env.FRONTEND_TASKCLUSTER_ROOT_URL;
export const RELEASE_CHANNEL = process.env.RELEASE_CHANNEL;
export const SENTRY_DSN = process.env.SENTRY_DSN || null;
export default require(`./configs/${RELEASE_CHANNEL}`); // eslint-disable-line import/no-dynamic-require, global-require
