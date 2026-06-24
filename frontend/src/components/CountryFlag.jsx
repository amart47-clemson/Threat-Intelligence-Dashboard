import { countryName, flagUrl } from '../utils';

export default function CountryFlag({ code }) {
  if (!code || code === '—') return <span>—</span>;

  const url = flagUrl(code);
  const name = countryName(code);

  return (
    <span className="country-cell" title={name}>
      {url && (
        <img
          src={url}
          alt={`${code} flag`}
          width={16}
          height={12}
          className="country-flag"
          loading="lazy"
        />
      )}
      <span>{code}</span>
    </span>
  );
}
