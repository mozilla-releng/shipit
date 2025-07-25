import lazy from './utils/lazy';

const Releases = lazy(
  () => import(/* webpackChunkName: 'Releases' */ './views/Releases'),
);
const NewRelease = lazy(
  () => import(/* webpackChunkName: 'NewRelease' */ './views/NewRelease'),
);
const NewXPIRelease = lazy(
  () => import(/* webpackChunkName: 'NewXPIRelease' */ './views/NewXPIRelease'),
);

export default [
  {
    component: Releases,
    path: '/',
    exact: true,
  },
  {
    component: Releases,
    path: '/recent',
    recent: true,
  },
  {
    component: Releases,
    path: '/recentxpi',
    recent: true,
    xpi: true,
  },
  {
    component: Releases,
    path: '/xpi',
    recent: false,
    xpi: true,
  },
  {
    component: NewRelease,
    path: '/new',
  },
  {
    component: NewXPIRelease,
    path: '/newxpi',
  },
];
