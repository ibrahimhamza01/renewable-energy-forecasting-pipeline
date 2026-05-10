import LiveWindExplorer from "@/components/LiveWindExplorer";
import LiveWindOutlook from "@/components/LiveWindOutlook";

export default function LivePage() {
  return (
    <main className="mx-auto w-full max-w-7xl px-6 py-10">
      <section className="rounded-3xl border border-slate-800 bg-slate-900 p-8">
        <p className="text-sm font-semibold uppercase tracking-wide text-cyan-300">
          Live NOAA Analysis
        </p>

        <h1 className="mt-3 text-4xl font-bold text-white">
          Live wind outlook explorer
        </h1>

        <p className="mt-4 max-w-3xl text-slate-300">
          Explore real-time NOAA/NWS observations, turbine-inspired wind
          capacity-factor estimation, and deployable backend outlook analysis
          powered by preserved Spark pipeline artifacts.
        </p>
      </section>

      <section className="mt-8">
        <LiveWindExplorer />
      </section>

      <section className="mt-8">
        <LiveWindOutlook defaultStationId="KMSP" />
      </section>

      <section className="mt-8 grid gap-5 md:grid-cols-3">
        <InfoCard
          title="Live NOAA observations"
          text="Current wind speed, wind direction, temperature, and observation timestamps are fetched directly from the NOAA/NWS API."
        />

        <InfoCard
          title="Power-curve estimation"
          text="Wind speed is converted into estimated wind potential using turbine-inspired cut-in, rated, and cut-out operating regions."
        />

        <InfoCard
          title="Portable backend analysis"
          text="The backend combines live observations with preserved Spark-generated artifacts for historical contextualization and short-term outlook estimation."
        />
      </section>
    </main>
  );
}

function InfoCard({
  title,
  text,
}: {
  title: string;
  text: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
      <h2 className="text-xl font-semibold text-white">{title}</h2>

      <p className="mt-3 text-sm leading-7 text-slate-400">{text}</p>
    </div>
  );
}