"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "Overview" },
  { href: "/live", label: "Live" },
  { href: "/pipeline", label: "Pipeline" },
  { href: "/results", label: "Results" },
  { href: "/forecasting", label: "Forecasting" },
  { href: "/benchmarking", label: "Benchmarking" },
];

export default function Navbar() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 border-b border-slate-800 bg-slate-950/90 backdrop-blur">
      <nav className="mx-auto flex max-w-7xl flex-col gap-4 px-6 py-4 md:flex-row md:items-center md:justify-between">
        <Link href="/" className="group">
          <div className="text-lg font-bold text-white">
            Wind Energy Forecasting
          </div>
          <div className="text-xs text-slate-400">
            Spark · NOAA · ML · Live Analysis
          </div>
        </Link>

        <div className="flex flex-wrap gap-2">
          {navItems.map((item) => {
            const active =
              item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={[
                  "rounded-full px-4 py-2 text-sm font-medium transition",
                  active
                    ? "bg-cyan-400 text-slate-950"
                    : "text-slate-300 hover:bg-slate-800 hover:text-white",
                ].join(" ")}
              >
                {item.label}
              </Link>
            );
          })}
        </div>
      </nav>
    </header>
  );
}
