import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceDot,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { MarketDetail } from "../../types/market";

type ChartPoint = {
  label: string;
  shortLabel: string;
  probability: number;
};

/** True when the backend sent a modeled path (no live daily candles). */
export function isIllustrativeProbabilityChart(market: MarketDetail): boolean {
  return (
    market.snapshots.length >= 3 &&
    market.snapshots.every(
      (s) => (s.metadata_json as { kind?: string } | null)?.kind === "illustrative_path",
    )
  );
}

export function isKalshiCandleChart(market: MarketDetail): boolean {
  return market.snapshots.some(
    (s) => (s.metadata_json as { kind?: string } | null)?.kind === "kalshi_candle",
  );
}

function buildChartPoints(market: MarketDetail): ChartPoint[] {
  const dayCounts = new Map<string, number>();
  return market.snapshots.map((snapshot) => {
    const d = new Date(snapshot.captured_at);
    const dayKey = d.toDateString();
    const n = (dayCounts.get(dayKey) ?? 0) + 1;
    dayCounts.set(dayKey, n);
    const base = d.toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
    const shortLabel = n > 1 ? `${base} (${n})` : base;
    return {
      label: snapshot.captured_at,
      shortLabel,
      probability: snapshot.price,
    };
  });
}

export function MarketMoveChart({ market }: { market: MarketDetail }) {
  const points: ChartPoint[] = buildChartPoints(market);

  const markers = market.timeline_entries
    .map((entry) => {
      const exactPoint = points.find((point) => point.label === entry.occurred_at);
      let nearestPoint = exactPoint ?? null;

      if (!nearestPoint) {
        const entryTime = new Date(entry.occurred_at).getTime();
        for (let index = points.length - 1; index >= 0; index -= 1) {
          if (new Date(points[index].label).getTime() <= entryTime) {
            nearestPoint = points[index];
            break;
          }
        }
      }

      nearestPoint ??= points[points.length - 1];

      if (!nearestPoint) {
        return null;
      }

      return {
        x: nearestPoint.shortLabel,
        y: entry.price_after_move ?? nearestPoint.probability,
        label: entry.linked_label ?? entry.reason,
      };
    })
    .filter((marker): marker is { x: string; y: number; label: string } => marker !== null);

  if (points.length === 0) {
    return <div className="empty-state">No historical movement is available yet.</div>;
  }

  const chartData = points.map((point) => ({
    ...point,
    probabilityPct: Math.round(point.probability * 100),
  }));

  const pctValues = chartData.map((row) => row.probabilityPct);
  const pctMin = Math.min(...pctValues);
  const pctMax = Math.max(...pctValues);
  const span = Math.max(1, pctMax - pctMin);
  const pad = Math.max(8, span * 0.35);
  const yLow = Math.max(0, pctMin - pad);
  const yHigh = Math.min(100, pctMax + pad);

  return (
    <div className="move-chart-shell">
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={chartData} margin={{ top: 12, right: 8, left: 0, bottom: 8 }}>
          <CartesianGrid stroke="rgba(129, 154, 185, 0.12)" vertical={false} />
          <XAxis
            dataKey="shortLabel"
            tickLine={false}
            axisLine={false}
            tick={{ fill: "#8ea0b7", fontSize: 10 }}
            interval="preserveStartEnd"
            angle={-22}
            textAnchor="end"
            height={52}
          />
          <YAxis
            domain={[yLow, yHigh]}
            tickFormatter={(value: number) => `${value}%`}
            tickLine={false}
            axisLine={false}
            tick={{ fill: "#8ea0b7", fontSize: 11 }}
            width={36}
          />
          <Tooltip
            contentStyle={{
              background: "rgba(8, 13, 21, 0.98)",
              border: "1px solid rgba(129, 154, 185, 0.18)",
              borderRadius: "12px",
              color: "#e8eef6",
            }}
            labelFormatter={(_, payload) => {
              const row = payload?.[0]?.payload as { label?: string } | undefined;
              return row?.label
                ? new Date(row.label).toLocaleString(undefined, {
                    dateStyle: "medium",
                    timeStyle: "short",
                  })
                : "";
            }}
            formatter={(value: number) => [`${value}%`, "Implied yes"]}
          />
          <Line
            type="monotone"
            dataKey="probabilityPct"
            stroke="#7de2d1"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: "#7de2d1", stroke: "#08111a" }}
          />
          {markers.map((marker) => (
            <ReferenceDot
              key={`${marker.x}-${marker.label}`}
              x={marker.x}
              y={Math.round(marker.y * 100)}
              r={4}
              fill="#7dd3fc"
              stroke="#08111a"
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
