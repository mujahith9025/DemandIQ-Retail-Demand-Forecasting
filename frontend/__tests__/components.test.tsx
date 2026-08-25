import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import KPICard from "../components/KPICard";
import ChartWrapper from "../components/ChartWrapper";
import DataTable, { Column } from "../components/DataTable";
import { TrendingUp, DollarSign } from "lucide-react";

describe("KPICard Component", () => {
  it("renders title, formatted value, and change indicators", () => {
    render(
      <KPICard
        title="Projected 30D Revenue"
        value="$1,482,900"
        change="+8.4%"
        trend="up"
        icon={DollarSign}
        badgeColor="brand"
      />
    );

    expect(screen.getByText("Projected 30D Revenue")).toBeDefined();
    expect(screen.getByText("$1,482,900")).toBeDefined();
    expect(screen.getByText("+8.4%")).toBeDefined();
  });
});

describe("ChartWrapper Component", () => {
  it("renders title, subtitle, and badge", () => {
    render(
      <ChartWrapper
        title="Enterprise Demand vs Historical Sales"
        subtitle="Actual historical units vs 95% confidence interval forecast band"
        badge="Ensemble AI"
      >
        <div data-testid="chart-content">Chart Canvas</div>
      </ChartWrapper>
    );

    expect(screen.getByText("Enterprise Demand vs Historical Sales")).toBeDefined();
    expect(screen.getByText("Ensemble AI")).toBeDefined();
    expect(screen.getByTestId("chart-content")).toBeDefined();
  });
});

describe("DataTable Component", () => {
  interface SampleRow {
    sku: string;
    units: number;
  }

  const columns: Column<SampleRow>[] = [
    { header: "SKU Code", accessorKey: "sku" },
    { header: "Units Sold", accessorKey: "units" },
  ];

  const data: SampleRow[] = [
    { sku: "SKU-KEYBOARD", units: 120 },
    { sku: "SKU-MONITOR", units: 45 },
  ];

  it("renders table headers and row items accurately", () => {
    render(<DataTable columns={columns} data={data} />);

    expect(screen.getByText("SKU Code")).toBeDefined();
    expect(screen.getByText("Units Sold")).toBeDefined();
    expect(screen.getByText("SKU-KEYBOARD")).toBeDefined();
    expect(screen.getByText("SKU-MONITOR")).toBeDefined();
  });
});
