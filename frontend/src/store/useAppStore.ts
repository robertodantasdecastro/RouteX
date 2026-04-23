import { startTransition } from "react";
import { create } from "zustand";
import type { ProjectTokenResponse, RouteSection } from "@/lib/types";

type AppState = {
  currentSection: RouteSection;
  generatedProjectToken: ProjectTokenResponse | null;
  setCurrentSection: (section: RouteSection) => void;
  setGeneratedProjectToken: (token: ProjectTokenResponse | null) => void;
};

export const useAppStore = create<AppState>((set) => ({
  currentSection: "overview",
  generatedProjectToken: null,
  setCurrentSection: (section) => {
    startTransition(() => {
      set({ currentSection: section });
    });
  },
  setGeneratedProjectToken: (generatedProjectToken) => set({ generatedProjectToken }),
}));
