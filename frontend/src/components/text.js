/**
 * Shorten text if it is too long.
 */
export default function maybeShorten(str, length = 70, suffix = ' ...') {
  if (str.length > length) {
    const reduced = str.substring(0, length - suffix.length);

    return `${reduced}${suffix}`;
  }

  return str;
}
