import Image from "next/image";

type MapPanelProps = {
  title: string;
  description: string;
  imageSrc: string;
};

export default function MapPanel({ title, description, imageSrc }: MapPanelProps) {
  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-950 p-6 shadow-lg">
      <div className="mb-4">
        <h2 className="text-2xl font-semibold text-white">{title}</h2>
        <p className="mt-2 text-sm text-slate-400">{description}</p>
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900">
        <Image
          src={imageSrc}
          alt={title}
          width={1200}
          height={750}
          className="h-auto w-full"
          priority
        />
      </div>
    </section>
  );
}