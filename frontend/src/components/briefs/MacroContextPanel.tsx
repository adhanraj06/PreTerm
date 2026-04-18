import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { MacroContext } from "../../types/macro";

function formatValue(value: number | null, units: string) {
  if (value === null) {
    return "N/A";
  }
  const rounded = Math.abs(value) >= 100 ? value.toFixed(1) : value.toFixed(2);
  return units ? `${rounded} ${units}` : rounded;
}

export function MacroContextPanel({ context }: { context: MacroContext }) {
  if (!context.available) {
    return (
      <article className="brief-foot-card macro-context-card">
        <span className="section-kicker">Macro Context</span>
        <div className="empty-state">{context.reason ?? "Macro context is unavailable for this market."}</div>
      </article>
    );
  }

  return (
    <article className="brief-foot-card macro-context-card">
      <div className="panel-heading">
        <div>
          <span className="section-kicker">Macro Context</span>
          <h4>Relevant FRED series</h4>
          {context.macro_source === "fred_csv" ? (
            <small className="macro-source-hint">Using bundled fred.csv (no FRED API key).</small>
          ) : context.macro_source === "fred_api" ? (
            <small className="macro-source-hint">Live FRED API.</small>
          ) : null}
        </div>
        <small>{context.series.length} tracked</small>
      </div>

      <div className="macro-series-stack">
        {context.series.map((series) => (
          <div key={series.series_id} className="macro-series-card">
            <div className="list-card-header">
              <div>
                <strong>{series.title}</strong>
                <small>
                  {series.series_id} · {series.frequency}
                </small>
              </div>
              <div className="macro-series-metric">
                <strong>{formatValue(series.latest_value, series.units)}</strong>
                <small className={series.change !== null && series.change >= 0 ? "delta positive" : "delta negative"}>
                  {series.change !== null ? `${series.change >= 0 ? "+" : ""}${series.change.toFixed(2)}` : "flat"}
                </small>
              </div>
            </div>

            <div className="macro-mini-chart">
              <ResponsiveContainer width="100%" height={92}>
                <LineChart data={series.observations}>
                  <XAxis dataKey="date" hide />
                  <YAxis hide domain={["dataMin", "dataMax"]} />
                  <Tooltip
                    formatter={(value: number) => formatValue(value, series.units)}
                    labelFormatter={(label) => new Date(label).toLocaleDateString()}
                    contentStyle={{
                      background: "#0c1118",
                      border: "1px solid rgba(129, 154, 185, 0.18)",
                      borderRadius: "10px",
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke="#8cb4ff"
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 3, fill: "#d8e5ff" }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        ))}
      </div>
    </article>
  );
}
