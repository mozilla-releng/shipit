export const repoUrlBuilder = (urlPartial, revision) => {
  if (urlPartial.includes('hg')) {
    return `${urlPartial}/rev/${revision}`;
  }

  return `${urlPartial}/commit/${revision}`;
};

/**
 * Find the branch or repository config entry a release was created from.
 */
export const findProductBranch = (product, release) => {
  const productBranch = product?.branches?.find(
    (item) =>
      item.branch === release.branch && item.project === release.project,
  );

  if (productBranch || !product?.repositories) {
    return productBranch;
  }

  // Products configured with `repositories` (GitHub repos whose branches are
  // fetched dynamically) submit the git branch name as `branch`, so
  // `release.project` (the last path component of the branch) doesn't
  // identify the repository. The API doesn't store the repository, so use
  // the product's only repository, falling back to matching on product name.
  if (product.repositories.length === 1) {
    return product.repositories[0];
  }

  return product.repositories.find((item) => item.project === release.product);
};

/**
 * Treeherder project for a release: the config entry's project if known,
 * otherwise the project derived by the API from the release branch.
 */
export const treeherderProject = (productBranch, release) =>
  productBranch?.project || release.project;

export default { repoUrlBuilder, findProductBranch, treeherderProject };
