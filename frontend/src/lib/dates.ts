/** The one place that turns API dates into text (HANDOFF section 9). */

/**
 * A date-only value ("2026-11-12") on its own calendar day.
 *
 * Not `new Date("2026-11-12")`: that is UTC midnight, which is still 11 Nov in the Americas.
 */
export function formatDate(isoDate: string, locale?: string): string {
  const [year, month, day] = isoDate.split("-").map(Number);
  const local = new Date(year ?? 0, (month ?? 1) - 1, day ?? 1);
  return new Intl.DateTimeFormat(locale, { dateStyle: "medium" }).format(local);
}

/** An instant (a timestamp with a zone) in the user's time zone. */
export function formatDateTime(isoDateTime: string, locale?: string): string {
  return new Intl.DateTimeFormat(locale, { dateStyle: "medium", timeStyle: "short" }).format(
    new Date(isoDateTime),
  );
}

/** Today's local date as "YYYY-MM-DD", the format of date inputs and of the API. */
export function todayIso(now: Date = new Date()): string {
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${String(now.getFullYear())}-${month}-${day}`;
}
