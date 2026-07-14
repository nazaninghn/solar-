"use client";

import PresentationShell from "@/components/investor-demo/PresentationShell";
import { Scene1Landing, Scene2Login } from "@/components/investor-demo/scenes/ScenesIntro";
import { Scene3Dashboard, Scene4Recommendation } from "@/components/investor-demo/scenes/ScenesDashboard";
import { Scene5Battery, Scene6Forecast, Scene7Market } from "@/components/investor-demo/scenes/ScenesEnergy";
import { Scene8Financial, Scene9Portfolio, Scene10ControlCenter } from "@/components/investor-demo/scenes/ScenesBusiness";
import { Scene11Summary, Scene12CTA } from "@/components/investor-demo/scenes/ScenesClose";

export default function InvestorDemoPage() {
  return (
    <PresentationShell
      renderScene={(id, active) => {
        switch (id) {
          case "landing":
            return <Scene1Landing />;
          case "login":
            return <Scene2Login />;
          case "dashboard":
            return <Scene3Dashboard active={active} />;
          case "recommendation":
            return <Scene4Recommendation active={active} />;
          case "battery":
            return <Scene5Battery active={active} />;
          case "forecast":
            return <Scene6Forecast active={active} />;
          case "market":
            return <Scene7Market />;
          case "financial":
            return <Scene8Financial />;
          case "portfolio":
            return <Scene9Portfolio />;
          case "control-center":
            return <Scene10ControlCenter />;
          case "summary":
            return <Scene11Summary active={active} />;
          case "cta":
            return <Scene12CTA />;
          default:
            return null;
        }
      }}
    />
  );
}
