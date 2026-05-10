type Props = {
  label: string;
  value: string;
  helper?: string;
};

export default function MetricCard({ label, value, helper }: Props) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5 shadow-lg">
      <p className="text-sm text-slate-400">{label}</p>

      <p className="mt-2 text-2xl font-bold text-white">{value}</p>

      {helper ? (
        <p className="mt-2 text-xs leading-5 text-slate-500">{helper}</p>
      ) : null}
    </div>
  );
}