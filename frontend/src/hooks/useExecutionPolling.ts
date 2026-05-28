import { useQuery } from "@tanstack/react-query";
import { fetchExecution } from "../api/executions";

export function useExecutionPolling(executionId: string | undefined) {
  return useQuery({
    queryKey: ["execution", executionId],
    queryFn: () => fetchExecution(executionId!),
    enabled: Boolean(executionId),
    refetchIntervalInBackground: true,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "running" || status === "pending" ? 400 : false;
    }
  });
}
