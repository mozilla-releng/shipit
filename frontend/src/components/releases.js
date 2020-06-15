// Poor man's RC detection. xx.0 is the only pattern that matches RC
export default function isRc(version) {
  const parts = version.split('.');

  if (parts.length !== 2) {
    return false;
  }

  if (parts[1] !== '0') {
    return false;
  }

  return true;
}
