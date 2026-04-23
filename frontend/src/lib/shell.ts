import { invoke } from "@tauri-apps/api/core";
import type {
  ShellAppHealth,
  ShellBootstrapStatus,
  ShellLaunchAgentStatus,
  ShellTrayStatus,
} from "@/lib/types";

function shellAvailable() {
  return typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;
}

async function invokeShell<T>(command: string): Promise<T> {
  if (!shellAvailable()) {
    throw new Error("Shell Tauri indisponivel fora da app desktop.");
  }
  return invoke<T>(command);
}

export const shellApi = {
  appHealth: () => invokeShell<ShellAppHealth>("app_health"),
  bootstrapStatus: () => invokeShell<ShellBootstrapStatus>("bootstrap_status"),
  launchAgentStatus: () => invokeShell<ShellLaunchAgentStatus>("launch_agent_status"),
  trayStatus: () => invokeShell<ShellTrayStatus>("tray_status"),
};
