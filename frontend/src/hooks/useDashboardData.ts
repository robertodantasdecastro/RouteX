import { useQuery } from "@tanstack/react-query";
import { adminApi } from "@/lib/api";

export function useDashboardData() {
  const health = useQuery({ queryKey: ["health"], queryFn: adminApi.health });
  const providers = useQuery({ queryKey: ["providers"], queryFn: adminApi.providers });
  const profiles = useQuery({ queryKey: ["profiles"], queryFn: adminApi.profiles });
  const rules = useQuery({ queryKey: ["rules"], queryFn: adminApi.rules });
  const settings = useQuery({ queryKey: ["settings"], queryFn: adminApi.settings });
  const metrics = useQuery({ queryKey: ["metrics"], queryFn: adminApi.metrics });
  const requests = useQuery({ queryKey: ["requests"], queryFn: adminApi.requests });
  const models = useQuery({ queryKey: ["models"], queryFn: adminApi.models });

  return { health, providers, profiles, rules, settings, metrics, requests, models };
}
