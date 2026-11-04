import { expect, test } from "@playwright/test";

test("table and detailed card share one exposure per visible offer", async ({ page }, testInfo) => {
  if (testInfo.project.name === "mobile") await page.setViewportSize({ width: 320, height: 851 });
  const offers = [101, 102, 103].map((id) => ({
    id, source: "Fonte de teste", source_id: 1, is_demo: false, transaction_type: "sale",
    price_kind: id === 103 ? "reference" : "asking", price: "100000", area: "80",
    condominium_fee: null, iptu: null, price_per_m2: "1250", last_seen_at: null,
    source_inventory_date: null, previous_price: null, lowest_price: null,
    price_drop_percent: null, price_history: [], days_on_market: 1,
    description: "Oferta sintética para verificar visibilidade. ".repeat(100),
  }));
  const property = { id: 1, city: "Testópolis", state: "BA", neighborhood: "Centro",
    property_type: "apartment", min_price: "100000", listing_count: 3, area: "80",
    bedrooms: 2, parking_spaces: 1, has_demo_offers: false, has_special_sale: false };
  // API boundary only: real React rendering, scrolling and IntersectionObserver.
  await page.route("**/api/properties/**", (route) => route.fulfill({ json:
    new URL(route.request().url()).pathname === "/api/properties/1/"
      ? { ...property, listings: offers, analytics_receipt: "view-receipt" }
      : { count: 1, results: [property], next: null } }));
  const exposures: number[] = [];
  await page.route("**/api/analytics/events/", (route) => {
    const event = route.request().postDataJSON();
    if (event.kind === "exposure") exposures.push(event.listing_id);
    return route.fulfill({ status: 201, json: { accepted: true, context_token: "opening-context",
      redirect_token: `offer-${event.listing_id}` } });
  });
  await page.goto("/");
  await page.getByRole("button", { name: /Ver ofertas/ }).click();
  const dialog = page.getByRole("dialog");
  const table = dialog.getByRole("region", { name: "Tabela: Preços anunciados", exact: true });
  await expect(table.getByText("R$ 100.000", { exact: true }).first()).toBeVisible();
  await expect.poll(() => exposures.length).toBe(testInfo.project.name === "desktop" ? 2 : 1);
  await table.locator("thead th").nth(2).scrollIntoViewIfNeeded();
  await expect.poll(() => [...exposures].sort()).toEqual([101, 102]);
  const card = dialog.locator(".offer-item").first();
  await card.scrollIntoViewIfNeeded();
  await expect(card.getByRole("link", { name: /Ver anúncio original/ })).toHaveAttribute("href", /exposure=offer-101/);
  await table.locator("thead th").nth(1).scrollIntoViewIfNeeded();
  await page.screenshot({ path: testInfo.outputPath("table-exposures.png") });
  expect([...exposures].sort()).toEqual([101, 102]);
});
