export const repoUrlBuilder = (urlPartial, revision) => {
  if (urlPartial.includes('hg')) {
    return `${urlPartial}/rev/${revision}`;
  }

  return `${urlPartial}/commit/${revision}`;
};

export default { repoUrlBuilder };
