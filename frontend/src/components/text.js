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

export function phasePrettyName(name) {
  if (name === 'promote_firefox_rc') {
    return 'Promote RC';
  }

  if (name === 'ship_firefox_rc') {
    return 'Ship RC';
  }

  if (name === 'ship_fennec_rc') {
    return 'Ship RC';
  }

  if (name === 'ship_fennec_release_rc') {
    return 'Ship Release to RC';
  }

  if (name === 'ship_fennec_release') {
    return 'Ship Fennec to Release';
  }

  const firstTerm = name.split('_')[0];

  return firstTerm.charAt(0).toUpperCase() + firstTerm.slice(1);
}
