import LiveWindExplorer from "@/components/LiveWindExplorer";
import LiveWindOutlook from "@/components/LiveWindOutlook";

export default function LivePage() {
  return (
    <main className="space-y-8 p-6">
      <LiveWindExplorer />
      <LiveWindOutlook defaultStationId="KMSP" />
    </main>
  );
}