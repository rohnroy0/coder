// Backend timestamps are naive UTC (no "Z" suffix). new Date("2026-11-19T10:30:00")
// would parse that as LOCAL time and shift every displayed timestamp by the
// viewer's UTC offset, so always parse through here. Strings that already carry
// a zone ("Z" or "+hh:mm") pass through untouched.
export const parseUtc = (s) => (s ? new Date(/[zZ]|[+-]\d\d:\d\d$/.test(s) ? s : `${s}Z`) : null);

export const fmtDate = (s, opts) =>
  s ? parseUtc(s).toLocaleDateString(undefined, opts) : '—';

export const fmtDateTime = (s, opts) =>
  s ? parseUtc(s).toLocaleString(undefined, opts) : '—';
