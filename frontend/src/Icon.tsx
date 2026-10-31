export function Icon({ name }: { name: "search" | "pin" | "heart" }) {
  if (name === "pin") return <svg aria-hidden="true" viewBox="0 0 24 24" className="icon"><path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 1 1 14 0Z" /><circle cx="12" cy="10" r="2.25" /></svg>;
  if (name === "heart") return <svg aria-hidden="true" viewBox="0 0 24 24" className="icon"><path d="M20.8 8.8c0 5.4-8.8 10.2-8.8 10.2S3.2 14.2 3.2 8.8A4.6 4.6 0 0 1 12 6.3a4.6 4.6 0 0 1 8.8 2.5Z" /></svg>;
  return <svg aria-hidden="true" viewBox="0 0 24 24" className="icon"><circle cx="11" cy="11" r="6.5" /><path d="m16 16 4.5 4.5" /></svg>;
}
