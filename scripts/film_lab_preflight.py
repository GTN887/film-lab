"""Run Film Lab's no-render runtime readiness check from the project root."""
from film_lab.runtime_preflight import run_preflight

if __name__ == "__main__":
    report = run_preflight()
    print(report.summary())
    raise SystemExit(0 if report.ready else 2)
