import devConfig from '../src/configs/dev';
import { findProductBranch, treeherderProject } from '../src/utils/helpers';

const hgProduct = {
  product: 'firefox',
  branches: [
    {
      branch: 'releases/mozilla-beta',
      project: 'mozilla-beta',
      repo: 'https://hg.mozilla.org/releases/mozilla-beta',
    },
    {
      branch: 'releases/mozilla-release',
      project: 'mozilla-release',
      repo: 'https://hg.mozilla.org/releases/mozilla-release',
    },
  ],
};

const githubProduct = {
  product: 'focus-ios',
  repositories: [
    {
      project: 'firefox-ios',
      repo: 'https://github.com/mozilla-mobile/firefox-ios',
    },
  ],
};

// The API sets `project` to the last path component of `branch`.
const release = (product, branch) => ({
  product,
  branch,
  project: branch.split('/').pop(),
});

describe('findProductBranch', () => {
  test('matches hg branches on branch and project', () => {
    const r = release('firefox', 'releases/mozilla-release');

    expect(findProductBranch(hgProduct, r)).toBe(hgProduct.branches[1]);
    expect(treeherderProject(findProductBranch(hgProduct, r), r)).toBe(
      'mozilla-release',
    );
  });

  test('uses the only repository for github products', () => {
    const r = release('focus-ios', 'someone/feature-branch');
    const productBranch = findProductBranch(githubProduct, r);

    expect(productBranch).toBe(githubProduct.repositories[0]);
    expect(treeherderProject(productBranch, r)).toBe('firefox-ios');
  });

  test('matches on product name when there are several repositories', () => {
    const product = {
      product: 'app-services',
      repositories: [
        { project: 'other', repo: 'https://github.com/mozilla/other' },
        {
          project: 'app-services',
          repo: 'https://github.com/mozilla/application-services',
        },
      ],
    };

    expect(findProductBranch(product, release('app-services', 'main'))).toBe(
      product.repositories[1],
    );
  });

  test('falls back to the release project when nothing matches', () => {
    const r = release('firefox', 'projects/maple');
    const productBranch = findProductBranch(hgProduct, r);

    expect(productBranch).toBeUndefined();
    expect(treeherderProject(productBranch, r)).toBe('maple');
    expect(findProductBranch(undefined, r)).toBeUndefined();
  });
});

describe('dev config', () => {
  test.each(['firefox-ios', 'focus-ios'])(
    '%s releases link to staging-firefox-ios',
    (productName) => {
      const product = devConfig.PRODUCTS.firefox.find(
        (p) => p.product === productName,
      );
      const r = release(productName, 'someone/feature-branch');

      expect(treeherderProject(findProductBranch(product, r), r)).toBe(
        'staging-firefox-ios',
      );
    },
  );
});
