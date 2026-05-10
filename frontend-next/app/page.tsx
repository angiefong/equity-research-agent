import { Nav } from "@/components/landing/Nav";
import { LandingHero } from "@/components/landing/LandingHero";
import { RecentMemos } from "@/components/landing/RecentMemos";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { api } from "@/lib/api";

export default async function HomePage() {
  let runs: Awaited<ReturnType<typeof api.recentRuns>> = [];
  try {
    runs = await api.recentRuns(3);
  } catch {
    runs = [];
  }
  return (
    <main className="b-frame max-w-[920px] mx-auto my-6">
      <Nav active="research" />
      <LandingHero />
      <RecentMemos runs={runs} />
      <HowItWorks />
    </main>
  );
}
