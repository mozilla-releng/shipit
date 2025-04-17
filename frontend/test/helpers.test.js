import { repoUrlBuilder } from '../src/utils/helpers';

describe('repoUrlBuilder helper', () => {
  test('should return the correct url format for hg.mozilla.org projects', () => {
    const productBranch = {
      repo: 'https://hg.mozilla.org/try',
    };
    const release = {
      revision: 'c045b4d696bc96829cd19ddafee7776a8c5092fe',
    };
    const url =
      'https://hg.mozilla.org/try/rev/c045b4d696bc96829cd19ddafee7776a8c5092fe';

    expect(repoUrlBuilder(productBranch.repo, release.revision)).toMatch(url);
  });

  test('should return the correct url format for github.com projects', () => {
    const productBranch = {
      repo: 'https://github.com/mozilla-releng/staging-application-services',
    };
    const release = {
      revision: '23de0da019848861272eb2414a7787eea3314153',
    };
    const url =
      'https://github.com/mozilla-releng/staging-application-services/commit/23de0da019848861272eb2414a7787eea3314153';

    expect(repoUrlBuilder(productBranch.repo, release.revision)).toMatch(url);
  });

  test('should return the correct url format for github.com/mozilla-extension projects', () => {
    const owner = 'mozilla-extensions';
    const repo = 'balrog-dryrun';
    const urlPartial = `https://github.com/${owner}/${repo}`;
    const release = {
      xpi_revision: 'd311b29cc241b139fc8da2206c8eebd422d4cd3a',
    };
    const url =
      'https://github.com/mozilla-extensions/balrog-dryrun/commit/d311b29cc241b139fc8da2206c8eebd422d4cd3a';

    expect(repoUrlBuilder(urlPartial, release.xpi_revision)).toMatch(url);
  });
});
