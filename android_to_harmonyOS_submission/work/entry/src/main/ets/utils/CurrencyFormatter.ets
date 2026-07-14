import { i18n } from '@kit.LocalizationKit';

function localeOrFallback(localeTag: string): Intl.Locale {
  try {
    return new Intl.Locale(localeTag);
  } catch {
    try {
      return i18n.System.getSystemLocaleInstance();
    } catch {
      return new Intl.Locale('en-US');
    }
  }
}

function isAsciiLowercaseCurrencyCode(candidate: string): boolean {
  if (candidate.length !== 3) {
    return false;
  }
  const first: number = candidate.charCodeAt(0);
  const second: number = candidate.charCodeAt(1);
  const third: number = candidate.charCodeAt(2);
  return first >= 97 && first <= 122 &&
    second >= 97 && second <= 122 &&
    third >= 97 && third <= 122;
}

function currencyOverride(localeTag: string): string | undefined {
  const parts: string[] = localeTag.toLowerCase().split('-');
  const unicodeIndex: number = parts.indexOf('u');
  if (unicodeIndex < 0) {
    return undefined;
  }
  const unicodeParts: string[] = parts.slice(unicodeIndex + 1);
  const nextExtensionIndex: number = unicodeParts.findIndex(
    (part: string): boolean => part.length === 1
  );
  const extensionParts: string[] = nextExtensionIndex < 0 ?
    unicodeParts : unicodeParts.slice(0, nextExtensionIndex);
  const currencyIndex: number = extensionParts.indexOf('cu');
  if (currencyIndex < 0 || currencyIndex >= extensionParts.length - 1) {
    return undefined;
  }
  const candidate: string = extensionParts[currencyIndex + 1];
  if (isAsciiLowercaseCurrencyCode(candidate)) {
    return candidate.toUpperCase();
  }
  return undefined;
}

