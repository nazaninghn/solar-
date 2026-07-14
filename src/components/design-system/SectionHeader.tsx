export default function SectionHeader({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description: string;
}) {
  return (
    <div className="mb-8 max-w-2xl">
      <p className="text-xs font-semibold text-lime-dark uppercase tracking-widest mb-2">{eyebrow}</p>
      <h2 className="text-2xl sm:text-3xl font-bold text-ink tracking-tight">{title}</h2>
      <p className="mt-2 text-sm text-gray-500 leading-relaxed">{description}</p>
    </div>
  );
}
