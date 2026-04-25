import { Nav } from "@/components/landing/Nav";
import { LandingHero } from "@/components/landing/LandingHero";

export default function HomePage() {
  return (
    <main className="b-frame max-w-[920px] mx-auto my-6">
      <Nav active="research" />
      <LandingHero />
    </main>
  );
}
