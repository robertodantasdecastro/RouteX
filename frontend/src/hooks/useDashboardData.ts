import { useQuery } from "@tanstack/react-query";
import { adminApi } from "@/lib/api";

export function useDashboardData() {
  const health = useQuery({
    queryKey: ["health"],
    queryFn: adminApi.health,
    retry: 1,
    refetchInterval: 5_000,
    refetchOnMount: "always",
    refetchOnWindowFocus: true,
  });
  const runtimeReady = Boolean(health.data);
  const providers = useQuery({
    queryKey: ["providers"],
    queryFn: adminApi.providers,
    enabled: runtimeReady,
    retry: 1,
    refetchInterval: 10_000,
  });
  const profiles = useQuery({
    queryKey: ["profiles"],
    queryFn: adminApi.profiles,
    enabled: runtimeReady,
    retry: 1,
    refetchInterval: 10_000,
  });
  const rules = useQuery({
    queryKey: ["rules"],
    queryFn: adminApi.rules,
    enabled: runtimeReady,
    retry: 1,
    refetchInterval: 10_000,
  });
  const settings = useQuery({
    queryKey: ["settings"],
    queryFn: adminApi.settings,
    enabled: runtimeReady,
    retry: 1,
    refetchInterval: 10_000,
  });
  const metrics = useQuery({
    queryKey: ["metrics"],
    queryFn: adminApi.metrics,
    enabled: runtimeReady,
    retry: 1,
    refetchInterval: 5_000,
  });
  const requests = useQuery({
    queryKey: ["requests"],
    queryFn: adminApi.requests,
    enabled: runtimeReady,
    retry: 1,
    refetchInterval: 5_000,
  });
  const models = useQuery({
    queryKey: ["models"],
    queryFn: adminApi.models,
    enabled: runtimeReady,
    retry: 1,
    refetchInterval: 10_000,
  });

  return { health, providers, profiles, rules, settings, metrics, requests, models };
}
