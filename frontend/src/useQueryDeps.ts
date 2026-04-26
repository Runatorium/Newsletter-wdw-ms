import { useEffect, useState, type DependencyList } from "react";

export type LoadState<T> = { data: T | null; err: string | null; loading: boolean };

export function useQueryDeps<T>(
  factory: () => Promise<T>,
  deps: DependencyList,
): LoadState<T> {
  const [s, setS] = useState<LoadState<T>>({
    data: null,
    err: null,
    loading: true,
  });
  useEffect(() => {
    let on = true;
    setS((prev) => ({ ...prev, loading: true, err: null }));
    factory()
      .then((d) => on && setS({ data: d, err: null, loading: false }))
      .catch(
        (e) =>
          on &&
          setS({
            data: null,
            err: (e as Error).message ?? String(e),
            loading: false,
          }),
      );
    return () => {
      on = false;
    };
  }, deps);
  return s;
}