function currencyForRegion(region: string): string {
  switch (region.toUpperCase()) {
    case 'AE':
      return 'AED';
    case 'AF':
      return 'AFN';
    case 'AL':
      return 'ALL';
    case 'AM':
      return 'AMD';
    case 'AO':
      return 'AOA';
    case 'AR':
      return 'ARS';
    case 'AU':
    case 'CC':
    case 'CX':
    case 'HM':
    case 'KI':
    case 'NF':
    case 'NR':
    case 'TV':
      return 'AUD';
    case 'AW':
      return 'AWG';
    case 'AZ':
      return 'AZN';
    case 'BA':
      return 'BAM';
    case 'BB':
      return 'BBD';
    case 'BD':
      return 'BDT';
    case 'BH':
      return 'BHD';
    case 'BI':
      return 'BIF';
    case 'BM':
      return 'BMD';
    case 'BN':
      return 'BND';
    case 'BO':
      return 'BOB';
    case 'BR':
      return 'BRL';
    case 'BS':
      return 'BSD';
    case 'BT':
      return 'BTN';
    case 'BW':
      return 'BWP';
    case 'BY':
      return 'BYN';
    case 'BZ':
      return 'BZD';
    case 'CA':
      return 'CAD';
    case 'CD':
      return 'CDF';
    case 'CH':
    case 'LI':
      return 'CHF';
    case 'CL':
      return 'CLP';
    case 'CN':
      return 'CNY';
    case 'CO':
      return 'COP';
    case 'CR':
      return 'CRC';
    case 'CU':
      return 'CUP';
    case 'CV':
      return 'CVE';
    case 'CZ':
      return 'CZK';
    case 'DJ':
      return 'DJF';
    case 'DK':
    case 'FO':
    case 'GL':
      return 'DKK';
    case 'DO':
      return 'DOP';
    case 'DZ':
      return 'DZD';
    case 'EG':
      return 'EGP';
    case 'ER':
      return 'ERN';
    case 'ET':
      return 'ETB';
    case 'AD':
    case 'AT':
    case 'AX':
    case 'BE':
    case 'BG':
    case 'BL':
    case 'CY':
    case 'DE':
    case 'EA':
    case 'EE':
    case 'ES':
    case 'FI':
    case 'FR':
    case 'GF':
    case 'GP':
    case 'GR':
    case 'HR':
    case 'IC':
    case 'IE':
    case 'IT':
    case 'LT':
    case 'LU':
    case 'LV':
    case 'MC':
    case 'ME':
    case 'MF':
    case 'MQ':
    case 'MT':
    case 'NL':
    case 'PM':
    case 'PT':
    case 'RE':
    case 'SI':
    case 'SK':
    case 'SM':
    case 'TF':
    case 'VA':
    case 'XK':
    case 'YT':
      return 'EUR';
    case 'FJ':
      return 'FJD';
    case 'FK':
      return 'FKP';
    case 'GB':
    case 'GG':
    case 'GS':
    case 'IM':
    case 'JE':
    case 'TA':
      return 'GBP';
    case 'GE':
      return 'GEL';
    case 'GH':
      return 'GHS';
    case 'GI':
      return 'GIP';
    case 'GM':
      return 'GMD';
    case 'GN':
      return 'GNF';
    case 'GT':
      return 'GTQ';
    case 'GY':
      return 'GYD';
    case 'HK':
      return 'HKD';
    case 'HN':
      return 'HNL';
    case 'HT':
      return 'HTG';
    case 'HU':
      return 'HUF';
    case 'ID':
      return 'IDR';
    case 'IL':
    case 'PS':
      return 'ILS';
    case 'IN':
      return 'INR';
    case 'IQ':
      return 'IQD';
    case 'IR':
      return 'IRR';
    case 'IS':
      return 'ISK';
    case 'JM':
      return 'JMD';
    case 'JO':
      return 'JOD';
    case 'JP':
      return 'JPY';
    case 'KE':
      return 'KES';
    case 'KG':
      return 'KGS';
    case 'KH':
      return 'KHR';
    case 'KM':
      return 'KMF';
    case 'KP':
      return 'KPW';
    case 'KR':
      return 'KRW';
    case 'KW':
      return 'KWD';
    case 'KY':
      return 'KYD';
    case 'KZ':
      return 'KZT';
    case 'LA':
      return 'LAK';
    case 'LB':
      return 'LBP';
    case 'LK':
      return 'LKR';
    case 'LR':
      return 'LRD';
    case 'LS':
      return 'LSL';
    case 'LY':
      return 'LYD';
    case 'EH':
    case 'MA':
      return 'MAD';
    case 'MD':
      return 'MDL';
    case 'MG':
      return 'MGA';
    case 'MK':
      return 'MKD';
    case 'MM':
      return 'MMK';
    case 'MN':
      return 'MNT';
    case 'MO':
      return 'MOP';
    case 'MR':
      return 'MRU';
    case 'MU':
      return 'MUR';
    case 'MV':
      return 'MVR';
    case 'MW':
      return 'MWK';
    case 'MX':
      return 'MXN';
    case 'MY':
      return 'MYR';
    case 'MZ':
      return 'MZN';
    case 'NA':
      return 'NAD';
    case 'NG':
      return 'NGN';
    case 'NI':
      return 'NIO';
    case 'BV':
    case 'NO':
    case 'SJ':
      return 'NOK';
    case 'NP':
      return 'NPR';
    case 'CK':
    case 'NU':
    case 'NZ':
    case 'PN':
    case 'TK':
      return 'NZD';
    case 'OM':
      return 'OMR';
    case 'PA':
      return 'PAB';
    case 'PE':
      return 'PEN';
    case 'PG':
      return 'PGK';
    case 'PH':
      return 'PHP';
    case 'PK':
      return 'PKR';
    case 'PL':
      return 'PLN';
    case 'PY':
      return 'PYG';
    case 'QA':
      return 'QAR';
    case 'RO':
      return 'RON';
    case 'RS':
      return 'RSD';
    case 'RU':
      return 'RUB';
    case 'RW':
      return 'RWF';
    case 'SA':
      return 'SAR';
    case 'SB':
      return 'SBD';
    case 'SC':
      return 'SCR';
    case 'SD':
      return 'SDG';
    case 'SE':
      return 'SEK';
    case 'SG':
      return 'SGD';
    case 'AC':
    case 'SH':
      return 'SHP';
    case 'SL':
      return 'SLE';
    case 'SO':
      return 'SOS';
    case 'SR':
      return 'SRD';
    case 'SS':
      return 'SSP';
    case 'ST':
      return 'STN';
    case 'SV':
      return 'SVC';
    case 'SY':
      return 'SYP';
    case 'SZ':
      return 'SZL';
    case 'TH':
      return 'THB';
    case 'TJ':
      return 'TJS';
    case 'TM':
      return 'TMT';
    case 'TN':
      return 'TND';
    case 'TO':
      return 'TOP';
    case 'TR':
      return 'TRY';
    case 'TT':
      return 'TTD';
    case 'TW':
      return 'TWD';
    case 'TZ':
      return 'TZS';
    case 'UA':
      return 'UAH';
    case 'UG':
      return 'UGX';
    case 'AS':
    case 'BQ':
    case 'DG':
    case 'EC':
    case 'FM':
    case 'GU':
    case 'IO':
    case 'MH':
    case 'MP':
    case 'PR':
    case 'PW':
    case 'TC':
    case 'TL':
    case 'UM':
    case 'US':
    case 'VG':
    case 'VI':
      return 'USD';
    case 'UY':
      return 'UYU';
    case 'UZ':
      return 'UZS';
    case 'VE':
      return 'VES';
    case 'VN':
      return 'VND';
    case 'VU':
      return 'VUV';
    case 'WS':
      return 'WST';
    case 'CF':
    case 'CG':
    case 'CM':
    case 'GA':
    case 'GQ':
    case 'TD':
      return 'XAF';
    case 'AG':
    case 'AI':
    case 'DM':
    case 'GD':
    case 'KN':
    case 'LC':
    case 'MS':
    case 'VC':
      return 'XCD';
    case 'CW':
    case 'SX':
      return 'XCG';
    case 'BF':
    case 'BJ':
    case 'CI':
    case 'GW':
    case 'ML':
    case 'NE':
    case 'SN':
    case 'TG':
      return 'XOF';
    case 'NC':
    case 'PF':
    case 'WF':
      return 'XPF';
    case 'AQ':
    case 'CP':
      return 'XXX';
    case 'YE':
      return 'YER';
    case 'ZA':
      return 'ZAR';
    case 'ZM':
      return 'ZMW';
    case 'ZW':
      return 'ZWG';
    default:
      return 'XXX';
  }
}

export function formatPriceForLocale(priceCents: number, localeTag: string): string {
  const locale: Intl.Locale = localeOrFallback(localeTag);
  const canonicalTag: string = locale.toString();
  let region: string = locale.region ?? '';
  if (region.length === 0) {
    region = locale.maximize().region ?? '';
  }
  const currency: string = currencyOverride(canonicalTag) ?? currencyForRegion(region);
  try {
    return new Intl.NumberFormat(canonicalTag, {
      style: 'currency',
      currency: currency
    }).format(priceCents / 100);
  } catch {
    return new Intl.NumberFormat(canonicalTag, {
      style: 'currency',
      currency: 'XXX'
    }).format(priceCents / 100);
  }
}

export function formatPrice(priceCents: number): string {
  return formatPriceForLocale(
    priceCents,
    i18n.System.getSystemLocaleInstance().toString()
  );
}
