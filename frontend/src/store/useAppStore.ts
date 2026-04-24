import { startTransition } from "react";
import { create } from "zustand";
import type { ProjectTokenResponse, RouteSection } from "@/lib/types";

type AppState = {
  activeModelAlias: string | null;
  activeProviderHint: string | null;
  currentSection: RouteSection;
  generatedProjectToken: ProjectTokenResponse | null;
  setActiveModelAlias: (modelAlias: string | null) => void;
  setActiveProviderHint: (providerId: string | null) => void;
  setCurrentSection: (section: RouteSection) => void;
  setGeneratedProjectToken: (token: ProjectTokenResponse | null) => void;
};

export const useAppStore = create<AppState>((set) => ({
  activeModelAlias: null,
  activeProviderHint: null,
  currentSection: "overview",
  generatedProjectToken: null,
  setActiveModelAlias: (activeModelAlias) => set({ activeModelAlias }),
  setActiveProviderHint: (activeProviderHint) => set({ activeProviderHint }),
  setCurrentSection: (section) => {
    startTransition(() => {
      set({ currentSection: section });
    });
  },
  setGeneratedProjectToken: (generatedProjectToken) => set({ generatedProjectToken }),
}));
